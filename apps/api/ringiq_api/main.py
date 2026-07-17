from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.ringiq_api.db.session import dispose_database
from apps.api.ringiq_api.logging import configure_logging
from apps.api.ringiq_api.routes import demo_calls, health, me


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await dispose_database()


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="RingIQ API",
        description="Core SaaS Backend API. The current implementation exposes a voice pipeline demo endpoint.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(demo_calls.router)
    app.include_router(me.router)
    return app


app = create_app()
