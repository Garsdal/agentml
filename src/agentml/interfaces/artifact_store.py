"""Artifact store interface."""

from abc import ABC, abstractmethod


class ArtifactStore(ABC):
    """Abstract base class for binary artifact storage."""

    @abstractmethod
    async def save(self, artifact_id: str, data: bytes, *, content_type: str = "") -> str:
        """Save a binary artifact.

        Args:
            artifact_id: Unique identifier for the artifact.
            data: The binary data to store.
            content_type: MIME content type of the artifact.

        Returns:
            The artifact path or URL.
        """
        ...

    @abstractmethod
    async def load(self, artifact_id: str) -> bytes | None:
        """Load a binary artifact by ID.

        Args:
            artifact_id: The artifact ID.

        Returns:
            The binary data, or None if not found.
        """
        ...

    @abstractmethod
    async def list(self, *, prefix: str = "") -> list[str]:
        """List artifact IDs, optionally filtered by prefix.

        Args:
            prefix: If provided, only return artifacts with this prefix.

        Returns:
            A list of artifact IDs.
        """
        ...

    @abstractmethod
    async def delete(self, artifact_id: str) -> bool:
        """Delete an artifact.

        Args:
            artifact_id: The artifact ID.

        Returns:
            True if deleted, False if not found.
        """
        ...
