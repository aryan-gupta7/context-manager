import asyncio
import logging
from contextvars import ContextVar
from contextlib import contextmanager

import httpx
import ollama

from config import DEVICE_URLS, settings


_runtime_overrides: ContextVar[dict | None] = ContextVar("runtime_llm_overrides", default=None)

PROVIDER_PRESETS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "main_model": "gpt-4o-mini",
        "graph_model": "gpt-4o-mini",
        "kind": "openai_compatible",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "main_model": "deepseek-chat",
        "graph_model": "deepseek-chat",
        "kind": "openai_compatible",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "main_model": "moonshot-v1-8k",
        "graph_model": "moonshot-v1-8k",
        "kind": "openai_compatible",
    },
    "gemini": {
        # Gemini OpenAI-compatible endpoint
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "main_model": "gemini-2.0-flash",
        "graph_model": "gemini-2.0-flash",
        "kind": "openai_compatible",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "main_model": "claude-3-5-sonnet-latest",
        "graph_model": "claude-3-5-haiku-latest",
        "kind": "anthropic",
    },
}


class LLMService:

    @contextmanager
    def runtime_overrides(self, overrides: dict | None):
        token = _runtime_overrides.set(overrides or None)
        try:
            yield
        finally:
            _runtime_overrides.reset(token)

    def _get_override(self, key: str):
        runtime = _runtime_overrides.get() or {}
        return runtime.get(key)

    def _get_ollama_client(self, model_name: str) -> ollama.Client:
        url = DEVICE_URLS.get(model_name, settings.ollama_device_a_url)
        return ollama.Client(host=url)

    def _resolve_provider(self) -> dict:
        provider = (self._get_override("llm_provider") or settings.llm_provider).lower().strip()

        if provider == "ollama":
            return {"kind": "ollama"}

        if provider == "openai_compatible":
            return {
                "kind": "openai_compatible",
                "base_url": self._get_override("llm_base_url") or settings.llm_base_url,
                "main_model": self._get_override("llm_main_model") or settings.llm_main_model,
                "graph_model": self._get_override("llm_graph_model") or settings.llm_graph_model,
            }

        preset = PROVIDER_PRESETS.get(provider)
        if not preset:
            raise RuntimeError(
                f"Unsupported llm_provider '{settings.llm_provider}'. "
                "Use one of: ollama, openai, anthropic, gemini, deepseek, kimi, openai_compatible"
            )

        return {
            "kind": preset["kind"],
            "base_url": self._get_override("llm_base_url") or settings.llm_base_url or preset["base_url"],
            "main_model": self._get_override("llm_main_model") or settings.llm_main_model or preset["main_model"],
            "graph_model": self._get_override("llm_graph_model") or settings.llm_graph_model or preset["graph_model"],
        }

    def _role_model(self, provider_config: dict, role: str) -> str:
        runtime_graph = self._get_override("llm_graph_model")
        runtime_main = self._get_override("llm_main_model")
        model_name = runtime_graph if role == "graph" and runtime_graph else runtime_main if role != "graph" and runtime_main else provider_config["graph_model"] if role == "graph" else provider_config["main_model"]
        if not model_name:
            raise RuntimeError(f"No model configured for role '{role}' and provider '{settings.llm_provider}'")
        return model_name

    async def _call_ollama(self, model_name: str, system_prompt: str, user_content: str) -> str:
        client = self._get_ollama_client(model_name)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat(model=model_name, messages=messages),
        )
        return response["message"]["content"]

    async def _call_openai_compatible(
        self,
        base_url: str,
        model_name: str,
        system_prompt: str,
        user_content: str,
    ) -> str:
        api_key = self._get_override("llm_api_key") or settings.llm_api_key
        base_url = self._get_override("llm_base_url") or base_url
        api_key_header = self._get_override("llm_api_key_header") or settings.llm_api_key_header
        api_key_prefix = self._get_override("llm_api_key_prefix") if self._get_override("llm_api_key_prefix") is not None else settings.llm_api_key_prefix

        if not api_key:
            raise RuntimeError(f"LLM_API_KEY is required when llm_provider={settings.llm_provider}")
        if not base_url:
            raise RuntimeError("LLM_BASE_URL is required for cloud/openai-compatible providers")

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
        }

        auth_value = f"{api_key_prefix}{api_key}" if api_key_prefix else api_key
        headers = {
            api_key_header: auth_value,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"]

    async def _call_anthropic(
        self,
        base_url: str,
        model_name: str,
        system_prompt: str,
        user_content: str,
    ) -> str:
        api_key = self._get_override("llm_api_key") or settings.llm_api_key
        base_url = self._get_override("llm_base_url") or base_url

        if not api_key:
            raise RuntimeError("LLM_API_KEY is required when llm_provider=anthropic")
        if not base_url:
            raise RuntimeError("LLM_BASE_URL is required when llm_provider=anthropic")

        payload = {
            "model": model_name,
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}],
        }

        headers = {
            "x-api-key": api_key,
            "anthropic-version": settings.anthropic_version,
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/messages",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        content = data.get("content", [])
        if content and isinstance(content, list):
            first = content[0]
            if isinstance(first, dict):
                return first.get("text", "")
        return ""

    async def call(self, role: str, system_prompt: str, user_content: str) -> str:
        provider = self._resolve_provider()

        try:
            if provider["kind"] == "ollama":
                model_name = settings.MODEL_GRAPH_BUILDER if role == "graph" else settings.MODEL_MAIN_REASONER
                return await self._call_ollama(model_name, system_prompt, user_content)

            model_name = self._role_model(provider, role)
            if provider["kind"] == "anthropic":
                return await self._call_anthropic(
                    provider["base_url"],
                    model_name,
                    system_prompt,
                    user_content,
                )

            return await self._call_openai_compatible(
                provider["base_url"],
                model_name,
                system_prompt,
                user_content,
            )
        except Exception as e:
            logging.error("LLM call failed for role=%s provider=%s: %s", role, settings.llm_provider, e)
            raise

    async def chat(self, system_prompt: str, user_content: str) -> str:
        return await self.call("main", system_prompt, user_content)

    async def summarize(self, system_prompt: str, user_content: str) -> str:
        return await self.call("main", system_prompt, user_content)

    async def merge(self, system_prompt: str, user_content: str) -> str:
        return await self.call("main", system_prompt, user_content)

    async def extract_graph(self, system_prompt: str, user_content: str) -> str:
        return await self.call("graph", system_prompt, user_content)

    async def exploration_chat(self, system_prompt: str, user_content: str) -> tuple[str, str | None]:
        response = await self.chat(system_prompt, user_content)
        return response, None


llm_service = LLMService()
