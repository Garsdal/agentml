"""JSON serialization utilities for dataclasses and datetime."""

import dataclasses
import json
from datetime import datetime
from typing import Any


class AgentMLEncoder(json.JSONEncoder):
    """Custom JSON encoder supporting dataclasses and datetime objects."""

    def default(self, o: Any) -> Any:
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def to_json(obj: Any, *, indent: int | None = 2) -> str:
    """Serialize an object to a JSON string."""
    return json.dumps(obj, cls=AgentMLEncoder, indent=indent)


def from_json(data: str) -> Any:
    """Deserialize a JSON string."""
    return json.loads(data)
