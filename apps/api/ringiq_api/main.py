from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.ringiq_api.config import get_app_settings
from apps.api.ringiq_api.db.session import dispose_database
from apps.api.ringiq_api.logging import configure_logging
from apps.api.ringiq_api.routes import campaigns, demo_calls, health, knowledge_base, leads, me, platform, platform_catalog


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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_app_settings().cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(demo_calls.router)
    app.include_router(me.router)
    app.include_router(knowledge_base.router)
    app.include_router(leads.router)
    app.include_router(campaigns.router)
    app.include_router(platform.router)
    app.include_router(platform_catalog.router)
    return app


app = create_app()
