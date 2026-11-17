import json
import logging
from flask import Blueprint, request, jsonify, Response
from backend.config import settings
from backend.services.storage.metadata_store import db
from backend.services.llm.ollama_client import ollama_service
from backend.services.retrieval.hybrid_retriever import retriever

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
def send_message():
    data = request.get_json() or {}
    conversation_id = data.get("conversation_id")
    message_text = (data.get("message") or "").strip()
    use_rag = data.get("use_rag", True)
    source_ids = data.get("source_ids")  # Optional list of doc/website IDs
    source_type = data.get("source_type")  # Optional "document" or "website"
    model = data.get("model") or settings.default_model

    if not message_text:
        return jsonify({"error": "Message cannot be empty"}), 400

    # If conversation_id not provided, find or create one in the default project
    project_id = data.get("project_id", "default")
    if not conversation_id:
        # Create a new conversation with a title derived from the prompt
        title = message_text[:30] + "..." if len(message_text) > 30 else message_text
        conv = db.create_conversation(project_id, title=title)
        conversation_id = conv["id"]
    else:
        conv = db.get_conversation(conversation_id)
        if conv:
            project_id = conv["project_id"]
        else:
            return jsonify({"error": "Conversation not found"}), 404

    # Save user message
    user_msg = db.add_message(
        conversation_id=conversation_id,
        role="user",
        content=message_text,
        model=model
    )

    # Perform RAG retrieval if enabled
    citations = []
    system_prompt = settings.system_prompt
    final_prompt = message_text

    if use_rag:
        try:
            chunks = retriever.retrieve(
                project_id=project_id,
                query=message_text,
                top_k=settings.top_k,
                source_ids=source_ids,
                source_type=source_type,
                hybrid_alpha=settings.hybrid_alpha
            )
            rag_data = retriever.build_rag_prompt(message_text, chunks)
            system_prompt = rag_data["system_prompt"]
            final_prompt = rag_data["prompt"]
            citations = rag_data["citations"]
        except Exception as e:
            logger.warning(f"RAG retrieval skipped or error: {e}")

    # Build message context for LLM
    # Get previous messages for conversation continuity (last 6 messages)
    history = db.list_messages(conversation_id)
    llm_messages = []
    # Take prior messages (excluding the newly added user message)
    prior_messages = history[:-1][-6:]
    for m in prior_messages:
        llm_messages.append({"role": m["role"], "content": m["content"]})
    
    # Append current message with RAG context
    llm_messages.append({"role": "user", "content": final_prompt})

    # Call Ollama inference
    resp = ollama_service.chat(
        messages=llm_messages,
        model=model,
        system_prompt=system_prompt
    )

    assistant_content = resp.get("content", "")
    
    # Save assistant message
    asst_msg = db.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content,
        citations=citations,
        model=model
    )

    # Auto-update conversation title if it was "New Conversation"
    if conv and conv.get("title") in ("New Conversation", ""):
        new_title = message_text[:35] + ("..." if len(message_text) > 35 else "")
        db.update_conversation_title(conversation_id, new_title)

    return jsonify({
        "conversation_id": conversation_id,
        "user_message": user_msg,
        "message": asst_msg,
        "citations": citations,
        "model": model
    })

