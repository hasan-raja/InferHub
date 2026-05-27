from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from app.core.config import Settings


def configure_tracing(app: FastAPI, settings: Settings) -> None:
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "inferhub-gateway",
                "deployment.environment": settings.app_env,
            }
        )
    )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)

