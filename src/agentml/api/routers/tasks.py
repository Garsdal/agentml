"""Tasks router — submit and query tasks."""

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel

from agentml.agents.stub_agent import StubAgent
from agentml.core.task import Task, TaskStatus
from agentml.runtime.lab import LabEnvironment

router = APIRouter(prefix="/tasks", tags=["tasks"])

# In-memory task store for PoC (not persistent across restarts)
_tasks: dict[str, Task] = {}


def _get_lab(request: Request) -> LabEnvironment:
    return request.app.state.lab


class CreateTaskRequest(BaseModel):
    """Request body for creating a task."""

    prompt: str


class ExperimentSummary(BaseModel):
    """Summary of an experiment for API responses."""

    id: str
    state: str
    metrics: dict[str, float] | None = None


class TaskResponse(BaseModel):
    """API response for a task."""

    id: str
    prompt: str
    status: str
    summary: str | None = None
    experiments: list[ExperimentSummary] = []
    metrics: dict[str, float] | None = None


@router.post("", response_model=TaskResponse)
async def create_task(body: CreateTaskRequest, request: Request) -> TaskResponse:
    """Create and run a task."""
    lab = _get_lab(request)

    task = Task(prompt=body.prompt)
    task.status = TaskStatus.RUNNING
    task.updated_at = datetime.now(UTC)

    # Run with stub agent
    agent = StubAgent()
    result = await agent.run(task, lab)

    task.result = result
    task.status = TaskStatus.COMPLETED
    task.updated_at = datetime.now(UTC)

    # Store task
    _tasks[task.id] = task

    # Gather experiment summaries
    experiments = await lab.experiment_store.list(task_id=task.id)
    exp_summaries = [
        ExperimentSummary(
            id=exp.id,
            state=exp.state.value,
            metrics=exp.result.metrics if exp.result else None,
        )
        for exp in experiments
    ]

    task.experiment_ids = [exp.id for exp in experiments]

    return TaskResponse(
        id=task.id,
        prompt=task.prompt,
        status=task.status.value,
        summary=result.summary,
        experiments=exp_summaries,
        metrics=result.metrics,
    )


@router.get("", response_model=list[TaskResponse])
async def list_tasks(request: Request) -> list[TaskResponse]:
    """List all tasks."""
    lab = _get_lab(request)
    responses = []
    for task in _tasks.values():
        experiments = await lab.experiment_store.list(task_id=task.id)
        exp_summaries = [
            ExperimentSummary(
                id=exp.id,
                state=exp.state.value,
                metrics=exp.result.metrics if exp.result else None,
            )
            for exp in experiments
        ]
        responses.append(
            TaskResponse(
                id=task.id,
                prompt=task.prompt,
                status=task.status.value,
                summary=task.result.summary if task.result else None,
                experiments=exp_summaries,
                metrics=task.result.metrics if task.result else None,
            )
        )
    return responses


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, request: Request) -> TaskResponse:
    """Get a specific task by ID."""
    lab = _get_lab(request)

    task = _tasks.get(task_id)
    if task is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Task not found")

    experiments = await lab.experiment_store.list(task_id=task.id)
    exp_summaries = [
        ExperimentSummary(
            id=exp.id,
            state=exp.state.value,
            metrics=exp.result.metrics if exp.result else None,
        )
        for exp in experiments
    ]

    return TaskResponse(
        id=task.id,
        prompt=task.prompt,
        status=task.status.value,
        summary=task.result.summary if task.result else None,
        experiments=exp_summaries,
        metrics=task.result.metrics if task.result else None,
    )
