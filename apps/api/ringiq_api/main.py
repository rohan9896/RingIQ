from fastapi import FastAPI

from apps.api.ringiq_api.logging import configure_logging
from apps.api.ringiq_api.routes import demo_calls, health


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="RingIQ API",
        description="Core SaaS Backend API. The current implementation exposes a voice pipeline demo endpoint.",
        version="0.1.0",
    )
    app.include_router(health.router)
    app.include_router(demo_calls.router)
    return app


app = create_app()
