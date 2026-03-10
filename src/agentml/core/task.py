"""Task domain models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from agentml.utils.ids import generate_id


class TaskStatus(str, Enum):
    """Possible statuses for a task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskPlan:
    """Plan generated for a task."""

    steps: list[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class TaskResult:
    """Final result of a task."""

    summary: str = ""
    best_experiment_id: str | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """A task submitted by the user."""

    id: str = field(default_factory=generate_id)
    prompt: str = ""
    status: TaskStatus = TaskStatus.PENDING
    plan: TaskPlan | None = None
    experiment_ids: list[str] = field(default_factory=list)
    result: TaskResult | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
