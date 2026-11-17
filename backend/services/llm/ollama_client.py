import json
import logging
import requests
from typing import List, Dict, Any, Generator, Optional
from backend.config import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip('/')

    def check_health(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                models_data = resp.json().get("models", [])
                models = [m.get("name") for m in models_data]
                return {
                    "connected": True,
                    "models": models,
                    "default_model": settings.default_model,
                    "has_default_model": settings.default_model in models or any(settings.default_model in m for m in models)
                }
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
        return {
            "connected": False,
            "models": [],
            "default_model": settings.default_model,
            "has_default_model": False,
            "error": "Ollama service unreachable on " + self.base_url
        }

    def list_models(self) -> List[Dict[str, Any]]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                return resp.json().get("models", [])
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
        return []

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        target_model = model or settings.default_model
        temp = temperature if temperature is not None else settings.temperature
        tokens = max_tokens if max_tokens is not None else settings.max_tokens

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload = {
            "model": target_model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": tokens
            }
        }

        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=90)
            if resp.status_code == 200:
                data = resp.json()
                msg = data.get("message", {})
                return {
                    "role": "assistant",
                    "content": msg.get("content", ""),
                    "model": target_model,
                    "done": True,
                    "total_duration": data.get("total_duration", 0),
                    "eval_count": data.get("eval_count", 0)
                }
            else:
                return {
                    "role": "assistant",
                    "content": f"Ollama error: HTTP {resp.status_code} - {resp.text}",
                    "model": target_model,
                    "error": True
                }
        except requests.exceptions.Timeout:
            return {
                "role": "assistant",
                "content": "Request timed out while waiting for local model inference.",
                "model": target_model,
                "error": True
            }
        except Exception as e:
            return {
                "role": "assistant",
                "content": f"Failed to connect to Ollama inference: {str(e)}",
                "model": target_model,
                "error": True
            }

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:
        target_model = model or settings.default_model
        temp = temperature if temperature is not None else settings.temperature
        tokens = max_tokens if max_tokens is not None else settings.max_tokens

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload = {
            "model": target_model,
            "messages": formatted_messages,
            "stream": True,
            "options": {
                "temperature": temp,
                "num_predict": tokens
            }
        }

        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, stream=True, timeout=120)
            if resp.status_code != 200:
                err_data = json.dumps({"error": f"Ollama error: {resp.status_code}"})
                yield f"data: {err_data}\n\n"
                return

            for line in resp.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    try:
                        chunk_json = json.loads(decoded)
                        content = chunk_json.get("message", {}).get("content", "")
                        done = chunk_json.get("done", False)
                        out = json.dumps({"chunk": content, "done": done})
                        yield f"data: {out}\n\n"
                        if done:
                            break
                    except Exception:
                        continue
        except Exception as e:
            err_data = json.dumps({"error": str(e), "done": True})
            yield f"data: {err_data}\n\n"

ollama_service = OllamaClient()
