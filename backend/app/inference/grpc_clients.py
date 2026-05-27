import base64
from dataclasses import dataclass

import grpc
from inferhub.v1 import inference_pb2, inference_pb2_grpc

from app.core.config import Settings
from app.inference.schemas import (
    ASRTranscribeResponse,
    LLMChatRequest,
    LLMChatResponse,
    TTSSynthesizeRequest,
    TokenUsage,
    VisionAnalyzeRequest,
    VisionAnalyzeResponse,
)


@dataclass(slots=True)
class TTSResult:
    request_id: str
    provider: str
    model: str
    audio: bytes
    content_type: str
    latency_ms: int


class WorkerClientManager:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._llm_channel = grpc.aio.insecure_channel(settings.llm_worker_target)
        self._asr_channel = grpc.aio.insecure_channel(settings.asr_worker_target)
        self._tts_channel = grpc.aio.insecure_channel(settings.tts_worker_target)
        self._vision_channel = grpc.aio.insecure_channel(settings.vision_worker_target)
        self.llm = inference_pb2_grpc.LLMWorkerStub(self._llm_channel)
        self.asr = inference_pb2_grpc.ASRWorkerStub(self._asr_channel)
        self.tts = inference_pb2_grpc.TTSWorkerStub(self._tts_channel)
        self.vision = inference_pb2_grpc.VisionWorkerStub(self._vision_channel)

    async def close(self) -> None:
        await self._llm_channel.close()
        await self._asr_channel.close()
        await self._tts_channel.close()
        await self._vision_channel.close()

    async def chat(self, request_id: str, payload: LLMChatRequest) -> LLMChatResponse:
        response = await self.llm.Chat(
            _chat_request(request_id, payload),
            timeout=self._settings.grpc_timeout_seconds,
        )
        return LLMChatResponse(
            request_id=response.request_id,
            provider=response.provider,
            model=response.model,
            text=response.text,
            usage=TokenUsage(
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.total_tokens,
            ),
            latency_ms=response.latency_ms,
        )

    def stream_chat(self, request_id: str, payload: LLMChatRequest):
        return self.llm.StreamChat(
            _chat_request(request_id, payload),
            timeout=self._settings.grpc_timeout_seconds,
        )

    async def transcribe(
        self,
        *,
        request_id: str,
        model: str,
        audio: bytes,
        filename: str,
        language: str,
        prompt: str,
    ) -> ASRTranscribeResponse:
        response = await self.asr.Transcribe(
            inference_pb2.TranscribeRequest(
                request_id=request_id,
                model=model,
                audio=audio,
                filename=filename,
                language=language,
                prompt=prompt,
            ),
            timeout=self._settings.grpc_timeout_seconds,
        )
        return ASRTranscribeResponse(
            request_id=response.request_id,
            provider=response.provider,
            model=response.model,
            text=response.text,
            language=response.language,
            duration_seconds=response.duration_seconds,
            latency_ms=response.latency_ms,
        )

    async def synthesize(self, request_id: str, payload: TTSSynthesizeRequest) -> TTSResult:
        response = await self.tts.Synthesize(
            inference_pb2.SynthesizeRequest(
                request_id=request_id,
                model=payload.model,
                text=payload.text,
                voice=payload.voice,
                response_format=payload.response_format,
            ),
            timeout=self._settings.grpc_timeout_seconds,
        )
        return TTSResult(
            request_id=response.request_id,
            provider=response.provider,
            model=response.model,
            audio=response.audio,
            content_type=response.content_type,
            latency_ms=response.latency_ms,
        )

    async def analyze_vision(self, request_id: str, payload: VisionAnalyzeRequest) -> VisionAnalyzeResponse:
        response = await self.vision.Analyze(
            inference_pb2.VisionAnalyzeRequest(
                request_id=request_id,
                model=payload.model,
                prompt=payload.prompt,
                images=[
                    inference_pb2.VisionImage(
                        mime_type=image.mime_type,
                        content=base64.b64decode(image.content_base64) if image.content_base64 else b"",
                        image_url=image.image_url or "",
                    )
                    for image in payload.images
                ],
            ),
            timeout=self._settings.grpc_timeout_seconds,
        )
        return VisionAnalyzeResponse(
            request_id=response.request_id,
            provider=response.provider,
            model=response.model,
            text=response.text,
            usage=TokenUsage(
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.total_tokens,
            ),
            latency_ms=response.latency_ms,
        )


def _chat_request(request_id: str, payload: LLMChatRequest):
    return inference_pb2.ChatRequest(
        request_id=request_id,
        model=payload.model,
        messages=[
            inference_pb2.ChatMessage(role=message.role, content=message.content)
            for message in payload.messages
        ],
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
    )

