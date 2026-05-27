import time

import grpc
from inferhub.v1 import inference_pb2, inference_pb2_grpc

from workers.common.metrics import WORKER_LATENCY, WORKER_REQUESTS
from workers.common.provider import GroqProvider, extract_delta, extract_text, extract_usage
from workers.common.settings import WorkerSettings


class LLMWorkerService(inference_pb2_grpc.LLMWorkerServicer):
    def __init__(self, settings: WorkerSettings, provider: GroqProvider):
        self._settings = settings
        self._provider = provider

    async def Chat(self, request, context):
        started = time.perf_counter()
        method = "Chat"
        try:
            _validate_chat(request, context)
            response, latency_ms = await self._provider.chat(
                model=request.model,
                messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            input_tokens, output_tokens, total_tokens = extract_usage(response)
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "ok").inc()
            return inference_pb2.ChatResponse(
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
            await context.abort(grpc.StatusCode.INTERNAL, _error_detail(exc))
        finally:
            WORKER_LATENCY.labels(self._settings.worker_name, method).observe(time.perf_counter() - started)

    async def StreamChat(self, request, context):
        started = time.perf_counter()
        method = "StreamChat"
        try:
            _validate_chat(request, context)
            async for chunk in self._provider.stream_chat(
                model=request.model,
                messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                yield inference_pb2.ChatStreamChunk(
                    request_id=request.request_id,
                    provider="groq",
                    model=chunk.get("model") or request.model,
                    delta=extract_delta(chunk),
                    done=False,
                    latency_ms=round((time.perf_counter() - started) * 1000),
                )
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "ok").inc()
            yield inference_pb2.ChatStreamChunk(
                request_id=request.request_id,
                provider="groq",
                model=request.model,
                done=True,
                latency_ms=round((time.perf_counter() - started) * 1000),
            )
        except ValueError as exc:
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "invalid").inc()
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except Exception as exc:
            WORKER_REQUESTS.labels(self._settings.worker_name, method, "error").inc()
            await context.abort(grpc.StatusCode.INTERNAL, _error_detail(exc))
        finally:
            WORKER_LATENCY.labels(self._settings.worker_name, method).observe(time.perf_counter() - started)


def _validate_chat(request, context) -> None:
    if not request.request_id:
        raise ValueError("request_id is required")
    if not request.model:
        raise ValueError("model is required")
    if not request.messages:
        raise ValueError("messages are required")


def _error_detail(exc: Exception) -> str:
    detail = str(exc).strip()
    return f"{exc.__class__.__name__}: {detail}" if detail else exc.__class__.__name__
