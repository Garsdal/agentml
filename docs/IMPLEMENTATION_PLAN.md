# Dojo.ml — Implementation Plan

**Goal:** Scaffold the full project, implement all interfaces, wire local backends, and get `dojo start` running with a passing end-to-end test.

**Stack:** Python 3.13, uv, FastAPI, Typer, Pydantic Settings, structlog, hatchling  
**Architecture:** Hexagonal (ports & adapters) from STRUCTURE.md + FastAPI/CLI structure from PRD.md  
**Agent strategy:** Claude Agent SDK via `ToolRuntime` interface — agent logic lives in the SDK, not in our code

---

## Phase 0 — Project Setup

1. `uv init` with src layout, Python 3.13
2. `pyproject.toml` — hatchling build, all deps, `[project.scripts] dojo = "dojo.cli.main:app"`
3. `Makefile` — `dev`, `test`, `lint`, `run`
4. `.python-version` → `3.13`
5. `ruff.toml`

## Phase 1 — Core Domain Models

Pure dataclasses, zero infrastructure imports.

```
src/dojo/core/
├── __init__.py
├── experiment.py      # Experiment, Hypothesis, ExperimentResult
├── task.py            # Task, TaskStatus, TaskPlan, TaskResult
├── knowledge.py       # KnowledgeAtom
└── state_machine.py   # ExperimentState enum + VALID_TRANSITIONS + transition()
```

**Key models:**

- `Experiment(id, task_id, hypothesis, config, state, result)`
- `Task(id, prompt, status, experiment_ids, result, created_at)`
- `KnowledgeAtom(id, context, claim, action, confidence, evidence_ids)`
- `ExperimentState`: `RUNNING → COMPLETED | FAILED → ARCHIVED`

## Phase 2 — Interfaces (Ports)

ABCs defining every swappable contract. This is the critical layer.

```
src/dojo/interfaces/
├── __init__.py
├── agent.py             # Agent ABC: async run(task, lab) -> TaskResult
├── compute.py           # ComputeBackend ABC: run(fn, *args) -> Any
├── sandbox.py           # Sandbox ABC: execute(code) -> ExecutionResult
├── experiment_store.py  # save/load/list experiments
├── artifact_store.py    # save/load binary artifacts
├── memory_store.py      # add/search knowledge atoms
├── tool_runtime.py      # register_tool / start — Claude SDK integration point
└── tracking.py          # TrackingConnector: log_metrics/log_params/log_artifact
```

Each file: one ABC, 3-6 abstract methods, typed signatures, docstrings.

## Phase 3 — Local Implementations (Adapters)

One concrete class per interface. JSON files + subprocess + in-memory.

```
src/dojo/
├── compute/
│   └── local.py           # LocalCompute — fn(*args) directly
├── sandbox/
│   └── local.py           # LocalSandbox — subprocess + tempdir
├── storage/
│   ├── local_experiment.py  # JSON file per experiment
│   ├── local_artifact.py    # filesystem bytes
│   └── local_memory.py      # atoms.json keyword search
├── tracking/
│   └── file_tracker.py      # JSON-based metric logging
└── agents/
    └── stub_agent.py         # StubAgent — returns mock result (PoC)
```

`StubAgent` implements `Agent` and runs a hardcoded loop: create experiment → mark completed → return result. This lets us test the full pipeline without an LLM key. Replaced by Claude Agent SDK agent in production.

## Phase 4 — Runtime (Orchestration)

The wiring layer. LabEnvironment is the DI container; ExperimentService drives the lifecycle.

```
src/dojo/runtime/
├── __init__.py
├── lab.py                  # LabEnvironment — holds all injected backends
└── experiment_service.py   # create/run/record experiments using LabEnvironment
```

```python
class LabEnvironment:
    def __init__(self, compute, sandbox, experiment_store,
                 artifact_store, memory_store, tracking): ...
```

```python
class ExperimentService:
    def __init__(self, lab: LabEnvironment): ...
    async def create(self, experiment) -> str: ...
    async def run(self, experiment_id) -> Experiment: ...
```

## Phase 5 — Configuration

```
src/dojo/config/
├── __init__.py
├── settings.py    # Pydantic Settings: loads .dojo/config.yaml + env vars
└── defaults.py    # Default values
```

Nested settings: `LLMSettings`, `SandboxSettings`, `StorageSettings`, `TrackingSettings`, `APISettings`.  
Env prefix: `DOJO_`, nested delimiter: `__`.  
YAML file: `.dojo/config.yaml`.

## Phase 6 — FastAPI API

```
src/dojo/api/
├── __init__.py
├── app.py          # create_app(settings) -> FastAPI, wires LabEnvironment
├── deps.py         # build_lab(settings) -> LabEnvironment
└── routers/
    ├── __init__.py
    ├── health.py       # GET /health
    ├── tasks.py        # POST /tasks, GET /tasks, GET /tasks/{id}
    ├── experiments.py  # GET /experiments, GET /experiments/{id}
    └── knowledge.py    # GET /knowledge, GET /knowledge/relevant
```

