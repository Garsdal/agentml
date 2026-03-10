"""Sandbox interface for code execution."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ExecutionResult:
    """Result of code execution in a sandbox."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    artifacts: list[str] = field(default_factory=list)


class Sandbox(ABC):
    """Abstract base class for sandboxed code execution."""

    @abstractmethod
    async def execute(self, code: str, *, language: str = "python") -> ExecutionResult:
        """Execute code in the sandbox.

        Args:
            code: The source code to execute.
            language: The programming language (default: python).

        Returns:
            The execution result.
        """
        ...

    @abstractmethod
    async def install_packages(self, packages: list[str]) -> ExecutionResult:
        """Install packages in the sandbox environment.

        Args:
            packages: List of package names to install.

        Returns:
            The execution result.
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up sandbox resources."""
        ...
