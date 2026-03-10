"""Agent interface — the core AI agent contract."""

from abc import ABC, abstractmethod

from agentml.core.task import Task, TaskResult


class Agent(ABC):
    """Abstract base class for AI agents that execute tasks."""

    @abstractmethod
    async def run(self, task: Task, lab: "LabEnvironment") -> TaskResult:  # noqa: F821
        """Execute a task using the provided lab environment.

        Args:
            task: The task to execute.
            lab: The lab environment providing compute, sandbox, storage, etc.

        Returns:
            The result of the task execution.
        """
        ...
