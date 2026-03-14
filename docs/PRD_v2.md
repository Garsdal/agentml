# Dojo.ml — Product Requirements Document

**Project name:** Dojo.ml
**Type:** Autonomous ML Research Framework
**Version:** 0.2 — Prompt-Driven Architecture
**Date:** 2026-02-25
**Status:** Draft

---

## Table of Contents

1. [Vision](#1-vision)
2. [Non-Goals](#2-non-goals)
3. [Core Concepts](#3-core-concepts)
4. [System Architecture](#4-system-architecture)
5. [User Journey](#5-user-journey)
6. [Project Structure](#6-project-structure)
7. [Module Specifications](#7-module-specifications)
8. [Connector Interfaces](#8-connector-interfaces)
9. [Storage & Persistence](#9-storage--persistence)
10. [Experiment State Machine](#10-experiment-state-machine)
11. [Knowledge Memory](#11-knowledge-memory)
12. [Agent System](#12-agent-system)
13. [Claude Agent SDK Integration Plan](#13-claude-agent-sdk-integration-plan)
14. [API Specification](#14-api-specification)
15. [CLI Specification](#15-cli-specification)
16. [UI Dashboard](#16-ui-dashboard)
17. [Configuration](#17-configuration)
18. [Phased Implementation Roadmap](#18-phased-implementation-roadmap)
19. [Success Criteria](#19-success-criteria)
20. [Appendix — Dependency Map & Tech Stack](#20-appendix--dependency-map--tech-stack)

---

## 1. Vision

Traditional ML platforms automate training pipelines. Dojo.ml automates **scientific execution**.

Instead of:

> Humans manually writing training scripts, evaluation harnesses, and comparison notebooks every time they have an ML hypothesis to test.

Dojo.ml provides:

> A prompt-driven ML research system: describe what you want to investigate in plain English, and autonomous agents write code, execute experiments, collect results, and accumulate reusable knowledge — all without you writing a single line of glue code.

The system must:

- Accept **natural-language research prompts** as its primary input
- **Write and execute its own code** in a sandboxed environment — no user-defined adapter classes
- Remain **interpretable and observable** — users watch the agent think and can inspect every line of generated code
- **Accumulate reusable knowledge** over time via structured knowledge atoms
- Be **fully swappable at every infrastructure layer** — sandbox, storage, tracking, and LLM provider can all be replaced without touching core logic

### What Dojo.ml Ultimately Is

Not AutoML. Not MLOps. It is:

> A prompt-to-results ML research engine: you state the hypothesis, it does the science.

### Future: Recursive Self-Improvement

In v1, the **user** provides the hypothesis. In a future version, a recursive meta-agent can wrap Dojo.ml to generate hypotheses autonomously — turning Dojo.ml into a continuously self-improving research organization. But that layer sits *above* Dojo.ml and is explicitly out of scope for the initial implementation. The architecture must not prevent this future wrapping.

---

## 2. Non-Goals

Dojo.ml is **not**:

| Not This | Why |
|---|---|
| A replacement for feature stores | Dojo.ml consumes features; it doesn't manage them |
| A new deep learning framework | It orchestrates existing frameworks (scikit-learn, XGBoost, PyTorch, etc.) via generated code |
| A hyperparameter tuner | It reasons about *what* to try based on a user's research prompt, not grid-search |
| A production inference service | It produces models and results; serving is out of scope |
| A data pipeline tool | It loads data via generated code; ETL is external |
| An autonomous hypothesis generator (v1) | The user states what to investigate; the agent executes |

---

## 3. Core Concepts

### 3.1 Prompt-Driven Research

The fundamental interaction model is:

```
User prompt → Agent planning → Code generation → Sandboxed execution → Results → Knowledge
```

The user provides a **research prompt** — a natural-language description of what to investigate:

```
"Load the Boston housing dataset from sklearn. Compare linear regression, random forest, and XGBoost.
Report RMSE and R² on a 80/20 train/test split. Use 5-fold cross-validation."
```

The agent:
1. **Plans** the approach (what datasets, what models, what evaluation strategy)
2. **Writes Python code** to implement each step
3. **Executes the code** in a sandboxed environment
4. **Collects results** (metrics, artifacts, plots)
5. **Records experiments** with full provenance (code, data, metrics)
6. **Extracts knowledge** (generalizable lessons from the results)

There is no adapter class to write. The agent generates all code.

### 3.2 Separation of Responsibilities

| Component | Responsibility | Swappable? |
|---|---|---|
| **User** | Provides the research prompt (hypothesis / investigation) | — |
| **Agent** | Planning, code generation, analysis, knowledge extraction | Yes — simple loop → Claude Agent SDK |
| **Sandbox** | Isolated code execution environment | Yes — local subprocess → Docker → Modal |
| **Experiment Engine** | Governance & lifecycle (state machine) | No — core invariant |
| **Tracking Connector** | Metrics & artifact logging | Yes — filesystem → MLflow (local) → MLflow (Postgres) |
| **Storage Backend** | Experiment/knowledge/agent state persistence | Yes — JSON files → Postgres |
| **LLM Connector** | LLM API calls for agent reasoning | Yes — Anthropic → OpenAI → local vLLM |
| **Knowledge Memory** | Learning across tasks | No — core invariant (storage backend swappable) |
| **UI** | Observability & control | Yes — Streamlit → React |

### 3.3 Design Principle: Protocol-Based Swappability

Every swappable component is defined as a Python `Protocol` (structural subtyping). Implementations are selected via configuration, not code changes. No inheritance hierarchies — if a class has the right methods, it satisfies the protocol.

```python
# Example — any class with these methods is a valid Sandbox
class Sandbox(Protocol):
    async def execute(self, code: str, timeout: int = 300) -> ExecutionResult: ...
    async def install_packages(self, packages: list[str]) -> None: ...
    async def upload_file(self, local_path: str, remote_path: str) -> None: ...
    async def download_file(self, remote_path: str) -> bytes: ...
    async def health_check(self) -> bool: ...
```

### 3.4 Why No ProblemAdapter?

Traditional ML frameworks require users to implement an adapter class with methods like `train()`, `evaluate()`, `get_dataset()`. This has several problems:

1. **Friction:** Users must learn an API and write boilerplate before getting any value.
2. **Rigidity:** The adapter interface constrains what the agent can do. If the agent wants to try a technique not covered by the interface (e.g., ensembling, custom preprocessing), it can't.
3. **Redundancy:** The agent is an LLM that can write arbitrary Python code. Forcing it to call pre-written functions is an artificial limitation.

Dojo.ml's approach: the agent **writes the code itself** and runs it in a sandbox. This means:

- **Zero integration cost:** Describe what you want, not how to do it
- **Unlimited flexibility:** The agent can try any technique expressible in Python
- **Self-contained experiments:** Every experiment includes its own code — fully reproducible
- **Natural upgrade path:** As LLMs improve, the agent's code quality improves automatically

The sandbox provides safety. The experiment state machine provides governance. The knowledge memory provides learning.

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User / Browser                           │
│                                                                 │
│  "Compare linear regression vs XGBoost on the Boston dataset"  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼────────────────────────────────────┐
│                     UI Dashboard (Streamlit)                     │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Tasks   │  │ Experiments│  │  Memory  │  │   Results    │  │
│  └──────────┘  └────────────┘  └──────────┘  └──────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (internal)
┌────────────────────────────▼────────────────────────────────────┐
│                   FastAPI Control Plane                          │
│  ┌────────────┐  ┌────────────────┐  ┌───────────────────────┐  │
│  │  Task API  │  │ Experiment API │  │   Knowledge API       │  │
│  └──────┬─────┘  └───────┬────────┘  └──────────┬────────────┘  │
└─────────┼────────────────┼──────────────────────┼───────────────┘
          │                │                      │
┌─────────▼────────────────▼──────────────────────▼───────────────┐
│                        Core Layer                                │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │    Agent      │  │ Experiment Engine│  │ Knowledge Memory  │  │
│  │  Supervisor   │  │  (State Machine) │  │   (Atoms Store)   │  │
│  └──────┬────────┘  └───────┬──────────┘  └──────────┬────────┘  │
└─────────┼───────────────────┼────────────────────────┼──────────┘
          │                   │                        │
┌─────────▼───────────────────▼────────────────────────▼──────────┐
│                    Connectors Layer                               │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐                  │
│  │ Sandbox  │  │ Tracking  │  │     LLM      │                  │
│  │          │  │ Connector │  │  Connector   │                  │
│  └──────────┘  └───────────┘  └──────────────┘                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Storage Backend (Repository)                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                │              │
    ┌─────▼─────┐   ┌─────▼─────┐  ┌─────▼─────┐
    │  Local /   │   │  MLflow   │  │ Anthropic │
    │  Docker /  │   │  Server   │  │ / OpenAI  │
    │  Modal     │   │           │  │ / vLLM    │
    └───────────┘   └───────────┘  └───────────┘
```

### 4.2 Process Model — `dojo start`

When the user runs `dojo start`, a single CLI command launches all services:

```
dojo start
  ├── FastAPI server         (uvicorn, port 8000)
  ├── MLflow tracking server (mlflow server, port 5000)
  ├── Streamlit UI           (streamlit run, port 8501)
  └── Agent Supervisor       (async background task inside FastAPI)
```

All services are managed by a **process supervisor** within the CLI. Each service is a subprocess. Graceful shutdown on `Ctrl+C` tears down all processes.

### 4.3 Layer Dependency Rules

Dependencies flow **downward only**:

```
CLI → API → Core → Connectors → External Systems
                 → Storage
```

- **CLI** depends on **API** (HTTP calls or direct imports).
- **API** depends on **Core** (domain logic).
- **Core** depends on **Connectors** (via Protocol interfaces only — never concrete implementations).
- **Core** depends on **Storage** (via Repository Protocol).
- **Connectors** depend on **External Systems** (MLflow, Modal, Anthropic, filesystem).

**Forbidden dependencies:**

- Core MUST NOT import from API or CLI.
- Connectors MUST NOT import from Core.
- Storage MUST NOT import from Connectors.

---

## 5. User Journey

### Step 1 — Install

```bash
pip install dojo
```

### Step 2 — Configure an LLM

```bash
dojo config init
```

This creates `.dojo/config.yaml` with sensible defaults. The user adds their LLM API key:

```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  api_key: ${ANTHROPIC_API_KEY}
```

### Step 3 — Start the platform

```bash
dojo start
```

User sees:

```
✓ MLflow tracking server    → http://localhost:5000
✓ FastAPI control plane      → http://localhost:8000
✓ Agent supervisor           → running
✓ Dojo.ml dashboard          → http://localhost:8501
```

### Step 4 — Run a task (the core interaction)

**From the CLI (simplest):**

```bash
dojo run "Load the Boston housing dataset from sklearn. \
  Compare linear regression vs XGBoost. \
  Report RMSE and R² using 5-fold cross-validation."
```

**From the CLI (with data):**

```bash
dojo run "Find the best classifier for predicting churn" \
  --data ./customers.csv
```

**From the CLI (with a workspace):**

```bash
dojo run "Improve the model accuracy in train.py" \
  --workspace ./my_project
```

**From the UI dashboard:**

> New Task → type your research prompt → (optionally attach data files) → Start

### Step 5 — Watch the agent work

The agent:

1. **Plans** — breaks the prompt into sub-tasks (load data, train model A, train model B, evaluate, compare)
2. **Writes code** — generates Python scripts for each sub-task
3. **Executes** — runs code in the sandbox, installs packages as needed
4. **Collects results** — parses outputs, logs metrics
5. **Reports** — presents a structured comparison with all metrics

The user watches this in the UI:

- **Agent thoughts** — the reasoning at each step
- **Generated code** — every script the agent wrote (inspectable, rerunnable)
- **Execution output** — stdout/stderr from each run
- **Results table** — metrics comparison across all experiments
- **Knowledge learned** — what generalizable lessons the agent extracted

### Step 6 — Run more tasks

Each new task benefits from knowledge accumulated in previous tasks:

```bash
dojo run "Compare random forest vs XGBoost on this credit scoring dataset" \
  --data ./credit_data.csv
```

The agent checks its knowledge memory before planning. If it learned from a previous task that "XGBoost outperforms random forest on tabular data with high-cardinality categoricals," it might design the experiment differently — using smarter hyperparameter ranges or trying additional encoding strategies.

### What the user NEVER has to do:

- ❌ Write an adapter class
- ❌ Implement a training function
- ❌ Define an evaluation harness
- ❌ Learn a framework-specific API
- ❌ Write LLM prompts
- ❌ Configure experiment tracking manually

---

## 6. Project Structure

```
dojo/
├── pyproject.toml                      # PEP 621 — single source of truth
├── README.md
├── LICENSE
├── CHANGELOG.md
├── Makefile                            # Dev shortcuts: make test, make lint, make run
├── PRD.md                              # This document
│
├── src/
│   └── dojo/                        # Importable package (src layout)
│       ├── __init__.py                 # Public API exports
│       ├── _version.py                 # Package version
│       │
│       │── ─── CLI ──────────────────────────────────────────────
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py                 # Typer app — entry point
│       │   ├── start.py                # `dojo start` — launch all services
│       │   ├── run.py                  # `dojo run "<prompt>"` — submit a task
│       │   ├── task.py                 # `dojo task list/show/cancel`
│       │   └── config.py              # `dojo config init/show/set`
│       │
│       │── ─── API ──────────────────────────────────────────────
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py                  # FastAPI app factory (create_app)
│       │   ├── deps.py                 # Dependency injection container
│       │   ├── middleware.py            # CORS, request logging, error handling
│       │   └── routers/
│       │       ├── __init__.py
│       │       ├── tasks.py            # POST/GET /tasks — submit & manage tasks
│       │       ├── experiments.py      # CRUD + state transitions for experiments
│       │       ├── knowledge.py        # GET /knowledge, /knowledge/relevant
│       │       └── health.py           # GET /health — readiness + dependency checks
│       │
│       │── ─── CORE ─────────────────────────────────────────────
│       ├── core/
│       │   ├── __init__.py
│       │   │
│       │   ├── task/
│       │   │   ├── __init__.py
│       │   │   ├── models.py           # Task, TaskStatus, TaskResult dataclasses
│       │   │   └── manager.py          # TaskManager — creates tasks, dispatches to agents
│       │   │
│       │   ├── agent/
│       │   │   ├── __init__.py
│       │   │   ├── supervisor.py       # AgentSupervisor — manages agent lifecycles
│       │   │   ├── base.py             # Agent protocol
│       │   │   ├── simple.py           # SimpleAgent — Phase 1 (raw LLM tool loop)
│       │   │   ├── claude_agent.py     # ClaudeAgent — Phase 2 (Claude Agent SDK)
│       │   │   ├── planner.py          # Breaks a user prompt into executable steps
│       │   │   └── tools.py            # Agent tools (execute_code, log_metric, etc.)
│       │   │
│       │   ├── experiment/
│       │   │   ├── __init__.py
│       │   │   ├── engine.py           # ExperimentEngine — orchestrates lifecycle
│       │   │   ├── state_machine.py    # StateMachine — transition enforcement
│       │   │   └── models.py           # Experiment, ExperimentResult dataclasses
│       │   │
│       │   ├── knowledge/
│       │   │   ├── __init__.py
│       │   │   ├── memory.py           # KnowledgeMemory — query & retrieval
│       │   │   ├── synthesis.py        # Extract atoms from completed experiments
│       │   │   ├── models.py           # KnowledgeAtom, Evidence dataclasses
│       │   │   └── relevance.py        # Relevance scoring for cross-task transfer
│       │   │
│       │   └── models.py               # Shared domain models (ExecutionResult, etc.)
│       │
│       │── ─── CONNECTORS ───────────────────────────────────────
│       ├── connectors/
│       │   ├── __init__.py
│       │   ├── registry.py             # ConnectorRegistry — resolve by config
│       │   │
│       │   ├── sandbox/
│       │   │   ├── __init__.py
│       │   │   ├── base.py             # Sandbox Protocol
│       │   │   ├── local.py            # LocalSandbox — subprocess execution
│       │   │   ├── docker.py           # DockerSandbox — container-isolated
│       │   │   └── modal.py            # ModalSandbox — Modal.com serverless
│       │   │
│       │   ├── tracking/
│       │   │   ├── __init__.py
│       │   │   ├── base.py             # TrackingConnector Protocol
│       │   │   ├── mlflow_tracker.py   # MLflowTracker — MLflow integration
│       │   │   └── file_tracker.py     # FileTracker — JSON files (fallback)
│       │   │
│       │   └── llm/
│       │       ├── __init__.py
│       │       ├── base.py             # LLMConnector Protocol
│       │       ├── anthropic.py        # AnthropicLLM — Claude via anthropic SDK
│       │       └── openai.py           # OpenAILLM — GPT models
│       │
│       │── ─── STORAGE ──────────────────────────────────────────
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── base.py                 # Repository protocols
│       │   ├── filesystem.py           # JSON/YAML file-based storage
│       │   ├── postgres.py             # PostgreSQL via SQLAlchemy (Phase 2)
│       │   └── migrations/             # Alembic migrations (Phase 2)
│       │       ├── env.py
│       │       └── versions/
│       │
│       │── ─── CONFIG ───────────────────────────────────────────
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py             # Pydantic Settings — .dojo/config.yaml + env
│       │   └── defaults.py             # Default configuration values
│       │
│       │── ─── UTILS ────────────────────────────────────────────
│       └── utils/
│           ├── __init__.py
│           ├── logging.py              # Structured logging (structlog)
│           ├── serialization.py        # JSON/YAML/datetime serializers
│           ├── process.py              # Process management for `dojo start`
│           └── ids.py                  # ID generation (ULIDs)
│
│── ─── FRONTEND ─────────────────────────────────────────────────
├── frontend/
│   ├── app.py                          # Streamlit entry point (Phase 1)
│   ├── pages/
│   │   ├── tasks.py                    # Task submission & monitoring
│   │   ├── experiments.py              # Experiment browser & detail views
│   │   ├── knowledge.py               # Knowledge atom explorer
│   │   └── results.py                 # Result comparison & visualization
│   ├── components/
│   │   ├── task_input.py              # Prompt input with data attachment
│   │   ├── experiment_card.py          # Reusable experiment display
│   │   ├── code_viewer.py             # Syntax-highlighted code display
│   │   ├── knowledge_atom.py          # Knowledge atom visualization
│   │   ├── agent_thought.py           # Agent reasoning display
│   │   └── metric_chart.py            # Metric visualization
│   └── api_client.py                  # HTTP client to FastAPI backend
│
│── ─── TESTS ────────────────────────────────────────────────────
├── tests/
│   ├── conftest.py                     # Shared fixtures, test config
│   ├── unit/
│   │   ├── core/
│   │   │   ├── test_state_machine.py
│   │   │   ├── test_experiment_engine.py
│   │   │   ├── test_knowledge_memory.py
│   │   │   ├── test_task_manager.py
│   │   │   └── test_agent_supervisor.py
│   │   ├── connectors/
│   │   │   ├── test_local_sandbox.py
│   │   │   ├── test_mlflow_tracker.py
│   │   │   └── test_anthropic_llm.py
│   │   └── storage/
│   │       ├── test_filesystem_storage.py
│   │       └── test_postgres_storage.py
│   ├── integration/
│   │   ├── test_api_tasks.py
│   │   ├── test_api_experiments.py
│   │   ├── test_task_to_results.py
│   │   └── test_sandbox_execution.py
│   └── e2e/
│       └── test_full_task_lifecycle.py
│
│── ─── EXAMPLES ─────────────────────────────────────────────────
└── examples/
    ├── README.md                       # Example prompts and expected behavior
    └── sample_data/
        ├── customers.csv               # Sample dataset for demo tasks
        └── transactions.csv
```

### 6.1 Why `src/` Layout?

The `src/` layout prevents accidental imports from the working directory during development. When you run `python -c "import dojo"` from the repo root, it forces the installed package to be used — never the raw source directory.

### 6.2 Why No `core/problem/` Directory?

In the previous architecture, a `problem/` module housed the `ProblemAdapter` ABC and registry. This is gone. Instead:

- **`core/task/`** handles user-submitted research prompts (the Task concept replaces the Problem concept)
- **`core/agent/tools.py`** provides tools like `execute_code`, `install_packages`, `read_file` — these replace the adapter's `train()`, `evaluate()`, `get_dataset()` methods
- **`connectors/sandbox/`** provides the isolated execution environment where generated code runs

The agent writes all domain-specific code. No user-supplied Python class needed.

---

## 7. Module Specifications

### 7.1 CLI (`cli/`)

**Framework:** Typer (auto-generates `--help`, leverages type hints)

**Entry point** in `pyproject.toml`:

```toml
[project.scripts]
dojo = "dojo.cli.main:app"
```

**Commands:**

| Command | Module | Description |
|---|---|---|
| `dojo start` | `cli/start.py` | Launch all services (FastAPI, MLflow, Streamlit, Supervisor) |
| `dojo stop` | `cli/start.py` | Graceful shutdown of all services |
| `dojo run "<prompt>"` | `cli/run.py` | Submit a research task and optionally watch it execute |
| `dojo task list` | `cli/task.py` | List all tasks |
| `dojo task show <task_id>` | `cli/task.py` | Show task detail and results |
| `dojo task cancel <task_id>` | `cli/task.py` | Cancel a running task |
| `dojo config init` | `cli/config.py` | Create default config file |
| `dojo config show` | `cli/config.py` | Display current configuration |
| `dojo config set <key> <value>` | `cli/config.py` | Update configuration |

**`dojo start` behavior:**

```python
# Pseudocode for cli/start.py
def start():
    settings = load_settings()
    processes = []

    # 1. Start MLflow tracking server
    processes.append(launch_mlflow(
        backend_uri=settings.tracking.backend_uri,  # file:./mlruns or postgresql://
        port=settings.tracking.port,                 # default 5000
    ))

    # 2. Start FastAPI control plane (includes agent supervisor)
    processes.append(launch_fastapi(
        host=settings.api.host,
        port=settings.api.port,                      # default 8000
    ))

    # 3. Start Streamlit UI
    processes.append(launch_streamlit(
        port=settings.ui.port,                       # default 8501
    ))

    # Register signal handlers for graceful shutdown
    register_shutdown_handler(processes)
    wait_for_interrupt()
```

**`dojo run` behavior:**

```python
# Pseudocode for cli/run.py
def run(
    prompt: str,
    data: list[Path] | None = None,
    workspace: Path | None = None,
    watch: bool = True,
):
    # 1. Submit task to API
    task = api_client.create_task(
        prompt=prompt,
        data_files=data,
        workspace=workspace,
    )

    # 2. Optionally stream progress to terminal
    if watch:
        for event in api_client.stream_task(task.id):
            render_event(event)  # agent thoughts, code, results
    else:
        print(f"Task {task.id} submitted. View at http://localhost:8501")
```

### 7.2 API (`api/`)

**Framework:** FastAPI with async/await throughout.

**App factory pattern** (`api/app.py`):

```python
def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="Dojo.ml", version=__version__)

    # Dependency injection — wire connectors based on settings
    container = build_container(settings)
    app.state.container = container

    # Register routers
    app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
    app.include_router(experiments_router, prefix="/experiments", tags=["experiments"])
    app.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
    app.include_router(health_router, tags=["health"])

    # Middleware
    app.add_middleware(CORSMiddleware, ...)

    # Lifecycle — start/stop agent supervisor
    @app.on_event("startup")
    async def startup():
        container.agent_supervisor.start()

    return app
```

**Dependency injection** (`api/deps.py`):

```python
def build_container(settings: Settings) -> Container:
    """Build the dependency container from settings.

    This is the ONLY place where concrete implementations are selected.
    Everything else uses Protocol interfaces.
    """
    return Container(
        sandbox=resolve_sandbox(settings.sandbox),         # local, docker, or modal
        tracking=resolve_tracking_connector(settings.tracking),  # mlflow or file
        llm=resolve_llm_connector(settings.llm),           # anthropic or openai
        storage=resolve_storage_backend(settings.storage),  # filesystem or postgres
    )
```

### 7.3 Core — Task (`core/task/`)

The **Task** is the top-level domain object. It represents a user's research prompt and tracks its lifecycle from submission to completion.

#### `models.py` — Task Models

```python
class TaskStatus(str, Enum):
    PENDING = "pending"          # Submitted, not yet started
    PLANNING = "planning"        # Agent is planning the approach
    EXECUTING = "executing"      # Agent is running experiments
    COMPLETED = "completed"      # All experiments done, results available
    FAILED = "failed"            # Something went wrong
    CANCELLED = "cancelled"      # User cancelled

@dataclass
class Task:
    id: str
    prompt: str                       # The user's research prompt
    data_files: list[str] | None      # Paths to attached data files
    workspace: str | None             # Path to user's project directory
    status: TaskStatus
    agent_id: str | None              # Agent assigned to this task
    experiment_ids: list[str]         # Experiments created for this task
    plan: TaskPlan | None             # Agent's plan for executing the task
    result: TaskResult | None         # Final aggregated results
    created_at: datetime
    updated_at: datetime

@dataclass
class TaskPlan:
    """The agent's plan for executing the task."""
    steps: list[TaskStep]             # Ordered list of steps
    reasoning: str                    # Why the agent chose this plan

@dataclass
class TaskStep:
    description: str                  # "Load Boston housing dataset"
    step_type: str                    # "data_loading", "training", "evaluation", "comparison"
    status: str                       # "pending", "running", "completed", "failed"
    experiment_id: str | None         # Link to experiment if created

@dataclass
class TaskResult:
    """Aggregated results from all experiments in a task."""
    summary: str                      # Agent-generated summary of findings
    best_experiment_id: str | None    # Best performing experiment
    metrics_comparison: dict          # {"linear_regression": {"rmse": 4.2}, "xgboost": {"rmse": 2.8}}
    knowledge_atoms: list[str]        # IDs of knowledge atoms created
    artifacts: dict[str, str]         # {"comparison_plot": "path/to/plot.png"}
```

#### `manager.py` — TaskManager

```python
class TaskManager:
    """Creates tasks and dispatches them to agents."""

    def __init__(
        self,
        storage: TaskRepository,
        supervisor: AgentSupervisor,
    ):
        self._storage = storage
        self._supervisor = supervisor

    async def create_task(
        self,
        prompt: str,
        data_files: list[str] | None = None,
        workspace: str | None = None,
    ) -> Task:
        """Create a new task from a user prompt and dispatch to an agent."""
        task = Task(
            id=generate_id(),
            prompt=prompt,
            data_files=data_files,
            workspace=workspace,
            status=TaskStatus.PENDING,
            ...
        )
        await self._storage.save(task)

        # Dispatch to an agent
        agent_id = await self._supervisor.assign_task(task)
        task.agent_id = agent_id
        task.status = TaskStatus.PLANNING
        await self._storage.update(task)

        return task

    async def get_task(self, task_id: str) -> Task | None: ...
    async def list_tasks(self, **filters) -> list[Task]: ...
    async def cancel_task(self, task_id: str) -> None: ...
```

### 7.4 Core — Agent (`core/agent/`)

#### `supervisor.py` — AgentSupervisor

Manages the lifecycle of agents. When a task arrives, it assigns or creates an agent to handle it.

```python
class AgentSupervisor:
    """Manages agent lifecycles."""

    def __init__(self, container: Container):
        self._agents: dict[str, RunningAgent] = {}
        self._container = container

    async def assign_task(self, task: Task) -> str:
        """Assign a task to an agent. Creates one if needed. Returns agent_id."""

    async def stop_agent(self, agent_id: str) -> None:
        """Gracefully stop an agent."""

    async def get_agent_state(self, agent_id: str) -> AgentState:
        """Get current state: what the agent is doing, its thoughts, etc."""

    async def list_agents(self) -> list[AgentSummary]: ...
```

#### `base.py` — Agent Protocol

```python
class Agent(Protocol):
    """Protocol that all agent implementations must satisfy."""

    async def execute_task(self, task: Task, context: AgentContext) -> TaskResult:
        """Execute a user's research task end-to-end.

        The agent:
        1. Plans the approach (breaks prompt into steps)
        2. Writes code for each step
        3. Executes code in the sandbox
        4. Collects and interprets results
        5. Extracts knowledge
        6. Returns aggregated results

        The AgentContext provides access to:
        - sandbox: for code execution
        - tracking: for logging metrics
        - knowledge: for querying past learnings
        - experiment_engine: for recording experiments
        """
        ...
```

#### `simple.py` — SimpleAgent (Phase 1)

Uses the `anthropic` Python SDK with `tool_runner()` for an agentic tool loop:

```python
class SimpleAgent:
    """Phase 1 agent: direct LLM calls with tool-use loop.

    The agent receives a user prompt and has tools to:
    - execute Python code in a sandbox
    - install packages in the sandbox
    - read/write files in the sandbox
    - log experiments (metrics, artifacts)
    - query knowledge memory
    - upload data files to the sandbox
    """

    def __init__(self, llm: LLMConnector, sandbox: Sandbox, ...):
        self._llm = llm
        self._sandbox = sandbox
        ...

    async def execute_task(self, task: Task, context: AgentContext) -> TaskResult:
        # Build the system prompt + user message
        messages = self._build_messages(task, context)

        # Run the LLM tool loop — the agent calls tools iteratively
        # until it's done (or hits budget limits)
        responses = await self._llm.chat_with_tool_loop(
            messages=messages,
            tools=self._build_tools(context),
            max_iterations=context.config.max_iterations,
        )

        # Extract the final result from the conversation
        return self._extract_result(task, responses)
```

#### `tools.py` — Agent Tools

These are the tools the agent can call during execution. They replace the old ProblemAdapter methods:

| Tool | Replaces | Description |
|---|---|---|
| `execute_code(code: str)` | `adapter.train()`, `adapter.evaluate()`, `adapter.get_dataset()` | Run arbitrary Python code in the sandbox |
| `install_packages(packages: list[str])` | — | Install pip packages in the sandbox |
| `read_file(path: str)` | `adapter.list_features()` | Read a file from the sandbox or workspace |
| `write_file(path: str, content: str)` | — | Write a file to the sandbox |
| `upload_data(local_path: str)` | `adapter.get_dataset()` | Upload user's data files to sandbox |
| `log_experiment(hypothesis: str, metrics: dict, code: str)` | — | Record a structured experiment |
| `query_knowledge(context: str)` | — | Search knowledge memory for relevant atoms |
| `get_task_context()` | `adapter.describe_problem()` | Get the current task prompt, data files, etc. |

```python
# Example tool definitions for Phase 1 (raw anthropic SDK)
AGENT_TOOLS = [
    {
        "name": "execute_code",
        "description": "Execute Python code in a sandboxed environment. Returns stdout, stderr, and any files created.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 300},
            },
            "required": ["code"],
        },
    },
    {
        "name": "install_packages",
        "description": "Install Python packages in the sandbox environment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "packages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of pip packages to install, e.g. ['scikit-learn', 'xgboost']",
                },
            },
            "required": ["packages"],
        },
    },
    {
        "name": "log_experiment",
        "description": "Record a completed experiment with its hypothesis, code, and metrics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Short name, e.g. 'linear_regression_baseline'"},
                "hypothesis": {"type": "string", "description": "What this experiment was testing"},
                "code": {"type": "string", "description": "The Python code that was executed"},
                "metrics": {"type": "object", "description": "Result metrics, e.g. {'rmse': 4.2, 'r2': 0.78}"},
                "artifacts": {
                    "type": "object",
                    "description": "Paths to generated files, e.g. {'model': 'model.pkl'}",
                },
            },
            "required": ["name", "hypothesis", "code", "metrics"],
        },
    },
    {
        "name": "query_knowledge",
        "description": "Search knowledge memory for relevant learnings from past tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context": {"type": "string", "description": "Describe the current situation to find relevant knowledge"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["context"],
        },
    },
]
```

#### System Prompt

```
You are an ML research agent. The user gives you a research prompt describing what
ML experiments to run. Your job is to execute the research end-to-end:

1. Understand the prompt — what data, what models, what metrics, what comparisons
2. Plan your approach — break it into clear steps
3. Write Python code for each step and execute it in your sandbox
4. Collect results and log each experiment with log_experiment()
5. Compare results and provide a clear summary
6. Before starting, check query_knowledge() for relevant past learnings

Rules:
- Always install required packages before using them
- Write clean, readable code — the user will inspect it
- Log every experiment with clear hypothesis and metrics
- Handle errors gracefully — if code fails, debug and retry
- Use the data files the user provided (if any)
- Be thorough but efficient — don't run unnecessary experiments
```

#### Budget & Safety Controls

```python
@dataclass
class AgentConfig:
    max_iterations: int = 30          # Max LLM tool-loop iterations per task
    max_cost_usd: float = 5.0         # Max LLM spend per task
    max_execution_time: int = 600     # Max sandbox execution time per code block (seconds)
    sandbox_memory_mb: int = 4096     # Sandbox memory limit
```

### 7.5 Core — Experiment (`core/experiment/`)

#### `models.py` — Domain Models

Experiments now contain the **generated code** as a first-class field:

```python
@dataclass
class Experiment:
    id: str
    task_id: str                      # Parent task
    name: str                         # "linear_regression_baseline"
    hypothesis: str                   # "Linear regression provides a simple baseline"
    code: str                         # The actual Python code that was executed
    state: ExperimentState            # RUNNING, COMPLETED, FAILED
    metrics: dict[str, float] | None  # {"rmse": 4.2, "r2": 0.78}
    artifacts: dict[str, str] | None  # {"model": "path/to/model.pkl"}
    stdout: str | None                # Execution output
    stderr: str | None                # Execution errors
    duration_seconds: float | None
    analysis: str | None              # Agent's interpretation of results
    created_at: datetime
    updated_at: datetime
```

Note: the experiment state machine is simpler than v0.1 because the agent manages the full lifecycle within a single task. The engine still enforces valid states, but there are fewer transitions:

```python
class ExperimentState(str, Enum):
    RUNNING = "running"         # Code is executing in sandbox
    COMPLETED = "completed"     # Execution finished, metrics collected
    FAILED = "failed"           # Execution failed
    ARCHIVED = "archived"       # Frozen for reproducibility
```

#### `engine.py` — ExperimentEngine

```python
class ExperimentEngine:
    """Records and manages experiments within a task."""

    def __init__(
        self,
        tracking: TrackingConnector,
        storage: ExperimentRepository,
    ): ...

    async def record_experiment(
        self,
        task_id: str,
        name: str,
        hypothesis: str,
        code: str,
        metrics: dict[str, float],
        artifacts: dict[str, str] | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        duration: float | None = None,
    ) -> Experiment:
        """Record a completed experiment. Logs to tracking + storage."""

    async def get_experiment(self, experiment_id: str) -> Experiment | None: ...
    async def list_by_task(self, task_id: str) -> list[Experiment]: ...
    async def compare_experiments(self, experiment_ids: list[str]) -> dict: ...
```

### 7.6 Core — Knowledge (`core/knowledge/`)

#### `models.py` — Knowledge Atom

```python
@dataclass
class KnowledgeAtom:
    id: str
    context: str                      # "tabular classification, high-cardinality categoricals"
    claim: str                        # "XGBoost outperforms linear models by 8-15% on recall"
    action: str                       # "Start with tree ensembles for tabular classification"
    confidence: float                 # 0.0 - 1.0
    evidence_count: int
    evidence_ids: list[str]           # Experiment IDs
    task_names: list[str]             # Which tasks contributed
    created_at: datetime
    updated_at: datetime
    superseded_by: str | None
```

#### `memory.py` — KnowledgeMemory

```python
class KnowledgeMemory:
    """Query and manage knowledge atoms."""

    def __init__(self, storage: KnowledgeRepository):
        self._storage = storage

    async def get_relevant(self, context: str, limit: int = 10) -> list[KnowledgeAtom]:
        """Find knowledge atoms relevant to the given context.
        Phase 1: keyword matching.
        Phase 2: embedding similarity.
        """

    async def add_atom(self, atom: KnowledgeAtom) -> None: ...
    async def update_confidence(self, atom_id: str, new_evidence: str) -> KnowledgeAtom: ...
    async def get_all(self) -> list[KnowledgeAtom]: ...
    async def provide_feedback(self, atom_id: str, feedback: str) -> None: ...
```

#### `synthesis.py` — KnowledgeSynthesizer

```python
class KnowledgeSynthesizer:
    """Extract knowledge atoms from completed tasks using the LLM."""

    async def synthesize(
        self,
        task: Task,
        experiments: list[Experiment],
        existing_knowledge: list[KnowledgeAtom],
        llm: LLMConnector,
    ) -> list[KnowledgeAtom]:
        """After a task completes, ask the LLM to extract generalizable knowledge.

        The LLM determines:
        - What generalizable claim can be made from these experiments
        - What context it applies to (not just this specific dataset)
        - Whether it confirms, contradicts, or extends existing atoms
        """
```

### 7.7 Agent Thought Logging

Every LLM interaction is logged as an `AgentThought`:

```python
@dataclass
class AgentThought:
    id: str
    agent_id: str
    task_id: str
    timestamp: datetime
    type: str                 # "planning", "code_generation", "tool_call",
                              # "tool_result", "analysis", "decision"
    content: str              # Raw text or structured data
    tokens_used: int
    cost_usd: float
```

Persisted in the agent state repository and surfaced in the UI — users watch the agent think.

---

## 8. Connector Interfaces

### 8.1 Sandbox (replaces ComputeConnector + ProblemAdapter)

The **Sandbox** is where the agent's generated code executes. It provides an isolated Python environment with package installation, file I/O, and execution.

```python
from typing import Protocol

class Sandbox(Protocol):
    """Isolated Python execution environment for agent-generated code."""

    async def execute(self, code: str, timeout: int = 300) -> ExecutionResult:
        """Execute Python code. Returns stdout, stderr, exit code, created files."""
        ...

    async def install_packages(self, packages: list[str]) -> ExecutionResult:
        """Install pip packages in the sandbox environment."""
        ...

    async def upload_file(self, local_path: str, remote_path: str) -> None:
        """Upload a file into the sandbox (e.g., user's dataset)."""
        ...

    async def download_file(self, remote_path: str) -> bytes:
        """Download a file from the sandbox (e.g., trained model, plot)."""
        ...

    async def list_files(self, path: str = ".") -> list[str]:
        """List files in the sandbox workspace."""
        ...

    async def reset(self) -> None:
        """Reset the sandbox to a clean state."""
        ...

    async def health_check(self) -> bool:
        """Check if the sandbox is operational."""
        ...


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    files_created: list[str]      # New files created during execution
    duration_seconds: float
```

**Implementations:**

| Class | Module | Phase | Description |
|---|---|---|---|
| `LocalSandbox` | `connectors/sandbox/local.py` | 1 | Runs code in a local subprocess with a temp directory. Simple but no isolation. |
| `DockerSandbox` | `connectors/sandbox/docker.py` | 2 | Runs code in a Docker container. Memory/CPU limits, network isolation. |
| `ModalSandbox` | `connectors/sandbox/modal.py` | 3 | Runs code on Modal.com serverless. GPU support, auto-scaling. |

#### LocalSandbox Details (Phase 1)

```python
class LocalSandbox:
    """Runs agent code in a local subprocess with a temporary working directory.

    Not isolated — the agent can access the host filesystem.
    Suitable for development and trusted environments.
    """

    def __init__(self, work_dir: Path | None = None):
        self._work_dir = work_dir or Path(tempfile.mkdtemp(prefix="dojo_"))

    async def execute(self, code: str, timeout: int = 300) -> ExecutionResult:
        # Write code to a temp .py file in work_dir
        # Run via subprocess: python temp_script.py
        # Capture stdout, stderr, exit code
        # List newly created files
        ...

    async def install_packages(self, packages: list[str]) -> ExecutionResult:
        # Run: pip install <packages> in the sandbox's Python environment
        ...

    async def upload_file(self, local_path: str, remote_path: str) -> None:
        # Copy file into work_dir
        ...
```

### 8.2 TrackingConnector

```python
class TrackingConnector(Protocol):
    """Tracks experiment metrics, parameters, and artifacts."""

    async def create_experiment(self, name: str) -> str:
        """Create a tracking experiment group. Returns experiment_id."""
        ...

    async def start_run(self, experiment_id: str, run_name: str) -> str:
        """Start a tracking run. Returns run_id."""
        ...

    async def log_params(self, run_id: str, params: dict) -> None: ...
    async def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None: ...
    async def log_artifact(self, run_id: str, local_path: str) -> None: ...
    async def end_run(self, run_id: str, status: str = "FINISHED") -> None: ...
    async def get_best_run(self, experiment_id: str, metric: str) -> dict: ...
```

**Implementations:**

| Class | Module | Phase | Backend |
|---|---|---|---|
| `MLflowTracker` | `connectors/tracking/mlflow_tracker.py` | 1 | MLflow with file store or Postgres |
| `FileTracker` | `connectors/tracking/file_tracker.py` | 1 | Plain JSON files (no MLflow dependency) |

### 8.3 LLMConnector

```python
class LLMConnector(Protocol):
    """Provides LLM capabilities for agent reasoning."""

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a chat completion request, optionally with tools."""
        ...

    async def chat_with_tool_loop(
        self,
        messages: list[dict],
        tools: list[callable],
        max_iterations: int = 10,
    ) -> list[LLMResponse]:
        """Run an agentic tool loop until the LLM stops calling tools."""
        ...

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for budget tracking."""
        ...
```

**Implementations:**

| Class | Module | Phase | SDK |
|---|---|---|---|
| `AnthropicLLM` | `connectors/llm/anthropic.py` | 1 | `anthropic` SDK with `tool_runner()` |
| `OpenAILLM` | `connectors/llm/openai.py` | 2 | `openai` SDK |

### 8.4 Storage Backend (Repository Pattern)

```python
class TaskRepository(Protocol):
    async def save(self, task: Task) -> None: ...
    async def get(self, task_id: str) -> Task | None: ...
    async def list(self, **filters) -> list[Task]: ...
    async def update(self, task: Task) -> None: ...

class ExperimentRepository(Protocol):
    async def save(self, experiment: Experiment) -> None: ...
    async def get(self, experiment_id: str) -> Experiment | None: ...
    async def list_by_task(self, task_id: str) -> list[Experiment]: ...
    async def list(self, **filters) -> list[Experiment]: ...
    async def update(self, experiment: Experiment) -> None: ...

class KnowledgeRepository(Protocol):
    async def save(self, atom: KnowledgeAtom) -> None: ...
    async def get(self, atom_id: str) -> KnowledgeAtom | None: ...
    async def list(self) -> list[KnowledgeAtom]: ...
    async def search(self, query: str, limit: int = 10) -> list[KnowledgeAtom]: ...
    async def update(self, atom: KnowledgeAtom) -> None: ...

class AgentStateRepository(Protocol):
    async def save_state(self, agent_id: str, state: AgentState) -> None: ...
    async def get_state(self, agent_id: str) -> AgentState | None: ...
    async def append_thought(self, agent_id: str, thought: AgentThought) -> None: ...
    async def get_thoughts(self, agent_id: str, limit: int = 50) -> list[AgentThought]: ...
```

**Implementations:**

| Class | Module | Phase |
|---|---|---|
| `FileSystemStorage` | `storage/filesystem.py` | 1 |
| `PostgresStorage` | `storage/postgres.py` | 2 |

### 8.5 Phase 1 File Storage Layout

```
.dojo/
├── config.yaml                    # User configuration
└── data/
    ├── tasks/
    │   ├── task_01J7K9...json     # One file per task
    │   └── task_01J7KB...json
    ├── experiments/
    │   ├── exp_01J7K9...json      # One file per experiment (includes code)
    │   └── exp_01J7KB...json
    ├── knowledge/
    │   └── atoms.json             # All knowledge atoms
    ├── agents/
    │   ├── agent_01J7K...json     # Agent state + thought history
    │   └── agent_01J7M...json
    └── sandboxes/
        └── sandbox_01J7.../       # Sandbox working directories
            ├── script_001.py      # Generated code
            ├── output.csv
            └── model.pkl
```

---

## 9. Storage & Persistence

### 9.1 Strategy: Start Simple, Migrate Cleanly

| Phase | Storage | Backend | Migration Path |
|---|---|---|---|
| **1** | JSON files | Local filesystem | — |
| **2** | PostgreSQL | SQLAlchemy + Alembic | Alembic migration scripts |
| **3** | PostgreSQL + S3 | Postgres for metadata, S3 for artifacts | Add S3 connector |

The Repository Pattern makes this seamless. Core logic calls `repository.save(task)` — whether that writes a JSON file or inserts a Postgres row is invisible to the caller.

### 9.2 MLflow Storage

MLflow also has a swappable backend:

| Phase | MLflow Backend Store | MLflow Artifact Store |
|---|---|---|
| **1** | `file:./mlruns` | `./mlruns/artifacts/` |
| **2** | `postgresql://...` | S3 or local |

The `dojo start` command passes the backend URI to `mlflow server --backend-store-uri`.

---

## 10. Experiment State Machine

### 10.1 Simplified State Machine (v0.2)

Because the user provides the hypothesis and the agent manages execution end-to-end within a tool loop, the experiment state machine is simpler:

```
           ┌──────────┐
           │ RUNNING  │◄── Agent executes code in sandbox
           └────┬─────┘
                │
       ┌────────┼────────┐
       │                 │
  ┌────▼─────┐    ┌─────▼────┐
  │COMPLETED │    │  FAILED  │
  └────┬─────┘    └─────┬────┘
       │                │
       └────────┬───────┘
                │
         ┌──────▼──────┐
         │  ARCHIVED   │ ◄── terminal (frozen for reproducibility)
         └─────────────┘
```

### 10.2 State Behaviors

| State | What Happens | Who Acts |
|---|---|---|
| **RUNNING** | Code is executing in the sandbox | Agent → Sandbox |
| **COMPLETED** | Execution finished successfully. Metrics and artifacts collected. | Engine |
| **FAILED** | Code execution failed. stderr captured. Agent may retry with different code. | Engine |
| **ARCHIVED** | Frozen. Code, metrics, stdout, stderr all preserved. Immutable. | Engine |

### 10.3 Task-Level Governance

The heavier governance now lives at the **Task** level. A task goes through:

```
PENDING → PLANNING → EXECUTING → COMPLETED
                                      │
                   or ── FAILED ───── or ── CANCELLED
```

The agent's tool loop within `EXECUTING` may produce multiple experiments (one per model/approach), each following the experiment state machine above. The `log_experiment` tool is the boundary — once the agent calls it, the experiment is recorded with full provenance.

### 10.4 Why This Still Matters

Even though the state machine is simpler, it still prevents:

- **Lost experiments:** Every code execution that produces metrics is recorded
- **Unreproducible results:** Every experiment stores its code, stdout, stderr, and metrics
- **Unbounded execution:** Budget limits on iterations, cost, and time

---

## 11. Knowledge Memory

### 11.1 What Makes Dojo.ml Different

Most ML tools run experiments in isolation. Dojo.ml accumulates **generalizable ML knowledge** across tasks.

### 11.2 Knowledge Atom Structure

```json
{
  "id": "ka_01J7K9ABCDEF",
  "context": "tabular classification with high-cardinality categorical features",
  "claim": "XGBoost outperforms linear models by 8-15% on recall",
  "action": "Start with tree ensembles for tabular classification tasks",
  "confidence": 0.78,
  "evidence_count": 11,
  "evidence_ids": ["exp_01J7...", "exp_01J8...", "..."],
  "task_names": ["boston_housing_comparison", "credit_scoring", "churn_prediction"],
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-15T14:30:00Z",
  "superseded_by": null
}
```

### 11.3 Knowledge Lifecycle

1. **Creation:** After a task completes, the LLM is asked to extract generalizable claims from the experiments.
2. **Reinforcement:** New tasks that confirm an existing atom increase its confidence.
3. **Contradiction:** New tasks that contradict an atom decrease its confidence.
4. **Supersession:** A new atom that better explains the evidence replaces the old one.
5. **Cross-task transfer:** Before starting a new task, the agent queries knowledge memory. Relevant atoms from *other* tasks inform the approach.

### 11.4 Relevance Scoring

- **Phase 1:** Keyword matching between query context and atom contexts.
- **Phase 2:** Embedding similarity (sentence-transformers) for semantic matching.

### 11.5 Cross-Task Transfer Example

```
Task 1: "Compare linear regression vs XGBoost on Boston housing"
  → Learns: "XGBoost significantly outperforms linear regression on tabular regression"
  → Confidence: 0.85

Task 2: "Find the best model for predicting customer churn"
  → Agent queries knowledge before starting
  → Finds relevant atom: tree ensembles outperform linear models on tabular data
  → Plans to start with XGBoost instead of logistic regression
  → Converges faster
```

### 11.6 Future: Recursive Agent Wrapper

In a future version, a meta-agent could read the knowledge memory and **generate new research prompts** for Dojo.ml:

```
Meta-agent reads knowledge → notices gap →
  generates prompt: "Investigate whether LightGBM outperforms XGBoost
  on small datasets (<1000 rows)" →
  submits to Dojo.ml → results feed back into knowledge
```

This recursive loop sits *above* Dojo.ml and is architecturally enabled by the prompt-driven interface, but not implemented in v1.

---

## 12. Agent System

### 12.1 Interaction Model: User Drives, Agent Executes

The v1 model is:

```
User → writes research prompt → Dojo.ml executes → returns results

NOT:
Agent → autonomously generates hypotheses → runs forever
```

This is a deliberate design choice:

1. **Trust:** Users know exactly what they asked for and can verify results against their intent.
2. **Scope control:** Each task has a clear completion condition (the prompt is answered).
3. **Future-proofing:** A recursive meta-agent can be layered on top later without changing the core system.

### 12.2 Phase 1 — SimpleAgent (Direct LLM Loop)

The Phase 1 agent uses the `anthropic` Python SDK's `tool_runner()` method.

#### Execution Flow for a Typical Task

User prompt: *"Compare linear regression vs XGBoost on the Boston housing dataset. Report RMSE and R²."*

```
Agent receives task
  │
  ├─ query_knowledge("tabular regression, housing prices")
  │   → Found: "tree ensembles outperform linear models" (confidence 0.7)
  │
  ├─ [PLANNING] Agent plans 4 steps:
  │   1. Load Boston housing dataset
  │   2. Train and evaluate linear regression
  │   3. Train and evaluate XGBoost
  │   4. Compare and summarize
  │
  ├─ install_packages(["scikit-learn", "xgboost", "pandas"])
  │   → Success
  │
  ├─ execute_code("""
  │     from sklearn.datasets import load_boston
  │     from sklearn.model_selection import cross_val_score
  │     from sklearn.linear_model import LinearRegression
  │     import numpy as np
  │     X, y = load_boston(return_X_y=True)
  │     lr = LinearRegression()
  │     rmse_scores = -cross_val_score(lr, X, y, scoring='neg_root_mean_squared_error', cv=5)
  │     r2_scores = cross_val_score(lr, X, y, scoring='r2', cv=5)
  │     print(f"RMSE: {rmse_scores.mean():.4f} (+/- {rmse_scores.std():.4f})")
  │     print(f"R²:   {r2_scores.mean():.4f} (+/- {r2_scores.std():.4f})")
  │   """)
  │   → stdout: "RMSE: 4.8432 (+/- 0.8721)\nR²: 0.7217 (+/- 0.0587)"
  │
  ├─ log_experiment(
  │     name="linear_regression",
  │     hypothesis="Linear regression as baseline",
  │     code="...",
  │     metrics={"rmse": 4.8432, "r2": 0.7217}
  │   )
  │
  ├─ execute_code("""
  │     from xgboost import XGBRegressor
  │     ...
  │   """)
  │   → stdout: "RMSE: 2.9103 (+/- 0.5412)\nR²: 0.8934 (+/- 0.0321)"
  │
  ├─ log_experiment(
  │     name="xgboost",
  │     hypothesis="XGBoost should outperform linear regression on this tabular dataset",
  │     code="...",
  │     metrics={"rmse": 2.9103, "r2": 0.8934}
  │   )
  │
  └─ [RESULT] Agent summarizes:
      "XGBoost (RMSE=2.91, R²=0.89) significantly outperforms
       Linear Regression (RMSE=4.84, R²=0.72) on Boston housing.
       XGBoost reduces RMSE by 40%."
```

Every step is logged as an `AgentThought` and visible in the UI.

### 12.3 Error Recovery

When code fails, the agent sees the error and tries to fix it:

```
execute_code("from sklearn.datasets import load_boston ...")
  → stderr: "ImportError: load_boston is deprecated in 1.2..."

Agent sees error → writes corrected code:
execute_code("from sklearn.datasets import fetch_openml ...")
  → Success
```

This self-correction is natural in the tool loop — the LLM sees the error in the tool result and adjusts.

---

## 13. Claude Agent SDK Integration Plan

### 13.1 Why Upgrade to Claude Agent SDK (Phase 2)

The Phase 1 `SimpleAgent` uses raw `anthropic` SDK. This works but has limitations:

- Manual tool execution loop management
- No built-in multi-agent orchestration
- No lifecycle hooks for governance
- No session management

The `claude-agent-sdk` package provides:

| Feature | Benefit for Dojo.ml |
|---|---|
| `AgentDefinition` | Specialized subagents (planner, coder, analyst) |
| `@tool` decorator | Clean tool definition with auto-generated schemas |
| `create_sdk_mcp_server()` | Bundle tools as MCP servers |
| Lifecycle hooks | Enforce budget limits and governance at the tool level |
| `max_turns`, `max_budget_usd` | Built-in budget controls |
| Session management | Persistent multi-turn conversations |

### 13.2 Phase 2 — ClaudeAgent Architecture

```python
from claude_agent_sdk import (
    AgentDefinition, ClaudeAgentOptions, ClaudeSDKClient,
    tool, create_sdk_mcp_server, HookMatcher,
)

# === Define tools as MCP tools ===

@tool("execute_code", "Execute Python code in a sandboxed environment", {
    "code": str,
    "timeout": int,
})
async def execute_code_tool(args):
    result = await sandbox.execute(args["code"], timeout=args.get("timeout", 300))
    return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code}

@tool("log_experiment", "Record an experiment with hypothesis, code, and metrics", {
    "name": str,
    "hypothesis": str,
    "code": str,
    "metrics": dict,
})
async def log_experiment_tool(args):
    exp = await engine.record_experiment(task_id=current_task.id, **args)
    return {"experiment_id": exp.id, "status": "recorded"}

@tool("query_knowledge", "Search knowledge memory for relevant past learnings", {
    "context": str,
    "limit": int,
})
async def query_knowledge_tool(args):
    atoms = await memory.get_relevant(args["context"], limit=args.get("limit", 5))
    return {"atoms": [a.to_dict() for a in atoms]}

# === Bundle into MCP server ===

dojo_tools = create_sdk_mcp_server(
    name="dojo-tools",
    version="0.1.0",
    tools=[execute_code_tool, log_experiment_tool, query_knowledge_tool, ...],
)
```

### 13.3 Multi-Agent Setup (Phase 2+)

```python
options = ClaudeAgentOptions(
    system_prompt="You are the Dojo.ml research coordinator.",
    max_turns=50,
    max_budget_usd=5.0,

    mcp_servers={"dojo": dojo_tools},
    allowed_tools=["mcp__dojo__*"],

    agents={
        "planner": AgentDefinition(
            description="Plans the research approach for a given prompt",
            prompt="Break down the research prompt into clear, executable steps.",
            model="sonnet",
        ),
        "coder": AgentDefinition(
            description="Writes and executes ML code in the sandbox",
            prompt="Write clean, well-documented Python code. Handle errors gracefully.",
            tools=["mcp__dojo__execute_code", "mcp__dojo__install_packages"],
            model="sonnet",
        ),
        "analyst": AgentDefinition(
            description="Analyzes results and extracts knowledge",
            prompt="Analyze experiment results. Extract generalizable ML knowledge.",
            tools=["mcp__dojo__query_knowledge", "mcp__dojo__log_experiment"],
            model="sonnet",
        ),
    },

    hooks={
        "PreToolUse": [
            HookMatcher(
                matcher="mcp__dojo__execute_code",
                hooks=[budget_check_hook],  # enforce execution time/cost limits
            ),
        ],
    },
)
```

### 13.4 Migration Path: SimpleAgent → ClaudeAgent

1. Both implement the same `Agent` Protocol.
2. Configuration selects the implementation:
   ```yaml
   agent:
     engine: simple    # Phase 1
     # engine: claude  # Phase 2
   ```
3. No changes to `TaskManager`, `ExperimentEngine`, `KnowledgeMemory`, or any other module.

---

## 14. API Specification

### 14.1 Task API

| Method | Path | Description |
|---|---|---|
| `POST` | `/tasks` | Submit a new research task (prompt + optional data) |
| `GET` | `/tasks` | List all tasks (filterable by status) |
| `GET` | `/tasks/{id}` | Get task detail (plan, experiments, results) |
| `GET` | `/tasks/{id}/stream` | SSE stream of task progress (thoughts, code, results) |
| `POST` | `/tasks/{id}/cancel` | Cancel a running task |

#### `POST /tasks` Request Body

```json
{
  "prompt": "Compare linear regression vs XGBoost on the Boston housing dataset",
  "data_files": ["path/to/data.csv"],
  "workspace": "path/to/project",
  "config": {
    "max_iterations": 30,
    "max_cost_usd": 5.0
  }
}
```

#### `GET /tasks/{id}` Response

```json
{
  "id": "task_01J7K9...",
  "prompt": "Compare linear regression vs XGBoost...",
  "status": "completed",
  "plan": {
    "steps": [
      {"description": "Load Boston housing dataset", "status": "completed"},
      {"description": "Train linear regression", "status": "completed"},
      {"description": "Train XGBoost", "status": "completed"},
      {"description": "Compare results", "status": "completed"}
    ]
  },
  "experiments": [
    {"id": "exp_01...", "name": "linear_regression", "metrics": {"rmse": 4.84, "r2": 0.72}},
    {"id": "exp_02...", "name": "xgboost", "metrics": {"rmse": 2.91, "r2": 0.89}}
  ],
  "result": {
    "summary": "XGBoost outperforms linear regression by 40% on RMSE...",
    "best_experiment_id": "exp_02...",
    "knowledge_atoms": ["ka_01..."]
  }
}
```

### 14.2 Experiment API

| Method | Path | Description |
|---|---|---|
| `GET` | `/experiments` | List all experiments (filterable by task, status) |
| `GET` | `/experiments/{id}` | Get experiment detail (code, metrics, stdout) |
| `GET` | `/experiments/{id}/code` | Get just the generated code |
| `GET` | `/experiments/{id}/artifacts` | Get experiment artifacts |

### 14.3 Knowledge API

| Method | Path | Description |
|---|---|---|
| `GET` | `/knowledge` | List all knowledge atoms |
| `GET` | `/knowledge/{id}` | Get knowledge atom detail |
| `GET` | `/knowledge/relevant?context=...` | Get relevant atoms for a context |
| `POST` | `/knowledge/{id}/feedback` | Provide human feedback on an atom |
| `DELETE` | `/knowledge/{id}` | Delete a knowledge atom |

### 14.4 Health API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Overall system health |
| `GET` | `/health/dependencies` | Health of each dependency (MLflow, sandbox, LLM) |

---

## 15. CLI Specification

### 15.1 Command Tree

```
dojo
├── start                              # Launch all services
│   ├── --port INT                     # FastAPI port (default: 8000)
│   ├── --ui-port INT                  # Streamlit port (default: 8501)
│   ├── --mlflow-port INT              # MLflow port (default: 5000)
│   ├── --no-ui                        # Skip launching UI
│   └── --no-mlflow                    # Skip launching MLflow server
│
├── stop                               # Stop all services
│
├── run PROMPT                         # Submit and watch a research task
│   ├── --data PATH                    # Attach data file(s) (repeatable)
│   ├── --workspace PATH              # Point to a project directory
│   ├── --max-cost FLOAT              # Max LLM spend for this task
│   ├── --max-iterations INT          # Max tool loop iterations
│   └── --no-watch                    # Submit without streaming output
│
├── task
│   ├── list                           # List all tasks
│   ├── show TASK_ID                   # Show task detail + results
│   ├── cancel TASK_ID                 # Cancel a running task
│   └── rerun TASK_ID                  # Re-run a previous task
│
├── experiment
│   ├── list                           # List experiments
│   ├── show EXPERIMENT_ID             # Show experiment detail (code, metrics)
│   ├── code EXPERIMENT_ID             # Print just the generated code
│   └── compare EXP1 EXP2             # Compare two experiments
│
├── knowledge
│   ├── list                           # List knowledge atoms
│   └── show ATOM_ID                   # Show atom detail
│
└── config
    ├── init                           # Create default config file
    ├── show                           # Display current config
    └── set KEY VALUE                  # Set config value
```

### 15.2 Example Session

```bash
# First time setup
$ pip install dojo
$ dojo config init
Created .dojo/config.yaml — add your LLM API key.

$ export ANTHROPIC_API_KEY=sk-ant-...

# Start services
$ dojo start
✓ MLflow tracking server    → http://localhost:5000
✓ FastAPI control plane      → http://localhost:8000
✓ Agent supervisor           → running
✓ Dojo.ml dashboard          → http://localhost:8501

# Run your first task (in another terminal)
$ dojo run "Load the iris dataset. Compare logistic regression, random forest, \
  and SVM. Report accuracy and F1 score."

🔍 Planning...
  Step 1: Load iris dataset
  Step 2: Train logistic regression
  Step 3: Train random forest
  Step 4: Train SVM
  Step 5: Compare results

📦 Installing packages: scikit-learn, pandas
✓ Packages installed

🧪 Running: logistic_regression
  → accuracy: 0.9667, f1: 0.9665
  ✓ Experiment logged

🧪 Running: random_forest
  → accuracy: 0.9733, f1: 0.9731
  ✓ Experiment logged

🧪 Running: svm
  → accuracy: 0.9800, f1: 0.9798
  ✓ Experiment logged

📊 Results:
┌─────────────────────┬──────────┬────────┐
│ Model               │ Accuracy │ F1     │
├─────────────────────┼──────────┼────────┤
│ SVM                 │ 0.9800   │ 0.9798 │
│ Random Forest       │ 0.9733   │ 0.9731 │
│ Logistic Regression │ 0.9667   │ 0.9665 │
└─────────────────────┴──────────┴────────┘

🏆 Best: SVM (accuracy: 0.9800)

💡 Knowledge learned:
  "SVM performs competitively with ensemble methods on small, well-separated datasets"

Task completed: task_01J7K9... (3 experiments, $0.12 LLM cost)
```

---

## 16. UI Dashboard

### 16.1 Framework

**Phase 1:** Streamlit — fastest to build, Python-only, good enough for observability.
**Phase 2 (optional):** React + Vite — richer UX, real-time WebSockets.

### 16.2 Pages

#### Tasks Page (Home)

- **New Task input** — text area for research prompt, file upload for data, submit button
- **Task list** — recent tasks with status, prompt preview, experiment count, best metric
- **Task detail** — full view:
  - The original prompt
  - Agent's plan (steps with status indicators)
  - Agent thoughts (reasoning at each step, streaming)
  - Generated code (syntax-highlighted, copy-paste ready)
  - Results summary
  - Knowledge atoms created

#### Experiments Page

- **Experiment list** — filterable table: task, name, status, metrics, date
- **Experiment detail** — full view:
  - Hypothesis
  - Generated code (syntax-highlighted)
  - Execution output (stdout/stderr)
  - Metrics
  - Artifacts (downloadable)
- **Experiment comparison** — side-by-side metric comparison with charts

#### Knowledge Page

- **Atom list** — all knowledge atoms, sortable by confidence, evidence count, recency
- **Atom detail** — full atom with all linked experiments and tasks
- **Cross-task view** — which atoms span multiple tasks
- **Feedback interface** — mark atoms as useful, incorrect, or needs review

#### Results Page

- **Best results per task** — quick overview
- **Performance over time** — how results improve across related tasks
- **Model comparison charts** — bar charts, radar plots for multi-metric comparison

### 16.3 UI → Backend Communication

```python
class Dojo.mlClient:
    """Typed HTTP client for the Dojo.ml API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self._client = httpx.AsyncClient(base_url=base_url)

    async def create_task(self, prompt: str, **kwargs) -> dict: ...
    async def stream_task(self, task_id: str) -> AsyncIterator[dict]: ...
    async def list_tasks(self, **filters) -> list[dict]: ...
    async def get_task(self, task_id: str) -> dict: ...
    async def list_experiments(self, **filters) -> list[dict]: ...
    async def get_experiment(self, exp_id: str) -> dict: ...
    async def list_knowledge(self) -> list[dict]: ...
```

---

## 17. Configuration

### 17.1 Configuration File

Location: `.dojo/config.yaml` (in the working directory)

```yaml
# .dojo/config.yaml

# LLM provider
llm:
  provider: anthropic                # anthropic | openai
  model: claude-sonnet-4-20250514
  api_key: ${ANTHROPIC_API_KEY}      # Env var substitution
  max_tokens: 16384
  temperature: 0.0

# Agent defaults
agent:
  engine: simple                     # simple | claude (Phase 2)
  max_iterations: 30                 # Max tool loop iterations per task
  max_cost_usd: 5.0                  # Max LLM spend per task
  max_execution_time: 600            # Max sandbox execution per code block (seconds)

# Sandbox
sandbox:
  backend: local                     # local | docker | modal
  work_dir: .dojo/sandboxes       # When backend=local
  # image: python:3.11-slim         # When backend=docker
  # modal_token: ${MODAL_TOKEN}     # When backend=modal

# Storage backend
storage:
  backend: filesystem                # filesystem | postgres
  path: .dojo/data                # When backend=filesystem
  # database_url: postgresql://...   # When backend=postgres

# Tracking (MLflow)
tracking:
  backend: mlflow                    # mlflow | file
  backend_store_uri: file:./mlruns
  artifact_root: ./mlruns/artifacts
  port: 5000

# API server
api:
  host: 0.0.0.0
  port: 8000

# UI server
ui:
  port: 8501
```

### 17.2 Configuration Loading Priority

1. CLI flags (`dojo run --max-cost 10.0`)
2. Environment variables (`DOJO_LLM__PROVIDER=anthropic`)
3. `.dojo/config.yaml` in working directory
4. `~/.dojo/config.yaml` (global defaults)
5. Built-in defaults (`config/defaults.py`)

### 17.3 Pydantic Settings

```python
from pydantic_settings import BaseSettings

class LLMSettings(BaseSettings):
    provider: Literal["anthropic", "openai"] = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    api_key: str = ""
    max_tokens: int = 16384
    temperature: float = 0.0

class SandboxSettings(BaseSettings):
    backend: Literal["local", "docker", "modal"] = "local"
    work_dir: str = ".dojo/sandboxes"
    memory_mb: int = 4096
    max_execution_time: int = 600

class Settings(BaseSettings):
    llm: LLMSettings = LLMSettings()
    agent: AgentSettings = AgentSettings()
    sandbox: SandboxSettings = SandboxSettings()
    storage: StorageSettings = StorageSettings()
    tracking: TrackingSettings = TrackingSettings()
    api: APISettings = APISettings()
    ui: UISettings = UISettings()

    model_config = SettingsConfigDict(
        env_prefix="DOJO_",
        env_nested_delimiter="__",
        yaml_file=".dojo/config.yaml",
    )
```

---

## 18. Phased Implementation Roadmap

### Phase 1 — Foundation (Weeks 1–4)

**Goal:** A working end-to-end loop: user submits a research prompt → agent writes code → executes in sandbox → returns results with logged experiments and knowledge atoms.

| Week | Deliverable |
|---|---|
| **1** | Project scaffolding, `pyproject.toml`, CLI skeleton (`dojo start`, `dojo run`), configuration loading (Pydantic Settings + YAML), domain models (Task, Experiment, KnowledgeAtom, AgentThought) |
| **2** | LocalSandbox (subprocess execution), ExperimentEngine (record experiments), FileSystemStorage (JSON-based repos for tasks, experiments, knowledge, agents) |
| **3** | SimpleAgent (Anthropic `tool_runner`), agent tools (`execute_code`, `install_packages`, `log_experiment`, `query_knowledge`), AgentSupervisor, TaskManager |
| **4** | KnowledgeMemory + KnowledgeSynthesizer, MLflow tracking connector, FastAPI API (tasks, experiments, knowledge), Streamlit UI (basic), end-to-end test with a real prompt |

**Phase 1 Tech Stack:**

| Component | Choice |
|---|---|
| LLM | Anthropic Claude via `anthropic` SDK |
| Sandbox | Local subprocess (`LocalSandbox`) |
| Storage | JSON files in `.dojo/data/` |
| Tracking | MLflow with file backend |
| UI | Streamlit |
| CLI | Typer |
| API | FastAPI + uvicorn |

**Phase 1 delivers:**

- `pip install dojo && dojo start` works
- `dojo run "Compare models on iris dataset"` produces results
- Experiments logged with code, metrics, stdout
- Knowledge atoms accumulate
- UI shows task progress, experiments, knowledge

### Phase 2 — Scale & Intelligence (Weeks 5–8)

**Goal:** Docker sandbox, Postgres storage, Claude Agent SDK with multi-agent orchestration, cross-task knowledge transfer.

| Week | Deliverable |
|---|---|
| **5** | DockerSandbox (container isolation), Postgres storage (SQLAlchemy + Alembic), MLflow with Postgres |
| **6** | ClaudeAgent (Claude Agent SDK), multi-agent setup (planner/coder/analyst subagents), lifecycle hooks |
| **7** | Cross-task knowledge transfer, embedding-based relevance scoring, multiple concurrent tasks |
| **8** | Enhanced UI (experiment comparison charts, knowledge graph, code diffs), OpenAI LLM connector |

**Phase 2 adds:**

| Component | Upgrade |
|---|---|
| Agent | Claude Agent SDK with subagents |
| Sandbox | Docker container isolation |
| Storage | PostgreSQL |
| Tracking | MLflow with Postgres |
| Knowledge | Embedding-based relevance |
| LLM | + OpenAI support |

### Phase 3 — Production (Weeks 9–12)

**Goal:** Cloud compute, hardening, deployment-ready.

| Week | Deliverable |
|---|---|
| **9** | ModalSandbox (serverless, GPU support), S3 artifact storage |
| **10** | Docker + docker-compose deployment, task queuing (for multiple concurrent tasks) |
| **11** | Authentication, rate limiting, SSE streaming for real-time UI updates |
| **12** | Documentation, example prompts, performance benchmarks, polish |

### What to ABSOLUTELY DEFER

| Temptation | Why Defer |
|---|---|
| Autonomous hypothesis generation | User drives in v1. Recursive meta-agent is a future layer. |
| Kubernetes sandbox | Docker + Modal covers 95% of use cases |
| Custom deep learning training loops | Agent writes the code — it can use any framework |
| Multi-tenant SaaS | Single-user local is the right starting point |
| Real-time streaming UI | Streamlit polling is fine for Phase 1 |
| Embedding-based knowledge search | Keyword matching works for Phase 1 |
| React UI | Streamlit is "good enough" for Phase 1 |

---

## 19. Success Criteria

### 19.1 Technical Criteria

| # | Criterion | Measurable |
|---|---|---|
| 1 | `pip install dojo && dojo start` launches all services within 30 seconds | ✅ |
| 2 | `dojo run "..."` produces experiment results for any standard ML prompt | ✅ |
| 3 | Zero integration code — user only writes a prompt | ✅ |
| 4 | Swapping sandbox/storage/tracking requires only config change, zero code changes | ✅ |
| 5 | All experiments include generated code — fully reproducible | ✅ |
| 6 | Knowledge atoms are human-readable and auditable | ✅ |

### 19.2 Behavioral Criteria

| Timeframe | Expected Behavior |
|---|---|
| **Within minutes** | User submits first prompt, gets results |
| **Within hours** | Multiple tasks completed, knowledge accumulating |
| **Within days** | Knowledge transfer visibly improves results on related tasks |
| **Within weeks** | System becomes a trusted ML assistant with growing expertise |

### 19.3 User Trust Criteria

The system is successful when:

> Users trust it to execute their ML research prompts correctly and efficiently.

This requires:

- Every piece of generated code is visible and inspectable
- Every experiment is logged with full provenance
- Every knowledge atom is transparent with evidence links
- Errors are handled gracefully with clear feedback
- The UI makes all of this accessible without reading logs

---

## 20. Appendix — Dependency Map & Tech Stack

### 20.1 Python Dependencies

```toml
[project]
name = "dojo"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    # CLI
    "typer>=0.12",
    "rich>=13.0",

    # API
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",

    # Configuration
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",

    # LLM
    "anthropic>=0.80",

    # Tracking
    "mlflow>=2.15",

    # Data
    "pandas>=2.0",

    # HTTP client
    "httpx>=0.27",

    # Logging
    "structlog>=24.0",

    # IDs
    "ulid-py>=2.0",

    # UI
    "streamlit>=1.35",
]

[project.optional-dependencies]
openai = ["openai>=1.30"]
postgres = ["sqlalchemy[asyncio]>=2.0", "asyncpg>=0.29", "alembic>=1.13"]
modal = ["modal>=0.60"]
docker = ["docker>=7.0"]
claude-agent = ["claude-agent-sdk>=0.1.40"]
s3 = ["boto3>=1.34"]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
    "pre-commit>=3.7",
]

[project.scripts]
dojo = "dojo.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 20.2 Module Dependency Graph

```
cli/main.py
  └── imports: config/settings, utils/process

cli/run.py
  └── imports: api client (HTTP to FastAPI)

api/app.py
  └── imports: api/deps, api/routers/*, api/middleware

api/deps.py
  └── imports: config/settings, connectors/registry
  └── creates: Container(sandbox, tracking, llm, storage)

api/routers/tasks.py
  └── imports: core/task/manager

api/routers/experiments.py
  └── imports: core/experiment/engine

api/routers/knowledge.py
  └── imports: core/knowledge/memory

core/task/manager.py
  └── imports: core/agent/supervisor
  └── imports: storage/base (TaskRepository Protocol)

core/agent/supervisor.py
  └── imports: core/agent/base (Agent Protocol)
  └── imports: core/experiment/engine
  └── imports: core/knowledge/memory

core/agent/simple.py
  └── imports: core/agent/base (Agent Protocol)
  └── imports: connectors/llm/base (LLMConnector Protocol)
  └── imports: connectors/sandbox/base (Sandbox Protocol)
  └── imports: core/agent/tools

core/experiment/engine.py
  └── imports: connectors/tracking/base (TrackingConnector Protocol)
  └── imports: storage/base (ExperimentRepository Protocol)

core/knowledge/memory.py
  └── imports: storage/base (KnowledgeRepository Protocol)

connectors/registry.py
  └── imports: config/settings
  └── conditionally imports concrete connector implementations
```

### 20.3 Key Design Decisions Summary

| Decision | Choice | Rationale |
|---|---|---|
| No ProblemAdapter | Agent writes all code | Zero integration cost; unlimited flexibility |
| Sandbox as core abstraction | `Sandbox` Protocol | Clean swap: local → Docker → Modal |
| Package layout | `src/` layout | Prevents import-from-cwd bugs |
| All connectors | Python `Protocol` | Structural subtyping, no inheritance coupling |
| Storage migration | Repository pattern + Alembic | Swap filesystem → Postgres without touching domain |
| Agent abstraction | `Agent` Protocol | Swap SimpleAgent → ClaudeAgent via config |
| User-driven hypothesis | User writes prompt, agent executes | Trust, scope control, future recursive wrapping |
| Configuration | `pydantic-settings` | Type-safe, env vars, YAML, validation |
| CLI framework | Typer | Type hints, auto-help, less boilerplate |
| API framework | FastAPI | Async, OpenAPI auto-docs, dependency injection |
| UI framework (Phase 1) | Streamlit | Fastest MVP, Python-only |
| Logging | structlog | JSON-structured, async-safe |
| Build system | hatchling | PEP 621, simple, fast |
| ID generation | ULID | Sortable, unique, URL-safe |
| Linting | ruff | Replaces flake8 + isort + black |

---

*This document is the single source of truth for Dojo.ml architecture and implementation. All implementation work should reference this PRD.*
