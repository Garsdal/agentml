"""Shared test fixtures."""

import tempfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from agentml.api.app import create_app
from agentml.compute.local import LocalCompute
from agentml.config.settings import Settings
from agentml.runtime.lab import LabEnvironment
from agentml.sandbox.local import LocalSandbox
from agentml.storage.local_artifact import LocalArtifactStore
from agentml.storage.local_experiment import LocalExperimentStore
from agentml.storage.local_memory import LocalMemoryStore
from agentml.tracking.file_tracker import FileTracker


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def lab(tmp_dir: Path) -> LabEnvironment:
    """Build a LabEnvironment with temp-directory-based backends."""
    return LabEnvironment(
        compute=LocalCompute(),
        sandbox=LocalSandbox(timeout=10.0),
        experiment_store=LocalExperimentStore(base_dir=tmp_dir / "experiments"),
        artifact_store=LocalArtifactStore(base_dir=tmp_dir / "artifacts"),
        memory_store=LocalMemoryStore(base_dir=tmp_dir / "memory"),
        tracking=FileTracker(base_dir=tmp_dir / "tracking"),
    )


@pytest.fixture
def settings(tmp_dir: Path) -> Settings:
    """Build test settings pointing at the temp directory."""
    settings = Settings()
    settings.storage.base_dir = tmp_dir
    return settings


@pytest.fixture
async def client(settings: Settings):
    """Async HTTP client for the FastAPI app."""
    app = create_app(settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
