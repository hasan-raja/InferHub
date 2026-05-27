from uuid import uuid4

import grpc
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.auth.service import validate_api_key
from app.core.config import get_settings
from app.inference.schemas import ChatMessage, LLMChatRequest
from app.inference.websocket_presence import mark_connected, mark_disconnected, refresh

router = APIRouter(tags=["websockets"])


@router.websocket("/ws/llm")
async def llm_websocket(websocket: WebSocket) -> None:
    principal = await _authenticate_websocket(websocket)
    await websocket.accept()
    settings = get_settings()
    redis = websocket.app.state.dependencies.redis
    connection_id = await mark_connected(
        redis,
        modality="llm",
        user_id=str(principal.user_id),
        ttl_seconds=settings.websocket_presence_ttl_seconds,
    )
    try:
        while True:
            payload = await websocket.receive_json()
            await refresh(redis, modality="llm", connection_id=connection_id, ttl_seconds=settings.websocket_presence_ttl_seconds)
            request_id = payload.get("request_id") or str(uuid4())
            chat_request = LLMChatRequest(
                model=payload.get("model") or "llama-3.3-70b-versatile",
                messages=[ChatMessage(**message) for message in payload.get("messages", [])],
                temperature=payload.get("temperature", 0.2),
                max_tokens=payload.get("max_tokens", 1024),
                stream=True,
            )
            try:
                async for chunk in websocket.app.state.worker_clients.stream_chat(request_id, chat_request):
                    await websocket.send_json(
                        {
                            "type": "token",
                            "request_id": chunk.request_id,
                            "delta": chunk.delta,
                            "done": chunk.done,
                            "latency_ms": chunk.latency_ms,
                        }
                    )
                    if chunk.done:
                        break
            except grpc.aio.AioRpcError as exc:
                await websocket.send_json({"type": "error", "code": exc.code().name, "message": exc.details()})
    except WebSocketDisconnect:
        pass
    finally:
        await mark_disconnected(redis, modality="llm", connection_id=connection_id)


@router.websocket("/ws/asr")
async def asr_websocket(websocket: WebSocket) -> None:
    principal = await _authenticate_websocket(websocket)
    await websocket.accept()
    settings = get_settings()
    redis = websocket.app.state.dependencies.redis
    connection_id = await mark_connected(
        redis,
        modality="asr",
        user_id=str(principal.user_id),
        ttl_seconds=settings.websocket_presence_ttl_seconds,
    )
    try:
        while True:
            message = await websocket.receive()
            await refresh(redis, modality="asr", connection_id=connection_id, ttl_seconds=settings.websocket_presence_ttl_seconds)
            if "bytes" not in message:
                await websocket.send_json({"type": "error", "message": "send audio bytes"})
                continue
            request_id = str(uuid4())
            try:
                transcript = await websocket.app.state.worker_clients.transcribe(
                    request_id=request_id,
                    model=websocket.query_params.get("model", "whisper-large-v3-turbo"),
                    audio=message["bytes"],
                    filename="stream.wav",
                    language=websocket.query_params.get("language", ""),
                    prompt="",
                )
                words = transcript.text.split()
                for index in range(1, len(words) + 1):
                    await websocket.send_json(
                        {
                            "type": "partial_transcript",
                            "request_id": request_id,
                            "text": " ".join(words[:index]),
                            "final": index == len(words),
                        }
                    )
                if not words:
                    await websocket.send_json(
                        {
                            "type": "partial_transcript",
                            "request_id": request_id,
                            "text": "",
                            "final": True,
                        }
                    )
            except grpc.aio.AioRpcError as exc:
                await websocket.send_json({"type": "error", "code": exc.code().name, "message": exc.details()})
    except WebSocketDisconnect:
        pass
    finally:
        await mark_disconnected(redis, modality="asr", connection_id=connection_id)


async def _authenticate_websocket(websocket: WebSocket):
    raw_key = websocket.query_params.get("api_key")
    authorization = websocket.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        raw_key = authorization.split(" ", 1)[1]
    if not raw_key:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect
    try:
        return await validate_api_key(websocket.app.state.dependencies.postgres, get_settings(), raw_key)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect

