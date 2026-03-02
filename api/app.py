"""FastAPI application factory."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="Minions API", version="0.1.0")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
