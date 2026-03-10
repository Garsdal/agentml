"""Tool runtime interface for Claude SDK integration."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class ToolRuntime(ABC):
    """Abstract base class for tool registration and execution."""

    @abstractmethod
    def register_tool(self, name: str, fn: Callable[..., Any], *, description: str = "") -> None:
        """Register a tool that can be called by the agent.

        Args:
            name: The tool name.
            fn: The function implementing the tool.
            description: Human-readable description.
        """
        ...

    @abstractmethod
    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools.

        Returns:
            A list of tool descriptors.
        """
        ...

    @abstractmethod
    async def call_tool(self, name: str, **kwargs: Any) -> Any:
        """Call a registered tool by name.

        Args:
            name: The tool name.
            **kwargs: Arguments for the tool.

        Returns:
            The tool's return value.
        """
        ...
