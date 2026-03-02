"""FastAPI application factory."""

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from api.routes import router
import monitoring.metrics  # noqa: F401 — register Prometheus metrics


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Minions API", version="0.1.0")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(router)

    # Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app
