from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.risk import router as risk_router
from app.api.customers import router as customers_router
from app.core.config import settings
from app.db.pool import close_pool


def create_app() -> FastAPI:
    app = FastAPI(title="Predictive Analytics for Loss Prevention", version="0.1.0")

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(risk_router)
    app.include_router(customers_router)

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await close_pool()

    return app


app = create_app()