@chat_bp.route("/chat/stream", methods=["POST"])
def stream_message():
    data = request.get_json() or {}
    conversation_id = data.get("conversation_id")
    message_text = (data.get("message") or "").strip()
    use_rag = data.get("use_rag", True)
    source_ids = data.get("source_ids")
    source_type = data.get("source_type")
    model = data.get("model") or settings.default_model

    if not message_text:
        return jsonify({"error": "Message cannot be empty"}), 400

    project_id = data.get("project_id", "default")
    if not conversation_id:
        title = message_text[:30] + "..." if len(message_text) > 30 else message_text
        conv = db.create_conversation(project_id, title=title)
        conversation_id = conv["id"]
    else:
        conv = db.get_conversation(conversation_id)
        if conv:
            project_id = conv["project_id"]

    db.add_message(conversation_id=conversation_id, role="user", content=message_text, model=model)

    citations = []
    system_prompt = settings.system_prompt
    final_prompt = message_text

    if use_rag:
        try:
            chunks = retriever.retrieve(
                project_id=project_id,
                query=message_text,
                top_k=settings.top_k,
                source_ids=source_ids,
                source_type=source_type,
                hybrid_alpha=settings.hybrid_alpha
            )
            rag_data = retriever.build_rag_prompt(message_text, chunks)
            system_prompt = rag_data["system_prompt"]
            final_prompt = rag_data["prompt"]
            citations = rag_data["citations"]
        except Exception as e:
            logger.warning(f"RAG retrieval error: {e}")

    history = db.list_messages(conversation_id)
    llm_messages = []
    for m in history[:-1][-6:]:
        llm_messages.append({"role": m["role"], "content": m["content"]})
    llm_messages.append({"role": "user", "content": final_prompt})

    def event_stream():
        # First send initial metadata (citations, conversation_id)
        init_payload = json.dumps({
            "type": "meta",
            "conversation_id": conversation_id,
            "citations": citations,
            "model": model
        })
        yield f"data: {init_payload}\n\n"

        full_content = []
        for chunk_sse in ollama_service.chat_stream(
            messages=llm_messages,
            model=model,
            system_prompt=system_prompt
        ):
            # Parse chunk to collect full content
            try:
                line = chunk_sse.strip()
                if line.startswith("data: "):
                    d = json.loads(line[6:])
                    if "chunk" in d:
                        full_content.append(d["chunk"])
            except Exception:
                pass
            yield chunk_sse

        # Save assistant message to DB
        complete_text = "".join(full_content)
        if complete_text:
            db.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=complete_text,
                citations=citations,
                model=model
            )

    return Response(event_stream(), mimetype="text/event-stream")

@chat_bp.route("/chat/regenerate", methods=["POST"])
def regenerate_message():
    data = request.get_json() or {}
    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return jsonify({"error": "conversation_id required"}), 400

    messages = db.list_messages(conversation_id)
    if not messages:
        return jsonify({"error": "No messages in conversation"}), 400

    # If last message was assistant, delete it and use the preceding user message
    last_msg = messages[-1]
    if last_msg["role"] == "assistant":
        # Delete last message
        conn = db.init_db()  # reuse db
        from backend.services.storage.metadata_store import get_db_connection
        c = get_db_connection()
        c.execute("DELETE FROM messages WHERE id = ?", (last_msg["id"],))
        c.commit()
        c.close()
        messages = messages[:-1]

    if not messages or messages[-1]["role"] != "user":
        return jsonify({"error": "No user message to regenerate from"}), 400

    last_user_message = messages[-1]["content"]
    conv = db.get_conversation(conversation_id)
    project_id = conv["project_id"] if conv else "default"
    model = data.get("model") or settings.default_model

    # Perform RAG
    citations = []
    system_prompt = settings.system_prompt
    final_prompt = last_user_message

    try:
        chunks = retriever.retrieve(project_id=project_id, query=last_user_message)
        rag_data = retriever.build_rag_prompt(last_user_message, chunks)
        system_prompt = rag_data["system_prompt"]
        final_prompt = rag_data["prompt"]
        citations = rag_data["citations"]
    except Exception as e:
        logger.warning(f"RAG error: {e}")

    llm_messages = [{"role": m["role"], "content": m["content"]} for m in messages[:-1][-6:]]
    llm_messages.append({"role": "user", "content": final_prompt})

    resp = ollama_service.chat(messages=llm_messages, model=model, system_prompt=system_prompt)
    assistant_content = resp.get("content", "")

    asst_msg = db.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content,
        citations=citations,
        model=model
    )

    return jsonify({"message": asst_msg, "citations": citations})
