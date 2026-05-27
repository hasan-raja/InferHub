import base64
import time
from collections.abc import AsyncIterator
from typing import Any

from groq import AsyncGroq
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from workers.common.metrics import WORKER_RETRIES
from workers.common.settings import WorkerSettings


class GroqProvider:
    def __init__(self, settings: WorkerSettings):
        self._settings = settings
        self._client = AsyncGroq(
            api_key=settings.groq_api_key or "missing-local-key",
            base_url=settings.groq_base_url,
            timeout=settings.groq_timeout_seconds,
        )

    @property
    def configured(self) -> bool:
        return bool(self._settings.groq_api_key)

    async def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> tuple[dict[str, Any], int]:
        started = time.perf_counter()
        response = await self._retry("Chat", self._client.chat.completions.create)(
            model=model,
            messages=messages,
            temperature=temperature or 0.2,
            max_tokens=max_tokens or None,
        )
        return response.model_dump(), _latency_ms(started)

    async def stream_chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[dict[str, Any]]:
        stream = await self._retry("StreamChat", self._client.chat.completions.create)(
            model=model,
            messages=messages,
            temperature=temperature or 0.2,
            max_tokens=max_tokens or None,
            stream=True,
        )
        async for chunk in stream:
            yield chunk.model_dump()

    async def transcribe(
        self,
        *,
        model: str,
        audio: bytes,
        filename: str,
        language: str,
        prompt: str,
    ) -> tuple[dict[str, Any], int]:
        started = time.perf_counter()
        response = await self._retry("Transcribe", self._client.audio.transcriptions.create)(
            model=model,
            file=(filename or "audio.wav", audio),
            language=language or None,
            prompt=prompt or None,
        )
        return response.model_dump(), _latency_ms(started)

    async def synthesize(
        self,
        *,
        model: str,
        text: str,
        voice: str,
        response_format: str,
    ) -> tuple[bytes, str, int]:
        started = time.perf_counter()
        response = await self._retry("Synthesize", self._client.audio.speech.create)(
            model=model,
            input=text,
            voice=voice or "Fritz-PlayAI",
            response_format=response_format or "wav",
        )
        body = await response.aread()
        content_type = response.headers.get("content-type", "audio/wav")
        return body, content_type, _latency_ms(started)

    async def analyze_vision(
        self,
        *,
        model: str,
        prompt: str,
        images: list[dict[str, str]],
    ) -> tuple[dict[str, Any], int]:
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for image in images:
            url = image.get("image_url")
            if not url:
                encoded = base64.b64encode(image["content"]).decode("ascii")
                url = f"data:{image['mime_type']};base64,{encoded}"
            content.append({"type": "image_url", "image_url": {"url": url}})

        started = time.perf_counter()
        response = await self._retry("Analyze", self._client.chat.completions.create)(
            model=model,
            messages=[{"role": "user", "content": content}],
        )
        return response.model_dump(), _latency_ms(started)

    def _retry(self, method: str, func):
        async def wrapped(**kwargs):
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self._settings.groq_max_retries + 1),
                wait=wait_exponential(multiplier=0.1, min=0.1, max=1.0),
                retry=retry_if_exception_type(Exception),
                reraise=True,
            ):
                with attempt:
                    if attempt.retry_state.attempt_number > 1:
                        WORKER_RETRIES.labels(self._settings.worker_name, method).inc()
                    return await func(**kwargs)

        return wrapped


def _latency_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def extract_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return message.get("content") or ""


def extract_delta(chunk: dict[str, Any]) -> str:
    choices = chunk.get("choices") or []
    if not choices:
        return ""
    delta = choices[0].get("delta") or {}
    return delta.get("content") or ""


def extract_usage(response: dict[str, Any]) -> tuple[int, int, int]:
    usage = response.get("usage") or {}
    input_tokens = usage.get("prompt_tokens") or 0
    output_tokens = usage.get("completion_tokens") or 0
    total_tokens = usage.get("total_tokens") or input_tokens + output_tokens
    return input_tokens, output_tokens, total_tokens

