from uuid import uuid4

import grpc
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import Response, StreamingResponse

from app.auth.dependencies import enforce_rate_limit
from app.auth.models import Principal
from app.inference.errors import grpc_error_to_http
from app.inference.schemas import (
    ASRTranscribeResponse,
    LLMChatRequest,
    LLMChatResponse,
    TTSSynthesizeRequest,
    VisionAnalyzeRequest,
    VisionAnalyzeResponse,
)

router = APIRouter(prefix="/v1", tags=["inference"])


@router.post("/llm/chat", response_model=LLMChatResponse | None)
async def chat(
    payload: LLMChatRequest,
    request: Request,
    _principal: Principal = Depends(enforce_rate_limit),
):
    request_id = getattr(request.state, "request_id", str(uuid4()))
    clients = request.app.state.worker_clients
    try:
        if payload.stream:
            async def stream_tokens():
                async for chunk in clients.stream_chat(request_id, payload):
                    if chunk.delta:
                        yield f"data: {chunk.delta}\n\n"
                    if chunk.done:
                        yield "event: done\ndata: {}\n\n"

            return StreamingResponse(stream_tokens(), media_type="text/event-stream")
        return await clients.chat(request_id, payload)
    except grpc.aio.AioRpcError as exc:
        raise grpc_error_to_http(exc) from exc


@router.post("/asr/transcribe", response_model=ASRTranscribeResponse)
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    model: str = Form("whisper-large-v3-turbo"),
    language: str = Form(""),
    prompt: str = Form(""),
    _principal: Principal = Depends(enforce_rate_limit),
) -> ASRTranscribeResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    audio = await file.read()
    try:
        return await request.app.state.worker_clients.transcribe(
            request_id=request_id,
            model=model,
            audio=audio,
            filename=file.filename or "audio.wav",
            language=language,
            prompt=prompt,
        )
    except grpc.aio.AioRpcError as exc:
        raise grpc_error_to_http(exc) from exc


@router.post("/tts/synthesize")
async def synthesize(
    payload: TTSSynthesizeRequest,
    request: Request,
    _principal: Principal = Depends(enforce_rate_limit),
) -> Response:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    try:
        result = await request.app.state.worker_clients.synthesize(request_id, payload)
    except grpc.aio.AioRpcError as exc:
        raise grpc_error_to_http(exc) from exc
    return Response(
        content=result.audio,
        media_type=result.content_type,
        headers={
            "x-request-id": result.request_id,
            "x-provider": result.provider,
            "x-model": result.model,
            "x-latency-ms": str(result.latency_ms),
        },
    )


@router.post("/vision/analyze", response_model=VisionAnalyzeResponse)
async def analyze_vision(
    payload: VisionAnalyzeRequest,
    request: Request,
    _principal: Principal = Depends(enforce_rate_limit),
) -> VisionAnalyzeResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    try:
        return await request.app.state.worker_clients.analyze_vision(request_id, payload)
    except grpc.aio.AioRpcError as exc:
        raise grpc_error_to_http(exc) from exc

