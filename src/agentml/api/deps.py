"""Dependency builder — constructs LabEnvironment from settings."""

from pathlib import Path

from agentml.compute.local import LocalCompute
from agentml.config.settings import Settings
from agentml.runtime.lab import LabEnvironment
from agentml.sandbox.local import LocalSandbox
from agentml.storage.local_artifact import LocalArtifactStore
from agentml.storage.local_experiment import LocalExperimentStore
from agentml.storage.local_memory import LocalMemoryStore
from agentml.tracking.file_tracker import FileTracker


def build_lab(settings: Settings) -> LabEnvironment:
    """Build a LabEnvironment from application settings.

    Args:
        settings: Application settings.

    Returns:
        A fully wired LabEnvironment.
    """
    base = Path(settings.storage.base_dir)

    return LabEnvironment(
        compute=LocalCompute(),
        sandbox=LocalSandbox(timeout=settings.sandbox.timeout),
        experiment_store=LocalExperimentStore(base_dir=base / "experiments"),
        artifact_store=LocalArtifactStore(base_dir=base / "artifacts"),
        memory_store=LocalMemoryStore(base_dir=base / "memory"),
        tracking=FileTracker(base_dir=base / "tracking"),
    )
