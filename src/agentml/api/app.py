"""FastAPI application factory."""

from fastapi import FastAPI

from agentml._version import __version__
from agentml.api.deps import build_lab
from agentml.api.routers import experiments, health, knowledge, tasks
from agentml.config.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Application settings. Loads defaults if not provided.

    Returns:
        Configured FastAPI application.
    """
    if settings is None:
        settings = Settings.load()

    app = FastAPI(
        title="AgentML",
        description="AI-powered experiment orchestration",
        version=__version__,
    )

    # Wire up the lab environment
    app.state.lab = build_lab(settings)
    app.state.settings = settings

    # Register routers
    app.include_router(health.router)
    app.include_router(tasks.router)
    app.include_router(experiments.router)
    app.include_router(knowledge.router)

    return app
