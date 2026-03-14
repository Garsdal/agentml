"""Agent backend factory — creates the right backend from config."""

from __future__ import annotations

from dojo.agents.backend import AgentBackend


def create_agent_backend(backend: str = "claude") -> AgentBackend:
    """Create an AgentBackend instance by name.

    Args:
        backend: Backend identifier ("claude", "stub", etc.)

    Returns:
        A configured AgentBackend instance.

    Raises:
        ValueError: If the backend name is unknown.
    """
    if backend == "claude":
        from dojo.agents.backends.claude import ClaudeAgentBackend

        return ClaudeAgentBackend()

    if backend == "stub":
        from dojo.agents.backends.stub import StubAgentBackend

        return StubAgentBackend()

    msg = f"Unknown agent backend: {backend}"
    raise ValueError(msg)
