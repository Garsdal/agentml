"""Experiment store interface."""

from abc import ABC, abstractmethod

from agentml.core.experiment import Experiment


class ExperimentStore(ABC):
    """Abstract base class for experiment persistence."""

    @abstractmethod
    async def save(self, experiment: Experiment) -> str:
        """Save an experiment.

        Args:
            experiment: The experiment to save.

        Returns:
            The experiment ID.
        """
        ...

    @abstractmethod
    async def load(self, experiment_id: str) -> Experiment | None:
        """Load an experiment by ID.

        Args:
            experiment_id: The experiment ID.

        Returns:
            The experiment, or None if not found.
        """
        ...

    @abstractmethod
    async def list(self, *, task_id: str | None = None) -> list[Experiment]:
        """List experiments, optionally filtered by task ID.

        Args:
            task_id: If provided, only return experiments for this task.

        Returns:
            A list of experiments.
        """
        ...

    @abstractmethod
    async def delete(self, experiment_id: str) -> bool:
        """Delete an experiment.

        Args:
            experiment_id: The experiment ID.

        Returns:
            True if deleted, False if not found.
        """
        ...
