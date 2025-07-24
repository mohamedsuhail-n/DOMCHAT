# core/doc_analyzer.py
"""
Document analysis module for the Enhanced Domain Intelligence Analyzer.
Based on Project 2's Groq analyzer but adapted for session management.
"""

import threading
from typing import List, Dict
from groq import Groq
from core.doc_config import DocConfig
import re

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

# ──────────────────────────────────────────────────────────────
#  DOCUMENT GROQ ANALYZER  •  USING OFFICIAL SDK
# ──────────────────────────────────────────────────────────────
class DocumentGroqAnalyzer:
    """
    Thread-safe Groq analyzer specifically for document analysis.
    Maintains chat history and provides RAG-based responses.
    """
    
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = DocConfig.DOC_GROQ_API_KEY
        
        if not api_key:
            logger.error("DOC_GROQ_API_KEY not set in DocConfig.")
            raise ValueError("Set DOC_GROQ_API_KEY in DocConfig.")
        
        self.client = Groq(api_key=api_key)
        self.chat_history: List[Dict] = []
        logger.info(f"Document Analyzer initialized using Groq LLM: {DocConfig.DOC_GROQ_MODEL}")

    def _add_turn(self, user_msg: str, assistant_msg: str):
        """Add a conversation turn to history."""
        self.chat_history += [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg},
        ]
        # Keep last N turns (N*2 messages)
        max_len = DocConfig.DOC_MAX_CHAT_HISTORY * 2
        self.chat_history = self.chat_history[-max_len:]
        logger.debug(f"Added chat turn. History length: {len(self.chat_history)}")

    def generate_dynamic_suggestion(self, answer: str, question: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a strategic assistant that provides 1-sentence actionable suggestions "
                    "based on previous document-based answers. Your goal is to help the user take the next logical step, "
                    "apply the knowledge, or explore further related options. Do not repeat the original answer."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Given the following user question:\n\n{question}\n\n"
                    f"And this answer from a document chatbot:\n\n{answer}\n\n"
                    f"Provide a clear, helpful next-step suggestion:"
                )
            }
        ]

        try:
            resp = self.client.chat.completions.create(
                model=DocConfig.DOC_GROQ_MODEL,
                messages=messages,
                max_completion_tokens=60,
                temperature=0.4,
                stream=False,
            )
            suggestion = resp.choices[0].message.content.strip()
            logger.info("Generated dynamic suggestion for document chat.")
            return suggestion
        except Exception as e:
            logger.error(f"Failed to generate suggestion: {e}")
            return None

    def generate_response_with_context(
        self, query: str, context_chunks: List[Dict]
    ) -> str:
        """
        Generate response using RAG with document context.
        
        Args:
            query: User's question
            context_chunks: Relevant document chunks
            
        Returns:
            AI-generated response with source citations
        """
        # Build RAG context from chunks
        rag_context, sources = "", []
        if context_chunks:
            rag_context = "RELEVANT DOCUMENT CONTENT:\n"
            for i, c in enumerate(context_chunks, 1):
                src = (
                    c["metadata"].get("source_url")
                    or c["metadata"].get("file_name", "Unknown")
                )
                cleaned_text = re.sub(r"(📚|📝)?\s*Sources:\n(?:- .+\n?)+", "", c["text"])
                cleaned_text = re.sub(r"https?://[^\s\)\]]+", "", cleaned_text)
                rag_context += f"\n[Document {i}] Source: {src}\n{cleaned_text[:600]}...\n"
                sources.append(src)

        # Create system + user prompt
        # This is the final, production-ready prompt structure.

        messages = (
            [
                {
                    "role": "system",
                    "content": """
                    **Output Format (MANDATORY)**
                    Your response MUST strictly follow this structure, in this exact order:
                    [Answer]
                    Suggestion: [A single, concise recommendation or next step]
                    Sources:
                    - [source_file_or_url]

                    ---

                    **Your Role & Objective**
                    You are a helpful, insightful document analysis assistant. Your primary objective is to answer the user's questions in a friendly, empathetic, and natural conversational tone, strictly using the provided document context. Your goal is to feel less like an AI and more like a knowledgeable colleague. After your answer, you will provide a summary suggestion or insight to guide the user's next steps.

                    ---

                    **Critical Rules & Behavior**
                    1. Context is King: NEVER use information that is not found in the document context provided in the user's message. If the document doesn't contain the answer, use only what's most relevant or similar. Do not say "the context does not contain..." — just try your best to help.
                    2. Be Empathetic and Clear: Imagine the user is not an expert. Break things down simply, with calm, confident tone. Use real-world analogies if helpful.
                    3. Speak Like a Helpful Colleague: Do NOT use robotic or formal phrases like:
                    - "Based on the document..."
                    - "According to the context..."
                    - "From the document provided..."
                    These phrases are **strictly forbidden**. Start your answer naturally, like you're chatting with a teammate. For example: "You can control the message frequency..." or "One way to avoid over-messaging is..."
                    4. Use Plain Text Only: Do not use markdown formatting. For lists, use simple dashes (-).
                    5. Source Citation: Always end your response with a Sources: section. Do not mention the source file names inside the answer.

                    ---

                    **Examples (Follow the Good, Avoid the Bad)**

                    *Good Examples:*
                    [Answer in warm, human tone]
                    Suggestion: You may want to consider setting frequency caps to avoid overwhelming your audience with repeated messages.
                    Sources:
                    - 01- Master data management.pdf

                    [Answer in warm, human tone]
                    Suggestion: Try using the audience score to segment high-engagement users for better targeting.
                    Sources:
                    - 01- Master data management.pdf

                    *Bad Examples:*
                    ❌ Based on the document content, a frequency cap is...
                    ❌ The context does not contain that information.
                    ❌ Refer to the above document for more information.

                    IMPORTANT: Do a final self-check before responding. If your answer contains phrases like "based on the context" or anything robotic, rewrite the response to sound like a human colleague giving thoughtful advice.

                    """
                }
            ]
            + self.chat_history  # Your existing chat history
            + [
                {
                    "role": "user",
                    "content": f"""
                    DOCUMENT CONTEXT:
                    ---
                    {rag_context}
                    ---

                    QUESTION: {query}
                    """
                }
            ]
        )

        # LLM Completion Call
        try:
            resp = self.client.chat.completions.create(
                model=DocConfig.DOC_GROQ_MODEL,
                messages=messages,
                max_completion_tokens=700,
                temperature=0.3,
                top_p=1.0,
                stream=False,
            )
            assistant = resp.choices[0].message.content.strip().replace('**', '').replace('*', '-').replace('Based on the provided document context, ', '')
            logger.info("Generated response with document context.")
            logger.debug(f"Original LLM response:\n{assistant}\n{'='*50}")
        except Exception as e:
            logger.error(f"Error generating response with context: {e}")
            assistant = "Error: Could not generate response."

        self._add_turn(query, assistant)
        return assistant

    def clear_history(self):
        """Clear chat history."""
        self.chat_history = []
        logger.info("Cleared document chat history.")

    def get_history(self) -> List[Dict]:
        """Get chat history."""
        logger.debug("Retrieved document chat history.")
        return self.chat_history.copy()

# ---------- thread‑safe singleton ----------
_doc_groq_singleton = None
_doc_groq_lock = threading.Lock()


def get_document_analyzer() -> DocumentGroqAnalyzer:
    """
    Thread-safe function to return a singleton document analyzer.
    """
    global _doc_groq_singleton
    with _doc_groq_lock:
        if _doc_groq_singleton is None:
            logger.info("Initializing singleton DocumentGroqAnalyzer.")
            _doc_groq_singleton = DocumentGroqAnalyzer()
        return _doc_groq_singleton