import asyncio
import signal

import grpc
import structlog
import uvicorn
from fastapi import FastAPI
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from prometheus_client import make_asgi_app

from inferhub.v1 import inference_pb2_grpc
from workers.asr_worker.service import ASRWorkerService
from workers.common.provider import GroqProvider
from workers.common.settings import WorkerSettings, get_worker_settings
from workers.llm_worker.service import LLMWorkerService
from workers.tts_worker.service import TTSWorkerService
from workers.vision_worker.service import VisionWorkerService

logger = structlog.get_logger(__name__)


def create_health_app(settings: WorkerSettings, provider: GroqProvider) -> FastAPI:
    app = FastAPI(title=f"InferHub {settings.worker_name}", docs_url=None, redoc_url=None)

    @app.get("/health")
    async def health_check():
        return {
            "status": "ok",
            "worker": settings.worker_name,
            "kind": settings.worker_kind,
            "provider": "groq",
            "provider_configured": provider.configured,
        }

    app.mount("/metrics", make_asgi_app())
    return app


async def create_grpc_server(settings: WorkerSettings, provider: GroqProvider) -> grpc.aio.Server:
    server = grpc.aio.server(options=[("grpc.max_receive_message_length", 32 * 1024 * 1024)])
    _register_worker(server, settings, provider)

    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)

    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    return server


def _register_worker(server: grpc.aio.Server, settings: WorkerSettings, provider: GroqProvider) -> None:
    match settings.worker_kind:
        case "llm":
            inference_pb2_grpc.add_LLMWorkerServicer_to_server(LLMWorkerService(settings, provider), server)
        case "asr":
            inference_pb2_grpc.add_ASRWorkerServicer_to_server(ASRWorkerService(settings, provider), server)
        case "tts":
            inference_pb2_grpc.add_TTSWorkerServicer_to_server(TTSWorkerService(settings, provider), server)
        case "vision":
            inference_pb2_grpc.add_VisionWorkerServicer_to_server(VisionWorkerService(settings, provider), server)
        case _:
            raise ValueError(f"unsupported worker kind: {settings.worker_kind}")


async def main() -> None:
    settings = get_worker_settings()
    provider = GroqProvider(settings)
    grpc_server = await create_grpc_server(settings, provider)
    health_app = create_health_app(settings, provider)
    uvicorn_server = uvicorn.Server(
        uvicorn.Config(
            health_app,
            host=settings.health_host,
            port=settings.health_port,
            log_level="warning",
            access_log=False,
        )
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    await grpc_server.start()
    logger.info(
        "worker_started",
        worker=settings.worker_name,
        kind=settings.worker_kind,
        grpc_port=settings.grpc_port,
        health_port=settings.health_port,
    )
    health_task = asyncio.create_task(uvicorn_server.serve())
    stop_task = asyncio.create_task(stop_event.wait())

    done, _ = await asyncio.wait({health_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
    if stop_task in done:
        await grpc_server.stop(grace=5)
        uvicorn_server.should_exit = True
        await health_task


if __name__ == "__main__":
    asyncio.run(main())
