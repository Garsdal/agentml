"""Compute backend interface."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class ComputeBackend(ABC):
    """Abstract base class for compute backends."""

    @abstractmethod
    async def run(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a function on the compute backend.

        Args:
            fn: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The result of the function execution.
        """
        ...

    @abstractmethod
    async def status(self) -> dict[str, Any]:
        """Get the status of the compute backend.

        Returns:
            A dictionary with status information.
        """
        ...
