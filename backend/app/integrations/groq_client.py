from dataclasses import dataclass
from typing import Any

from groq import AsyncGroq

from app.core.config import Settings


@dataclass(slots=True)
class GroqClient:
    settings: Settings

    def __post_init__(self) -> None:
        self._client = AsyncGroq(
            api_key=self.settings.groq_api_key or "missing-local-key",
            base_url=self.settings.groq_base_url,
            timeout=self.settings.groq_timeout_seconds,
        )

    async def chat(self, *, model: str, messages: list[dict[str, str]]) -> dict[str, Any]:
        response = await self._client.chat.completions.create(model=model, messages=messages)
        return response.model_dump()

    async def stream_chat(self, *, model: str, messages: list[dict[str, str]]):
        stream = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            yield chunk.model_dump()

    async def transcribe(self, *, model: str, audio_file: Any) -> dict[str, Any]:
        response = await self._client.audio.transcriptions.create(model=model, file=audio_file)
        return response.model_dump()

    async def synthesize(self, *, model: str, text: str, voice: str) -> bytes:
        response = await self._client.audio.speech.create(model=model, input=text, voice=voice)
        return await response.aread()

    async def vision_chat(self, *, model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
        response = await self._client.chat.completions.create(model=model, messages=messages)
        return response.model_dump()

