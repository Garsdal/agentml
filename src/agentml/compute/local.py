"""Local compute backend — runs functions directly in-process."""

from collections.abc import Callable
from typing import Any

from agentml.interfaces.compute import ComputeBackend


class LocalCompute(ComputeBackend):
    """Compute backend that executes functions locally."""

    async def run(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a function directly in the current process."""
        return fn(*args, **kwargs)

    async def status(self) -> dict[str, Any]:
        """Return local compute status."""
        return {"backend": "local", "status": "ok"}
