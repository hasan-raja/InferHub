import time

import grpc
from inferhub.v1 import inference_pb2, inference_pb2_grpc

from workers.common.metrics import WORKER_LATENCY, WORKER_REQUESTS
from workers.common.provider import GroqProvider
from workers.common.settings import WorkerSettings


class ASRWorkerService(inference_pb2_grpc.ASRWorkerServicer):
    def __init__(self, settings: WorkerSettings, provider: GroqProvider):
        self._settings = settings
        self._provider = provider

    async def Transcribe(self, request, context):
        started = time.perf_counter()
        method = "Transcribe"
        try:
            _validate_transcribe(request)
            response, latency_ms = await self._provider.transcribe(
                model=request.model,
                audio=request.audio,
                filename=request.filename,
                language=request.language,
                prompt=request.prompt,
            )
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "ok").inc()
            return inference_pb2.TranscribeResponse(
                request_id=request.request_id,
                provider="groq",
                model=request.model,
                text=response.get("text") or "",
                language=response.get("language") or request.language,
                duration_seconds=float(response.get("duration") or 0),
                latency_ms=latency_ms,
            )
        except ValueError as exc:
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "invalid").inc()
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except Exception as exc:
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "error").inc()
            await context.abort(grpc.StatusCode.INTERNAL, exc.__class__.__name__)
        finally:
            WORKER_LATENCY.labels(self._settings.worker_name, method).observe(time.perf_counter() - started)


def _validate_transcribe(request) -> None:
    if not request.request_id:
        raise ValueError("request_id is required")
    if not request.model:
        raise ValueError("model is required")
    if not request.audio:
        raise ValueError("audio is required")
