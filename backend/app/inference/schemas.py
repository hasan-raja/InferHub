import base64
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=32_000)


class LLMChatRequest(BaseModel):
    model: str = Field(default="llama-3.3-70b-versatile", min_length=1, max_length=160)
    messages: list[ChatMessage] = Field(min_length=1, max_length=128)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    stream: bool = False


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class LLMChatResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    text: str
    usage: TokenUsage
    latency_ms: int


class ASRTranscribeResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    text: str
    language: str
    duration_seconds: float
    latency_ms: int


class TTSSynthesizeRequest(BaseModel):
    model: str = Field(default="playai-tts", min_length=1, max_length=160)
    text: str = Field(min_length=1, max_length=16_000)
    voice: str = Field(default="Fritz-PlayAI", min_length=1, max_length=80)
    response_format: Literal["wav", "mp3"] = "wav"


class VisionImageInput(BaseModel):
    mime_type: str = Field(default="image/png", max_length=80)
    content_base64: str | None = None
    image_url: str | None = Field(default=None, max_length=4096)

    @field_validator("content_base64")
    @classmethod
    def validate_base64(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            base64.b64decode(value, validate=True)
        except Exception as exc:  # noqa: BLE001 - Pydantic validator should map all decode failures.
            raise ValueError("content_base64 must be valid base64") from exc
        return value


class VisionAnalyzeRequest(BaseModel):
    model: str = Field(default="meta-llama/llama-4-scout-17b-16e-instruct", min_length=1, max_length=160)
    prompt: str = Field(min_length=1, max_length=16_000)
    images: list[VisionImageInput] = Field(min_length=1, max_length=8)

    @field_validator("images")
    @classmethod
    def validate_images(cls, value: list[VisionImageInput]) -> list[VisionImageInput]:
        for image in value:
            if not image.content_base64 and not image.image_url:
                raise ValueError("each image requires content_base64 or image_url")
        return value


class VisionAnalyzeResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    text: str
    usage: TokenUsage
    latency_ms: int

