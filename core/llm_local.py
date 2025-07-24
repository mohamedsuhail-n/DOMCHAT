# ~/core/llm_local.py
"""
Lightweight wrapper around the *shared* Llama model.
Keeps a private chat history per session without re-loading GGUF weights.

Supports two-stage workflow:
1. Generate an initial summary of a crawled domain or URLs.
2. Handle conversational Q&A (chat) with the loaded data.
"""

from typing import List
from config import Config
from core.llm_singleton import get_llm  # singleton loader

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

class LlamaCppAnalyzer:
    """
    Wrapper for the shared Llama model.
    Maintains chat history and provides summary and chat responses.
    """

    def __init__(self):
        # Grab the already-loaded model (or trigger first load).
        self.llm = get_llm()
        self.chat_history: List[dict] = []
        logger.info("Initialized LlamaCppAnalyzer.")

    def add_to_history(self, user_message: str, assistant_message: str):
        """
        Add a user/assistant message pair to chat history.
        Keeps only the last N turns.
        """
        self.chat_history.append({"role": "user", "content": user_message})
        self.chat_history.append({"role": "assistant", "content": assistant_message})
        if len(self.chat_history) > Config.MAX_CHAT_HISTORY * 2:
            self.chat_history = self.chat_history[-(Config.MAX_CHAT_HISTORY * 2):]
        logger.debug(f"Added chat turn. History length: {len(self.chat_history)}")

    def generate_summary(
        self,
        context_chunks: List[dict] | None = None,
        domain_info: dict | None = None,
    ) -> str:
        """
        Generates the first, comprehensive summary report after crawling
        a domain or a set of URLs. Should be called once at the beginning
        of an analysis session.

        Args:
            context_chunks: List of content chunks from crawl
            domain_info: Metadata about the domain

        Returns:
            str: Initial summary report
        """
        context_text = self._build_context_text(context_chunks, domain_info, is_initial_analysis=True)

        system_prompt = """
        Your Role: AI Business Intelligence Analyst
        You are a specialist AI that produces professional, plain-text business intelligence reports. Your purpose is to analyze web content that has just been processed and generate a clear, structured, and insightful summary for a business stakeholder.

        ---
        Project Goal Understanding
        The user's project has just crawled and stored web pages. This is the first output the user will see. Your report must provide a complete and professional overview to prepare them for a detailed Q&A session.

        ---
        Output Format and Rules (MANDATORY)
        1.  **Plain Text Only:** The entire output must be plain text. DO NOT use any markdown characters like `*`, `#`, or `**`.
        2.  **Strict Structure:** You must generate the report in the exact format below, using uppercase headers followed by a line of hyphens (`---`) for a clean, professional look.
        3.  **Use Bullet Points:** For lists under a header, use the bullet character `•` followed by two spaces.

        ---
        **REPORT STRUCTURE**

        SUMMARY
        -----------------
        [A 2-3 sentence high-level summary of the most important findings from the entire dataset. Focus on the primary business purpose and key value proposition.]

        KEY THEMES AND TOPICS
        ----------------------
        [A bulleted list summarizing the main themes, recurring topics, products, or services mentioned across all the provided content.]
        •   [Theme 1]
        •   [Theme 2]
        •   [Theme 3]

        SUGGESTSION
        ----------
        The content from these sources has been successfully loaded and indexed. You can now ask any detailed questions about the information discovered in the chat box below.
        
        CONTENT OVERVIEW
        ----------------
        •   Primary Subject: [Identify the main subject, industry, or focus of the website(s).]
        •   Content Volume: [State the number of pages/URLs that were analyzed.]
        """

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"{context_text.strip()}\n\nPlease generate the initial analysis report based on the provided content."}
        ]

        logger.info("Generating initial summary report with LlamaCppAnalyzer.")
        output = self.llm.create_chat_completion(
            messages=messages,
            temperature=0.6,
            max_tokens=1200,
            stop=["</s>"],
        )
        logger.debug(f"Summary output: {output['choices'][0]['message']['content'][:200]}...")
        return output["choices"][0]["message"]["content"]

    def generate_response(
        self,
        prompt: str,
        context_chunks: List[dict] | None = None,
    ) -> str:
        """
        Handles follow-up, conversational questions from the user after the
        initial analysis has been performed. This is the main "chat" function.

        Args:
            prompt: User's question
            context_chunks: Relevant content chunks

        Returns:
            str: AI-generated response
        """
        context_text = self._build_context_text(context_chunks)

        system_prompt = """
        **Output Format (MANDATORY)**
        Your response MUST strictly follow this structure, in this exact order:
        
        [Answer]
        Suggestion: [A single, concise recommendation, next step, or insight]
        Sources:
        - [Full URL of Source 1 that you used]

        ---
        **Your Role & Objective**
        You are a helpful, insightful Website and Domain Analysis Assistant. Your goal is to answer the user's questions in a friendly and natural conversational tone, feeling less like an AI and more like a knowledgeable colleague. Your answers must be based strictly on the provided website context. After your answer, you will provide a concise suggestion to guide the user's next steps.

        ---
        **Critical Rules & Behavior**
        1.  **Context is King:** NEVER use information that is not found in the `WEBSITE CONTEXT`. If you cannot directly answer, synthesize a helpful response from the most relevant parts of the provided context. Never state that you "cannot find the information."
        2.  **Be Empathetic and Clear:** Assume the user may not be an expert. Explain concepts clearly and patiently.
        3.  **Natural Language Only:** Do not start your answer with robotic phrases like "Based on the document..." or "According to the context...". Engage naturally.
        4.  **No Markdown or Special Characters:** The entire response must be plain text. Do not use markdown like **, *, _, `, or ~. For lists within the answer, use a simple hyphen (`-`).
        5.  **Source Citation:** The `Sources:` line is mandatory at the very end. List the relevant source URLs there. Do NOT mention the sources or URLs anywhere else in your response. Cite sources from the context using brackets `[1]` in the main answer.

        ---
        **Good & Bad Examples**

        *Good Example:*
        Resulticks appears to offer a comprehensive suite of services focused on creating robust omnichannel customer experiences [1]. They leverage AI-powered analytics and a customer data platform (CDP) to help global brands increase customer affinity and drive revenue growth [2].
        Suggestion: You might want to ask about the specific industries they serve to see if their solutions are a good fit for your needs.
        Sources:
        - https://example.com/customers.html
        - https://example.com

        *Bad Example:*
        ❌ Based on the context, Resulticks offers...
        ❌ I cannot find that information in the provided context.
        """

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            *self.chat_history,
            {"role": "user", "content": f"{context_text.strip()}\n\nQUESTION: {prompt}"}
        ]

        logger.info("Generating chat response with LlamaCppAnalyzer.")
        output = self.llm.create_chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            stop=["</s>"],
        )
        # Clean up any markdown that might still slip through
        logger.debug(f"Chat output: {output['choices'][0]['message']['content'][:200]}...")
        return output["choices"][0]["message"]["content"].replace('**', '').replace('*', '').replace('_', '').replace('`', '').replace('~', '')
    def _build_context_text(self, context_chunks, domain_info=None, is_initial_analysis=False) -> str:
        """
        Build context text for prompts from content chunks and domain info.

        Args:
            context_chunks: List of content chunks
            domain_info: Domain metadata
            is_initial_analysis: Whether for initial summary

        Returns:
            str: Context text for prompt
        """
        context_text = ""
        if context_chunks:
            limit = 10 if is_initial_analysis else 5
            context_text += "WEBSITE CONTEXT:\n"
            for i, chunk in enumerate(context_chunks[:limit], 1):
                source_url = chunk.get('metadata', {}).get('url', 'Unknown URL')
                context_text += (
                    f"\nSource [{i}]: {source_url}\n"
                    f"Content: {chunk.get('text', '')[:800]}...\n"
                )
        if domain_info and is_initial_analysis:
            context_text += (
                f"\nDOMAIN INFO:\n"
                f"- Domain Analyzed: {domain_info.get('domain')}\n"
                f"- Pages Crawled: {domain_info.get('total_pages')}\n"
                f"- Analysis Date: {domain_info.get('last_crawl')}\n"
            )
        logger.debug(f"Built context text for prompt. Length: {len(context_text)}")
        return context_text

    def clear_history(self):
        """Clear chat history for this session."""
        self.chat_history = []
        logger.info("Cleared chat history for LlamaCppAnalyzer.")

    def get_history(self):
        """Get chat history for this session."""
        logger.debug("Retrieved chat history for LlamaCppAnalyzer.")
        return self.chat_history