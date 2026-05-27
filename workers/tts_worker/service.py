import time

import grpc
from inferhub.v1 import inference_pb2, inference_pb2_grpc

from workers.common.metrics import WORKER_LATENCY, WORKER_REQUESTS
from workers.common.provider import GroqProvider
from workers.common.settings import WorkerSettings


class TTSWorkerService(inference_pb2_grpc.TTSWorkerServicer):
    def __init__(self, settings: WorkerSettings, provider: GroqProvider):
        self._settings = settings
        self._provider = provider

    async def Synthesize(self, request, context):
        started = time.perf_counter()
        method = "Synthesize"
        try:
            _validate_synthesize(request)
            audio, content_type, latency_ms = await self._provider.synthesize(
                model=request.model,
                text=request.text,
                voice=request.voice,
                response_format=request.response_format,
            )
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "ok").inc()
            return inference_pb2.SynthesizeResponse(
                request_id=request.request_id,
                provider="groq",
                model=request.model,
                audio=audio,
                content_type=content_type,
                latency_ms=latency_ms,
            )
        except ValueError as exc:
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "invalid").inc()
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except Exception as exc:
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "error").inc()
            await context.abort(grpc.StatusCode.INTERNAL, _error_detail(exc))
        finally:
            WORKER_LATENCY.labels(self._settings.worker_name, method).observe(time.perf_counter() - started)


def _validate_synthesize(request) -> None:
    if not request.request_id:
        raise ValueError("request_id is required")
    if not request.model:
        raise ValueError("model is required")
    if not request.text:
        raise ValueError("text is required")


def _error_detail(exc: Exception) -> str:
    detail = str(exc).strip()
    return f"{exc.__class__.__name__}: {detail}" if detail else exc.__class__.__name__
