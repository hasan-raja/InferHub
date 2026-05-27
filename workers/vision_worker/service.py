import time

import grpc
from inferhub.v1 import inference_pb2, inference_pb2_grpc

from workers.common.metrics import WORKER_LATENCY, WORKER_REQUESTS
from workers.common.provider import GroqProvider, extract_text, extract_usage
from workers.common.settings import WorkerSettings


class VisionWorkerService(inference_pb2_grpc.VisionWorkerServicer):
    def __init__(self, settings: WorkerSettings, provider: GroqProvider):
        self._settings = settings
        self._provider = provider

    async def Analyze(self, request, context):
        started = time.perf_counter()
        method = "Analyze"
        try:
            _validate_analyze(request)
            response, latency_ms = await self._provider.analyze_vision(
                model=request.model,
                prompt=request.prompt,
                images=[
                    {
                        "mime_type": image.mime_type or "image/png",
                        "content": image.content,
                        "image_url": image.image_url,
                    }
                    for image in request.images
                ],
            )
            input_tokens, output_tokens, total_tokens = extract_usage(response)
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "ok").inc()
            return inference_pb2.VisionAnalyzeResponse(
                request_id=request.request_id,
                provider="groq",
                model=response.get("model") or request.model,
                text=extract_text(response),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
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


def _validate_analyze(request) -> None:
    if not request.request_id:
        raise ValueError("request_id is required")
    if not request.model:
        raise ValueError("model is required")
    if not request.prompt:
        raise ValueError("prompt is required")
    if not request.images:
        raise ValueError("at least one image is required")
