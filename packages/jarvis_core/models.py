from __future__ import annotations

from dataclasses import dataclass

import httpx

from .config import settings


@dataclass(frozen=True)
class ModelResponse:
    text: str
    model: str


class ModelError(RuntimeError):
    pass


class OpenRouterModel:
    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    async def complete(self, messages: list[dict[str, str]], model: str | None = None) -> ModelResponse:
        if not settings.openrouter_api_key:
            raise ModelError("OPENROUTER_API_KEY is not configured")
        selected = model or settings.model
        payload = {"model": selected, "messages": messages}
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(self.endpoint, json=payload, headers=headers)
        if response.status_code >= 400:
            raise ModelError(f"model provider returned HTTP {response.status_code}")
        data = response.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError("invalid model response") from exc
        return ModelResponse(text=text, model=selected)


class ModelRouter:
    def __init__(self) -> None:
        self.primary = OpenRouterModel()

    async def complete(self, messages: list[dict[str, str]]) -> ModelResponse:
        try:
            return await self.primary.complete(messages, settings.model)
        except Exception:
            if not settings.fallback_model or settings.fallback_model == settings.model:
                raise
            return await self.primary.complete(messages, settings.fallback_model)
