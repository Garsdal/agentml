"""ID generation utilities."""

from ulid import ULID


def generate_id() -> str:
    """Generate a unique ULID string."""
    return str(ULID())
