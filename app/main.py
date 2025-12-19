"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.routers import payload


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # Startup: nothing special needed, Alembic handles migrations
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Caching Service",
    description="A microservice that caches transformer function results",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(payload.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for container orchestration."""
    return {"status": "healthy"}