`create_app()`:
1. Build `LabEnvironment` from settings
2. Attach to `app.state`
3. Register routers
4. Return app

**PoC endpoints (must work):**
- `GET /health` → `{"status": "ok"}`
- `POST /tasks` → creates task, runs stub agent, returns result
- `GET /tasks/{id}` → returns task with experiments

## Phase 7 — CLI

```
src/dojo/cli/
├── __init__.py
├── main.py       # Typer app, register subcommands
├── start.py      # `dojo start` — launches uvicorn
├── run.py        # `dojo run "<prompt>"` — POST /tasks then poll
└── config.py     # `dojo config init/show`
```

`dojo start`:
1. Load settings
2. Build FastAPI app
3. Run uvicorn programmatically (single process, no subprocess management for PoC)
4. Print status banner

## Phase 8 — Utils

```
src/dojo/utils/
├── __init__.py
├── logging.py         # structlog setup
├── ids.py             # generate_id() → ULID string
└── serialization.py   # JSON encoder for dataclasses/datetime
```

## Phase 9 — End-to-End Test

```
tests/
├── conftest.py                    # Shared fixtures: lab, app client
├── unit/
│   ├── test_state_machine.py      # transition validation
│   ├── test_experiment_service.py # create + run via local backends
│   └── test_local_storage.py      # JSON round-trip
└── e2e/
    └── test_full_lifecycle.py     # The money test
```

**`test_full_lifecycle.py`:**

```python
async def test_submit_task_and_get_results(client):
    """POST /tasks with a prompt → GET /tasks/{id} → verify experiments + result."""
    # 1. POST /tasks {"prompt": "test task"}
    resp = await client.post("/tasks", json={"prompt": "Compare models on iris"})
    assert resp.status_code == 200
    task_id = resp.json()["id"]

    # 2. GET /tasks/{id}
    resp = await client.get(f"/tasks/{task_id}")
    task = resp.json()
    assert task["status"] == "completed"
    assert len(task["experiments"]) >= 1
    assert task["experiments"][0]["metrics"] is not None

    # 3. GET /health
    resp = await client.get("/health")
    assert resp.json()["status"] == "ok"
```

Uses `httpx.AsyncClient` with FastAPI `TestClient`. `StubAgent` ensures no LLM key needed.

---

## File Creation Order

Exact sequence to avoid import errors:

| # | What | Files |
|---|---|---|
| 1 | Project config | `pyproject.toml`, `Makefile`, `ruff.toml`, `.python-version` |
| 2 | Package init | `src/dojo/__init__.py`, `src/dojo/_version.py` |
| 3 | Utils | `utils/ids.py`, `utils/logging.py`, `utils/serialization.py` |
| 4 | Core models | `core/experiment.py`, `core/task.py`, `core/knowledge.py`, `core/state_machine.py` |
| 5 | Interfaces | All 8 interface files |
| 6 | Config | `config/settings.py`, `config/defaults.py` |
| 7 | Local backends | `compute/local.py`, `sandbox/local.py`, `storage/*`, `tracking/file_tracker.py` |
| 8 | Runtime | `runtime/lab.py`, `runtime/experiment_service.py` |
| 9 | Stub agent | `agents/stub_agent.py` |
| 10 | API | `api/deps.py`, `api/app.py`, `api/routers/*` |
| 11 | CLI | `cli/main.py`, `cli/start.py`, `cli/run.py`, `cli/config.py` |
| 12 | Tests | `conftest.py`, unit tests, e2e test |

---

## Dependency Summary

```toml
dependencies = [
    "typer>=0.15",
    "rich>=13.0",
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "httpx>=0.28",
    "structlog>=24.0",
    "python-ulid>=3.0",
]

[project.optional-dependencies]
anthropic = ["anthropic>=0.80"]
claude-agent = ["agents-sdk>=0.1"]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24", "pytest-cov>=6.0", "ruff>=0.11", "mypy>=1.10"]
```

No MLflow, no Streamlit, no heavy deps in the PoC. Added as optional extras later.

---

## What `dojo start` Does (PoC)

```
$ dojo start
  Dojo.ml v0.1.0
  ✓ FastAPI server → http://localhost:8000
  ✓ API docs       → http://localhost:8000/docs

  Press Ctrl+C to stop.
```

Single process. Uvicorn runs inline. No subprocess orchestration yet.

---

## What Is Explicitly Deferred

| Deferred | Why |
|---|---|
| Claude Agent SDK integration | Needs API key + prompt engineering — comes after scaffolding |
| MLflow tracking | Optional dependency, file tracker covers PoC |
| Streamlit UI | Not needed for PoC validation |
| Docker/Modal sandbox | Local subprocess is sufficient |
| Postgres storage | JSON files cover PoC |
| Async everywhere | Use sync where simpler for PoC; async interfaces ready for later |
| Knowledge synthesis via LLM | Stub returns empty atoms |
| SSE streaming | Polling or direct response for PoC |
