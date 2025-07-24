# ~/core/llm_singleton.py
"""
Load either the local GGUF model using llama-cpp (Mistral)
or Groq's hosted models via OpenAI-compatible API.

This singleton makes sure only one model is loaded per runtime.
"""

import os
import time
from threading import Lock
from typing import Any
import requests
from config import Config

# Add logger
from core.logger_config import setup_logger
logger = setup_logger(__name__)

__all__ = ["get_llm"]

_llm = None
_lock = Lock()

class GroqChatLLM:
    """
    Thin wrapper that mimics llama_cpp.Llama.create_chat_completion()
    but calls Groq’s OpenAI‑compatible endpoint.

    Includes automatic message sanitization so Groq never
    receives invalid roles or empty content.
    """
    VALID_ROLES = {"system", "user", "assistant"}

    def __init__(self):
        self.api_key  = Config.GROQ_API_KEY
        self.base_url = Config.GROQ_BASE_URL.rstrip("/")
        self.model    = Config.GROQ_MODEL_NAME
        logger.info(f"Using Groq LLM: {self.model}")

    def _clean_messages(self, raw: list[dict]) -> list[dict]:
        """
        Ensure every message has a valid role and non‑empty string content.
        Invalid entries are fixed or dropped.
        """
        cleaned = []
        for m in raw:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role", "user")).lower()
            if role not in self.VALID_ROLES:
                role = "user"
            content = str(m.get("content", "")).strip()
            if not content:
                continue           # drop empty messages
            cleaned.append({"role": role, "content": content})
        # If the list is now empty Groq will error; add a placeholder:
        if not cleaned:
            cleaned.append({"role": "user", "content": "..."})
        logger.debug(f"Cleaned messages for Groq: {cleaned}")
        return cleaned

    def create_chat_completion(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs,
    ) -> dict:
        """
        Send a chat completion request to Groq's API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens for response
            temperature: Sampling temperature
            **kwargs: Additional OpenAI-compatible parameters

        Returns:
            dict: Groq API response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model":    self.model,
            "messages": self._clean_messages(messages),   # sanitise here
            "max_tokens":  max_tokens,
            "temperature": temperature,
        }

        for k in ("stop", "top_p", "presence_penalty", "frequency_penalty"):
            if k in kwargs and kwargs[k] is not None:
                payload[k] = kwargs[k]

        # Debug print – comment out after you verify
        import json
        logger.debug(f"Payload to Groq: {json.dumps(payload, indent=2)}")

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            logger.info("Groq API chat completion successful.")
            return resp.json()
        except Exception as e:
            logger.error(f"Groq API chat completion failed: {e}")
            raise

def get_llm() -> Any:
    """
    Thread-safe function to return a singleton LLM.
    Loads either a local GGUF model or uses the Groq API.

    Returns:
        LLM instance (GroqChatLLM or llama_cpp.Llama)
    """
    global _llm
    if _llm is not None:
        logger.debug("Returning cached LLM instance.")
        return _llm

    with _lock:
        if _llm is not None:
            logger.debug("Returning cached LLM instance (locked).")
            return _llm

        if Config.LLM_PROVIDER == "groq":
            logger.info("Initializing Groq LLM API client...")
            _llm = GroqChatLLM()

        elif Config.LLM_PROVIDER == "local":
            logger.info("Loading Mistral‑7B‑Q3_K_M locally...")
            from llama_cpp import Llama

            start = time.time()
            _llm = Llama(
                model_path=Config.LLAMA_MODEL_PATH,
                n_ctx=2048,
                n_threads=2,
                n_gpu_layers=0,
                verbose=False,
            )
            elapsed = time.time() - start
            logger.info(f"LLM ready (loaded in {elapsed:.2f} seconds)")

        else:
            logger.error(f"Unsupported LLM_PROVIDER: {Config.LLM_PROVIDER}")
            raise ValueError(f"Unsupported LLM_PROVIDER: {Config.LLM_PROVIDER}")

        return _llm

