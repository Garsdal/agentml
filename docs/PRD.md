# AgentML — Product Requirements Document

**Project name:** AgentML
**Type:** Autonomous ML Research Framework
**Version:** 0.1 — Initial Architecture & Implementation Spec
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

Traditional ML platforms automate training pipelines. AgentML automates **scientific improvement**.

Instead of:

> Humans repeatedly designing experiments to improve models.

AgentML provides:

> A persistent autonomous ML researcher that runs experiments, learns generalizable lessons, and transfers knowledge across ML problems.

The system must:

- Work across **arbitrary ML use cases** (forecasting, fraud detection, planning, recommendation, etc.)
- Integrate with **existing data & model code** through a minimal adapter interface
- Remain **interpretable and observable** — users watch the agent think
- **Accumulate reusable knowledge** over time via structured knowledge atoms
- Be **fully swappable at every layer** — compute, storage, tracking, and LLM provider can all be replaced without touching domain logic

### What AgentML Ultimately Is

Not AutoML. Not MLOps. It is:

> A persistent machine learning research organization encoded in software.

You are no longer optimizing models. You are **optimizing the process that discovers models**.

---

## 2. Non-Goals

AgentML is **not**:

| Not This | Why |
|---|---|
| A replacement for feature stores | AgentML consumes features; it doesn't manage them |
| A new deep learning framework | It orchestrates existing frameworks (scikit-learn, XGBoost, PyTorch, etc.) |
| A hyperparameter tuner | It reasons about *what* to try, not grid-search parameters |
| A production inference service | It produces models; serving is out of scope |
| A data pipeline tool | It reads data through adapters; ETL is external |

It operates **above** those layers as a research orchestration and learning system.

---

## 3. Core Concepts

### 3.1 Scientific Loop

Every ML problem is treated as an experimental environment:

```
Hypothesis → Experiment → Evidence → Analysis → Learning → Improved Hypothesis
       ↑                                                          │
       └──────────────────────────────────────────────────────────┘
```

- The **LLM** performs reasoning (hypothesis generation, analysis, learning extraction).
- **AgentML** performs enforcement (state machine), execution (connectors), and memory (knowledge store).

### 3.2 Separation of Responsibilities

| Component | Responsibility | Swappable? |
|---|---|---|
| **Agent** | Reasoning and planning | Yes — simple loop → Claude Agent SDK |
| **Experiment Engine** | Governance & lifecycle (state machine) | No — core invariant |
| **Problem Adapter** | Domain integration (user-provided) | N/A — user implements |
| **Compute Connector** | Job execution | Yes — local → Modal → Ray → K8s |
| **Data Connector** | Dataset access | Yes — filesystem → S3 → Postgres |
| **Tracking Connector** | Metrics & artifacts | Yes — filesystem → MLflow (local) → MLflow (Postgres) |
| **Storage Backend** | Experiment/knowledge persistence | Yes — JSON files → Postgres |
| **LLM Connector** | LLM API calls | Yes — Anthropic → OpenAI → local vLLM |
| **Knowledge Memory** | Learning across problems | No — core invariant (storage backend swappable) |
| **UI** | Observability & control | Yes — Streamlit → React |

### 3.3 Design Principle: Protocol-Based Swappability

Every swappable component is defined as a Python `Protocol` (structural subtyping). Implementations are selected via configuration, not code changes. No inheritance hierarchies — if a class has the right methods, it satisfies the protocol.

```python
# Example — any class with these methods is a valid ComputeConnector
class ComputeConnector(Protocol):
    async def run_job(self, job_spec: JobSpec) -> JobResult: ...
    async def job_status(self, job_id: str) -> JobStatus: ...
    async def cancel_job(self, job_id: str) -> None: ...
    async def health_check(self) -> bool: ...
```

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User / Browser                           │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼────────────────────────────────────┐
│                     UI Dashboard (Streamlit)                     │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Agents  │  │ Experiments│  │  Memory  │  │   Models     │  │
│  └──────────┘  └────────────┘  └──────────┘  └──────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (internal)
┌────────────────────────────▼────────────────────────────────────┐
│                   FastAPI Control Plane                          │
│  ┌────────────┐  ┌────────────────┐  ┌───────────────────────┐  │
│  │ Agent API  │  │ Experiment API │  │   Knowledge API       │  │
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
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Compute  │  │   Data    │  │ Tracking │  │     LLM       │  │
│  │Connector │  │ Connector │  │Connector │  │  Connector    │  │
│  └──────────┘  └───────────┘  └──────────┘  └───────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Storage Backend (Repository)                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                │              │               │
    ┌─────▼─────┐   ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
    │  Local /   │   │ Files /   │  │  MLflow   │  │ Anthropic │
    │  Modal /   │   │  S3 /     │  │  Server   │  │ / OpenAI  │
    │  Ray       │   │ Postgres  │  │           │  │ / vLLM    │
    └───────────┘   └───────────┘  └───────────┘  └───────────┘
```

### 4.2 Process Model — `agentml start`

When the user runs `agentml start`, a single CLI command launches all services:

```
agentml start
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
pip install agentml
```

### Step 2 — Start the platform

```bash
agentml start
```

This launches all services. User sees:

```
✓ MLflow tracking server    → http://localhost:5000
✓ FastAPI control plane      → http://localhost:8000
✓ Agent supervisor           → running
✓ AgentML dashboard          → http://localhost:8501
```

### Step 3 — Add a Problem (the only integration point)

A team creates a **Problem Adapter** — the single file that connects their domain:

```python
# my_team_adapter.py
from agentml import ProblemAdapter

class FraudAdapter(ProblemAdapter):

    def describe_problem(self) -> dict:
        """Tell the agent what kind of ML problem this is."""
        return {
            "name": "fraud_detection",
            "target_type": "classification",
            "primary_metric": "recall_at_5_fpr",
            "description": "Detect fraudulent transactions while keeping FPR < 5%",
        }

    def list_features(self) -> list[dict]:
        """List available features with metadata."""
        return [
            {"name": "amount", "type": "numeric", "description": "Transaction amount in USD"},
            {"name": "merchant", "type": "categorical", "cardinality": "high"},
            {"name": "hour", "type": "numeric", "description": "Hour of day (0-23)"},
            {"name": "country", "type": "categorical", "cardinality": "medium"},
        ]

    def get_dataset(self, spec: dict) -> "pd.DataFrame":
        """Load data according to the experiment spec."""
        return load_transactions(spec)

    def train(self, train_spec: dict) -> dict:
        """Train a model. Return a result dict with model artifact path."""
        return train_fraud_model(train_spec)

    def evaluate(self, eval_spec: dict) -> dict:
        """Evaluate a trained model. Return metrics dict."""
        return evaluate_fraud_model(eval_spec)
```

Register via CLI:

```bash
agentml register-problem fraud ./my_team_adapter.py
```

**No LLM prompt writing required.** The adapter is pure Python — teams keep their existing training code.

### Step 4 — Connect an LLM

Create `.agentml/config.yaml`:

```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  api_key: ${ANTHROPIC_API_KEY}
```

Supported (phased):
- **Phase 1:** Anthropic (Claude) via `anthropic` SDK
- **Phase 2:** OpenAI (GPT-4.1), Azure OpenAI
- **Phase 3:** Local vLLM, Ollama

### Step 5 — Start an Agent

From the UI dashboard:

> Create Agent → Select Problem ("fraud") → Start Hypothesis Agent

Or via CLI:

```bash
agentml agent start --problem fraud
```

The agent immediately begins the scientific loop: generating hypotheses, designing experiments, executing them through the adapter, analyzing results, and storing knowledge.

---

## 6. Project Structure

```
agentml/
├── pyproject.toml                      # PEP 621 — single source of truth
├── README.md
├── LICENSE
├── CHANGELOG.md
├── Makefile                            # Dev shortcuts: make test, make lint, make run
├── PRD.md                              # This document
│
├── src/
│   └── agentml/                        # Importable package (src layout)
│       ├── __init__.py                 # Public API: ProblemAdapter, etc.
│       ├── _version.py                 # Package version
│       │
│       │── ─── CLI ──────────────────────────────────────────────
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py                 # Typer app — entry point
│       │   ├── start.py                # `agentml start` — launch all services
│       │   ├── agent.py                # `agentml agent start/stop/list`
│       │   ├── problem.py              # `agentml register-problem`
│       │   └── config.py               # `agentml config show/set`
│       │
│       │── ─── API ──────────────────────────────────────────────
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py                  # FastAPI app factory (create_app)
│       │   ├── deps.py                 # Dependency injection container
│       │   ├── middleware.py            # CORS, request logging, error handling
│       │   └── routers/
│       │       ├── __init__.py
│       │       ├── agents.py           # POST/GET /agents, /agents/{id}/start
│       │       ├── experiments.py      # CRUD + state transitions
│       │       ├── knowledge.py        # GET /knowledge, /knowledge/relevant
│       │       ├── problems.py         # GET /problems, problem metadata
│       │       └── health.py           # GET /health — readiness + dependency checks
│       │
│       │── ─── CORE ─────────────────────────────────────────────
│       ├── core/
│       │   ├── __init__.py
│       │   ├── agent/
│       │   │   ├── __init__.py
│       │   │   ├── supervisor.py       # AgentSupervisor — manages agent lifecycles
│       │   │   ├── base.py             # BaseAgent protocol / ABC
│       │   │   ├── simple.py           # SimpleAgent — Phase 1 (raw LLM loop)
│       │   │   ├── claude_agent.py     # ClaudeAgent — Phase 2 (Claude Agent SDK)
│       │   │   ├── reasoning.py        # Reasoning chain construction
│       │   │   ├── planning.py         # Experiment planning policy
│       │   │   └── tools.py            # Agent tools (design_experiment, analyze_results, etc.)
│       │   │
│       │   ├── experiment/
│       │   │   ├── __init__.py
│       │   │   ├── engine.py           # ExperimentEngine — orchestrates lifecycle
│       │   │   ├── state_machine.py    # StateMachine — transition enforcement
│       │   │   ├── validator.py        # Validation rules (leakage, duplicates, illegal metrics)
│       │   │   └── models.py           # Experiment, Hypothesis, ExperimentResult dataclasses
│       │   │
│       │   ├── knowledge/
│       │   │   ├── __init__.py
│       │   │   ├── memory.py           # KnowledgeMemory — query & retrieval
│       │   │   ├── synthesis.py        # KnowledgeSynthesizer — extract atoms from experiments
│       │   │   ├── models.py           # KnowledgeAtom, Evidence, Context dataclasses
│       │   │   └── relevance.py        # Relevance scoring for cross-domain transfer
│       │   │
│       │   ├── problem/
│       │   │   ├── __init__.py
│       │   │   ├── adapter.py          # ProblemAdapter ABC (user implements this)
│       │   │   ├── registry.py         # ProblemRegistry — loads and manages adapters
│       │   │   └── models.py           # ProblemDescription, FeatureSpec dataclasses
│       │   │
│       │   └── models.py               # Shared domain models (JobSpec, JobResult, etc.)
│       │
│       │── ─── CONNECTORS ───────────────────────────────────────
│       ├── connectors/
│       │   ├── __init__.py
│       │   ├── registry.py             # ConnectorRegistry — resolve by config
│       │   │
│       │   ├── compute/
│       │   │   ├── __init__.py
│       │   │   ├── base.py             # ComputeConnector Protocol
│       │   │   ├── local.py            # LocalCompute — subprocess execution
│       │   │   └── modal.py            # ModalCompute — Modal.com integration
│       │   │
│       │   ├── data/
│       │   │   ├── __init__.py
│       │   │   ├── base.py             # DataConnector Protocol
│       │   │   ├── filesystem.py       # FilesystemData — local files
│       │   │   └── s3.py               # S3Data — object storage
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
│       │   ├── base.py                 # Repository protocols (ExperimentRepo, KnowledgeRepo, etc.)
│       │   ├── filesystem.py           # JSON/YAML file-based storage
│       │   ├── postgres.py             # PostgreSQL via SQLAlchemy (Phase 2)
│       │   └── migrations/             # Alembic migrations (Phase 2)
│       │       ├── env.py
│       │       └── versions/
│       │
│       │── ─── CONFIG ───────────────────────────────────────────
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py             # Pydantic Settings — loads .agentml/config.yaml + env vars
│       │   └── defaults.py             # Default configuration values
│       │
│       │── ─── UTILS ────────────────────────────────────────────
│       └── utils/
│           ├── __init__.py
│           ├── logging.py              # Structured logging (structlog)
│           ├── serialization.py        # JSON/YAML/datetime serializers
│           ├── process.py              # Process management for `agentml start`
│           └── ids.py                  # ID generation (ULIDs or UUIDs)
│
│── ─── FRONTEND ─────────────────────────────────────────────────
├── frontend/
│   ├── app.py                          # Streamlit entry point (Phase 1)
│   ├── pages/
│   │   ├── agents.py                   # Agent management & monitoring
│   │   ├── experiments.py              # Experiment browser & detail views
│   │   ├── knowledge.py               # Knowledge atom explorer
│   │   └── models.py                  # Model comparison & best models
│   ├── components/
│   │   ├── experiment_card.py          # Reusable experiment display
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
│   │   │   └── test_agent_supervisor.py
│   │   ├── connectors/
│   │   │   ├── test_local_compute.py
│   │   │   ├── test_mlflow_tracker.py
│   │   │   └── test_anthropic_llm.py
│   │   └── storage/
│   │       ├── test_filesystem_storage.py
│   │       └── test_postgres_storage.py
│   ├── integration/
│   │   ├── test_api_agents.py
│   │   ├── test_api_experiments.py
│   │   ├── test_experiment_lifecycle.py
│   │   └── test_agent_with_adapter.py
│   └── e2e/
│       └── test_full_scientific_loop.py
│
│── ─── EXAMPLES ─────────────────────────────────────────────────
├── examples/
│   ├── fraud_adapter.py                # Fraud detection problem adapter
│   ├── forecasting_adapter.py          # Time-series forecasting adapter
│   └── titanic_adapter.py             # Simple classification demo
│
│── ─── DOCS ─────────────────────────────────────────────────────
└── docs/
    ├── getting-started.md
    ├── writing-adapters.md
    ├── architecture.md
    ├── knowledge-system.md
    └── deployment.md
```

### 6.1 Why `src/` Layout?

The `src/` layout prevents accidental imports from the working directory during development. When you run `python -c "import agentml"` from the repo root, it forces the installed package to be used — never the raw source directory. This avoids a class of subtle bugs in testing and packaging.

### 6.2 Why Separate `core/` from `connectors/`?

Core contains **domain logic** that should never change when you swap infrastructure. Connectors contain **infrastructure integration** that changes when you swap providers. The boundary is enforced by the rule: **Core imports only Protocol interfaces from connectors, never concrete classes.**

---

## 7. Module Specifications

### 7.1 CLI (`cli/`)

**Framework:** Typer (auto-generates `--help`, leverages type hints)

**Entry point** in `pyproject.toml`:

```toml
[project.scripts]
agentml = "agentml.cli.main:app"
```

**Commands:**

| Command | Module | Description |
|---|---|---|
| `agentml start` | `cli/start.py` | Launch all services (FastAPI, MLflow, Streamlit, Supervisor) |
| `agentml stop` | `cli/start.py` | Graceful shutdown of all services |
| `agentml agent start --problem <name>` | `cli/agent.py` | Start an agent on a registered problem |
| `agentml agent stop <agent_id>` | `cli/agent.py` | Stop a running agent |
| `agentml agent list` | `cli/agent.py` | List all agents and their status |
| `agentml register-problem <name> <path>` | `cli/problem.py` | Register a problem adapter |
| `agentml config show` | `cli/config.py` | Display current configuration |
| `agentml config set <key> <value>` | `cli/config.py` | Update configuration |

**`agentml start` behavior:**

```python
# Pseudocode for cli/start.py
def start():
    settings = load_settings()
    processes = []

    # 1. Start MLflow tracking server
    processes.append(launch_mlflow(
        backend_uri=settings.tracking.backend_uri,  # file:./mlruns or postgresql://...
        port=settings.tracking.port,                 # default 5000
    ))

    # 2. Start FastAPI control plane
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

    # Block until interrupted
    wait_for_interrupt()
```

### 7.2 API (`api/`)

**Framework:** FastAPI with async/await throughout.

**App factory pattern** (`api/app.py`):

```python
def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="AgentML", version=__version__)

    # Dependency injection — wire connectors based on settings
    container = build_container(settings)
    app.state.container = container

    # Register routers
    app.include_router(agents_router, prefix="/agents", tags=["agents"])
    app.include_router(experiments_router, prefix="/experiments", tags=["experiments"])
    app.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
    app.include_router(problems_router, prefix="/problems", tags=["problems"])
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

The container resolves concrete implementations from configuration. This is where swappability is wired:

```python
def build_container(settings: Settings) -> Container:
    """Build the dependency container from settings."""
    return Container(
        compute=resolve_compute_connector(settings.compute),       # local or modal
        data=resolve_data_connector(settings.data),                # filesystem or s3
        tracking=resolve_tracking_connector(settings.tracking),    # mlflow or file
        llm=resolve_llm_connector(settings.llm),                   # anthropic or openai
        storage=resolve_storage_backend(settings.storage),         # filesystem or postgres
    )
```

### 7.3 Core — Agent (`core/agent/`)

#### `supervisor.py` — AgentSupervisor

Manages the lifecycle of all running agents. Runs as an async background task within the FastAPI process.

```python
class AgentSupervisor:
    """Manages agent lifecycles. Starts, stops, and monitors agents."""

    def __init__(self, container: Container):
        self._agents: dict[str, RunningAgent] = {}
        self._container = container

    async def start_agent(self, problem_name: str, config: AgentConfig) -> str:
        """Start an agent on a registered problem. Returns agent_id."""

    async def stop_agent(self, agent_id: str) -> None:
        """Gracefully stop an agent."""

    async def get_agent_state(self, agent_id: str) -> AgentState:
        """Get current state including reasoning, planned experiments, etc."""

    async def list_agents(self) -> list[AgentSummary]:
        """List all agents with status."""
```

#### `base.py` — Agent Protocol

```python
class Agent(Protocol):
    """Protocol that all agent implementations must satisfy."""

    async def run_cycle(self, context: AgentContext) -> AgentAction:
        """Execute one cycle of the scientific loop.

        Given the current context (problem description, past experiments,
        relevant knowledge), decide what to do next.

        Returns an AgentAction:
        - DesignExperiment(hypothesis, plan)
        - AnalyzeExperiment(experiment_id)
        - SynthesizeKnowledge(experiment_ids)
        - Wait(reason)
        - Stop(reason)
        """
        ...

    async def analyze_results(self, experiment: Experiment, results: ExperimentResult) -> Analysis:
        """Interpret experiment results. Return structured analysis."""
        ...

    async def extract_knowledge(self, experiments: list[Experiment]) -> list[KnowledgeAtom]:
        """Extract generalizable knowledge from a set of experiments."""
        ...
```

#### `simple.py` — SimpleAgent (Phase 1)

Uses the `anthropic` Python SDK with `tool_runner()` for an agentic loop:

```python
class SimpleAgent:
    """Phase 1 agent: direct LLM calls with tool_runner loop."""

    def __init__(self, llm: LLMConnector, knowledge: KnowledgeMemory):
        self._llm = llm
        self._knowledge = knowledge

    async def run_cycle(self, context: AgentContext) -> AgentAction:
        # 1. Build prompt with problem description, past experiments, relevant knowledge
        prompt = self._build_prompt(context)

        # 2. Call LLM with tools
        response = await self._llm.chat(
            messages=[{"role": "user", "content": prompt}],
            tools=AGENT_TOOLS,  # design_experiment, analyze_results, etc.
        )

        # 3. Parse response into AgentAction
        return self._parse_action(response)
```

#### `tools.py` — Agent Tools

Tools the agent can invoke during reasoning:

| Tool | Purpose |
|---|---|
| `design_experiment` | Create a new experiment with hypothesis and plan |
| `query_knowledge` | Search knowledge memory for relevant atoms |
| `analyze_results` | Request analysis of completed experiment |
| `compare_experiments` | Compare metrics across experiments |
| `list_features` | Get available features for the problem |
| `get_dataset_profile` | Get statistical profile of a dataset |

### 7.4 Core — Experiment (`core/experiment/`)

#### `models.py` — Domain Models

```python
@dataclass
class Hypothesis:
    id: str
    statement: str                    # "Tree ensembles will outperform linear models on high-cardinality features"
    rationale: str                    # Agent's reasoning
    source_knowledge: list[str]       # Knowledge atom IDs that informed this
    created_at: datetime

@dataclass
class ExperimentPlan:
    features: list[str]
    algorithm: str
    hyperparameters: dict
    dataset_spec: dict                # Passed to adapter.get_dataset()
    train_spec: dict                  # Passed to adapter.train()
    eval_spec: dict                   # Passed to adapter.evaluate()

@dataclass
class Experiment:
    id: str
    problem_name: str
    hypothesis: Hypothesis
    plan: ExperimentPlan
    state: ExperimentState            # DRAFT, APPROVED, RUNNING, etc.
    results: ExperimentResult | None
    analysis: Analysis | None
    created_at: datetime
    updated_at: datetime
    agent_id: str

@dataclass
class ExperimentResult:
    metrics: dict[str, float]         # {"recall_at_5_fpr": 0.82, "auc": 0.91}
    artifacts: dict[str, str]         # {"model": "path/to/model.pkl", "predictions": "..."}
    duration_seconds: float
    metadata: dict
```

#### `state_machine.py` — Experiment State Machine

Enforces valid transitions. Prevents agents from skipping steps or creating chaos.

```python
class ExperimentState(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    RUNNING = "running"
    EVALUATING = "evaluating"
    ANALYZED = "analyzed"
    LEARNED = "learned"
    ARCHIVED = "archived"
    FAILED = "failed"

VALID_TRANSITIONS: dict[ExperimentState, set[ExperimentState]] = {
    ExperimentState.DRAFT:      {ExperimentState.APPROVED, ExperimentState.ARCHIVED},
    ExperimentState.APPROVED:   {ExperimentState.RUNNING, ExperimentState.ARCHIVED},
    ExperimentState.RUNNING:    {ExperimentState.EVALUATING, ExperimentState.FAILED},
    ExperimentState.EVALUATING: {ExperimentState.ANALYZED, ExperimentState.FAILED},
    ExperimentState.ANALYZED:   {ExperimentState.LEARNED, ExperimentState.ARCHIVED},
    ExperimentState.LEARNED:    {ExperimentState.ARCHIVED},
    ExperimentState.FAILED:     {ExperimentState.ARCHIVED, ExperimentState.DRAFT},  # retry
    ExperimentState.ARCHIVED:   set(),  # terminal state
}

class ExperimentStateMachine:
    def transition(self, experiment: Experiment, target: ExperimentState) -> Experiment:
        if target not in VALID_TRANSITIONS[experiment.state]:
            raise InvalidTransitionError(experiment.state, target)
        experiment.state = target
        experiment.updated_at = datetime.utcnow()
        return experiment
```

#### `engine.py` — ExperimentEngine

Orchestrates the full experiment lifecycle:

```python
class ExperimentEngine:
    """Orchestrates experiment lifecycle through the state machine."""

    def __init__(
        self,
        state_machine: ExperimentStateMachine,
        validator: ExperimentValidator,
        compute: ComputeConnector,
        tracking: TrackingConnector,
        storage: ExperimentRepository,
        problem_registry: ProblemRegistry,
    ): ...

    async def create_experiment(self, spec: CreateExperimentSpec) -> Experiment:
        """Create a DRAFT experiment. Validates hypothesis & plan."""

    async def approve_experiment(self, experiment_id: str) -> Experiment:
        """Validate and approve. Checks for duplicates, leakage, illegal metrics."""

    async def run_experiment(self, experiment_id: str) -> Experiment:
        """Execute via compute connector + problem adapter. Track in MLflow."""

    async def evaluate_experiment(self, experiment_id: str) -> Experiment:
        """Run standardized evaluation through the adapter."""

    async def analyze_experiment(self, experiment_id: str, agent: Agent) -> Experiment:
        """Agent interprets evidence. Produces structured analysis."""

    async def learn_from_experiment(self, experiment_id: str, agent: Agent) -> list[KnowledgeAtom]:
        """Agent extracts generalizable knowledge atoms."""

    async def archive_experiment(self, experiment_id: str) -> Experiment:
        """Freeze for reproducibility."""
```

#### `validator.py` — Experiment Validation

```python
class ExperimentValidator:
    """Validates experiments before approval."""

    def validate(self, experiment: Experiment, history: list[Experiment]) -> ValidationResult:
        errors = []
        errors.extend(self._check_duplicate_hypothesis(experiment, history))
        errors.extend(self._check_feature_leakage(experiment))
        errors.extend(self._check_illegal_metrics(experiment))
        errors.extend(self._check_plan_completeness(experiment))
        return ValidationResult(valid=len(errors) == 0, errors=errors)
```

### 7.5 Core — Knowledge (`core/knowledge/`)

#### `models.py` — Knowledge Atom

```python
@dataclass
class KnowledgeAtom:
    id: str
    context: str                      # "classification with high-cardinality categorical features"
    claim: str                        # "gradient boosting outperforms linear models"
    action: str                       # "prioritize tree ensembles"
    confidence: float                 # 0.0 - 1.0
    evidence_count: int               # Number of experiments supporting this
    evidence_ids: list[str]           # Experiment IDs
    problem_names: list[str]          # Which problems contributed
    created_at: datetime
    updated_at: datetime
    superseded_by: str | None         # ID of atom that replaced this (if any)
```

#### `memory.py` — KnowledgeMemory

```python
class KnowledgeMemory:
    """Query and manage knowledge atoms."""

    def __init__(self, storage: KnowledgeRepository):
        self._storage = storage

    async def get_relevant(self, context: str, limit: int = 10) -> list[KnowledgeAtom]:
        """Find knowledge atoms relevant to the given context."""

    async def add_atom(self, atom: KnowledgeAtom) -> None:
        """Store a new knowledge atom."""

    async def update_confidence(self, atom_id: str, new_evidence: str) -> KnowledgeAtom:
        """Update confidence based on new supporting/contradicting evidence."""

    async def get_all(self) -> list[KnowledgeAtom]:
        """Return all knowledge atoms."""

    async def provide_feedback(self, atom_id: str, feedback: str) -> None:
        """Human feedback on a knowledge atom (useful, incorrect, etc.)."""
```

#### `synthesis.py` — KnowledgeSynthesizer

```python
class KnowledgeSynthesizer:
    """Extract knowledge atoms from experiments using the agent."""

    async def synthesize(
        self,
        experiments: list[Experiment],
        existing_knowledge: list[KnowledgeAtom],
        agent: Agent,
    ) -> list[KnowledgeAtom]:
        """Given completed experiments and existing knowledge,
        produce new or updated knowledge atoms.

        The agent determines:
        - What generalizable claim can be made
        - What context it applies to
        - Whether it confirms, contradicts, or extends existing atoms
        """
```

### 7.6 Core — Problem (`core/problem/`)

#### `adapter.py` — ProblemAdapter (User-Facing ABC)

```python
from abc import ABC, abstractmethod

class ProblemAdapter(ABC):
    """Abstract base class that users implement to integrate their ML problem.

    This is the ONLY class users need to implement. Everything else is handled
    by AgentML.
    """

    @abstractmethod
    def describe_problem(self) -> dict:
        """Return problem metadata.

        Required keys:
        - name: str — unique problem identifier
        - target_type: "classification" | "regression" | "forecasting" | "ranking"
        - primary_metric: str — main metric to optimize
        - description: str — human-readable description

        Optional keys:
        - secondary_metrics: list[str]
        - constraints: dict — e.g. {"max_fpr": 0.05}
        """
        ...

    @abstractmethod
    def list_features(self) -> list[dict]:
        """Return available features with metadata.

        Each feature dict should have:
        - name: str
        - type: "numeric" | "categorical" | "text" | "datetime"
        Optional:
        - description: str
        - cardinality: "low" | "medium" | "high" (for categorical)
        """
        ...

    @abstractmethod
    def get_dataset(self, spec: dict) -> "pd.DataFrame":
        """Load a dataset according to the experiment spec."""
        ...

    @abstractmethod
    def train(self, train_spec: dict) -> dict:
        """Train a model and return result dict.

        Must include:
        - model_path: str — path to saved model artifact
        Optional:
        - training_metrics: dict
        - metadata: dict
        """
        ...

    @abstractmethod
    def evaluate(self, eval_spec: dict) -> dict:
        """Evaluate a model and return metrics dict.

        Must include the primary_metric specified in describe_problem().
        """
        ...

    def deploy(self, deploy_spec: dict) -> dict:
        """Optional: deploy a model. Default: no-op."""
        return {"status": "not_implemented"}
```

#### `registry.py` — ProblemRegistry

```python
class ProblemRegistry:
    """Loads and manages problem adapters."""

    def __init__(self, storage: StorageBackend):
        self._adapters: dict[str, ProblemAdapter] = {}

    def register(self, name: str, adapter_path: str) -> None:
        """Dynamically load a ProblemAdapter from a Python file."""

    def get(self, name: str) -> ProblemAdapter:
        """Get a registered adapter by name."""

    def list_problems(self) -> list[dict]:
        """List all registered problems with their descriptions."""
```

---

## 8. Connector Interfaces

All connectors use Python `Protocol` classes for structural subtyping. No inheritance required — any class with matching methods is valid.

### 8.1 ComputeConnector

```python
from typing import Protocol
from agentml.core.models import JobSpec, JobResult, JobStatus

class ComputeConnector(Protocol):
    """Executes ML training/evaluation jobs."""

    async def run_job(self, job_spec: JobSpec) -> JobResult:
        """Submit and run a job. Blocks until completion."""
        ...

    async def run_job_async(self, job_spec: JobSpec) -> str:
        """Submit a job. Returns job_id immediately."""
        ...

    async def job_status(self, job_id: str) -> JobStatus:
        """Check status of an async job."""
        ...

    async def cancel_job(self, job_id: str) -> None:
        """Cancel a running job."""
        ...

    async def fetch_artifacts(self, job_id: str) -> dict[str, str]:
        """Download artifacts from a completed job."""
        ...

    async def health_check(self) -> bool:
        """Check if the compute backend is reachable."""
        ...
```

**Implementations:**

| Class | Module | Phase | Description |
|---|---|---|---|
| `LocalCompute` | `connectors/compute/local.py` | 1 | Runs jobs as local subprocesses |
| `ModalCompute` | `connectors/compute/modal.py` | 2 | Runs jobs on Modal.com |
| `RayCompute` | `connectors/compute/ray.py` | 3 | Runs jobs on a Ray cluster |

### 8.2 DataConnector

```python
class DataConnector(Protocol):
    """Provides access to datasets and data profiling."""

    async def load_dataset(self, spec: dict) -> "pd.DataFrame":
        """Load a dataset according to spec."""
        ...

    async def profile_dataset(self, spec: dict) -> dict:
        """Return statistical profile of a dataset."""
        ...

    async def store_predictions(self, predictions: "pd.DataFrame", path: str) -> str:
        """Store prediction results. Returns storage path."""
        ...
```

**Implementations:**

| Class | Module | Phase |
|---|---|---|
| `FilesystemData` | `connectors/data/filesystem.py` | 1 |
| `S3Data` | `connectors/data/s3.py` | 2 |

### 8.3 TrackingConnector

```python
class TrackingConnector(Protocol):
    """Tracks experiment metrics, parameters, and artifacts."""

    async def create_experiment(self, name: str) -> str:
        """Create a tracking experiment. Returns experiment_id."""
        ...

    async def start_run(self, experiment_id: str, run_name: str) -> str:
        """Start a tracking run. Returns run_id."""
        ...

    async def log_params(self, run_id: str, params: dict) -> None:
        """Log parameters."""
        ...

    async def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        """Log metrics."""
        ...

    async def log_artifact(self, run_id: str, local_path: str) -> None:
        """Log an artifact file."""
        ...

    async def end_run(self, run_id: str, status: str = "FINISHED") -> None:
        """End a tracking run."""
        ...

    async def get_best_run(self, experiment_id: str, metric: str) -> dict:
        """Get the best run by a given metric."""
        ...
```

**Implementations:**

| Class | Module | Phase | Backend |
|---|---|---|---|
| `MLflowTracker` | `connectors/tracking/mlflow_tracker.py` | 1 | MLflow with file store or Postgres |
| `FileTracker` | `connectors/tracking/file_tracker.py` | 1 | Plain JSON files (no MLflow dependency) |

### 8.4 LLMConnector

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

### 8.5 Storage Backend (Repository Pattern)

```python
class ExperimentRepository(Protocol):
    """Persistence for experiments."""

    async def save(self, experiment: Experiment) -> None: ...
    async def get(self, experiment_id: str) -> Experiment | None: ...
    async def list(self, filters: dict | None = None) -> list[Experiment]: ...
    async def update(self, experiment: Experiment) -> None: ...
    async def delete(self, experiment_id: str) -> None: ...

class KnowledgeRepository(Protocol):
    """Persistence for knowledge atoms."""

    async def save(self, atom: KnowledgeAtom) -> None: ...
    async def get(self, atom_id: str) -> KnowledgeAtom | None: ...
    async def list(self) -> list[KnowledgeAtom]: ...
    async def search(self, query: str, limit: int = 10) -> list[KnowledgeAtom]: ...
    async def update(self, atom: KnowledgeAtom) -> None: ...
    async def delete(self, atom_id: str) -> None: ...

class AgentStateRepository(Protocol):
    """Persistence for agent state (thoughts, plans, status)."""

    async def save_state(self, agent_id: str, state: AgentState) -> None: ...
    async def get_state(self, agent_id: str) -> AgentState | None: ...
    async def append_thought(self, agent_id: str, thought: AgentThought) -> None: ...
    async def get_thoughts(self, agent_id: str, limit: int = 50) -> list[AgentThought]: ...
```

**Implementations:**

| Class | Module | Phase | Backend |
|---|---|---|---|
| `FileSystemStorage` | `storage/filesystem.py` | 1 | JSON files in `.agentml/data/` |
| `PostgresStorage` | `storage/postgres.py` | 2 | PostgreSQL via SQLAlchemy async |

### 8.6 Phase 1 File Storage Layout

```
.agentml/
├── config.yaml                  # User configuration
└── data/
    ├── experiments/
    │   ├── exp_01J7K9...json    # One file per experiment
    │   └── exp_01J7KB...json
    ├── knowledge/
    │   └── atoms.json           # All knowledge atoms
    ├── agents/
    │   ├── agent_01J7K...json   # Agent state + thought history
    │   └── agent_01J7M...json
    ├── problems/
    │   └── registry.json        # Registered problem adapters
    └── models/
        └── ...                  # Model artifacts
```

---

## 9. Storage & Persistence

### 9.1 Strategy: Start Simple, Migrate Cleanly

| Phase | Storage | Backend | Migration Path |
|---|---|---|---|
| **1** | JSON files | Local filesystem | — |
| **2** | PostgreSQL | SQLAlchemy + Alembic | Alembic migration scripts |
| **3** | PostgreSQL + S3 | Postgres for metadata, S3 for artifacts | Add S3 connector |

The Repository Pattern makes this seamless. Core logic calls `repository.save(experiment)` — whether that writes a JSON file or inserts a Postgres row is invisible to the caller.

### 9.2 MLflow Storage

MLflow also has a swappable backend:

| Phase | MLflow Backend Store | MLflow Artifact Store |
|---|---|---|
| **1** | `file:./mlruns` | `./mlruns/artifacts/` |
| **2** | `postgresql://...` | S3 or local |

The `agentml start` command passes the backend URI to `mlflow server --backend-store-uri`.

---

## 10. Experiment State Machine

### 10.1 States

```
                     ┌──────────┐
                     │  DRAFT   │◄─── Agent creates experiment
                     └────┬─────┘
                          │ validate & approve
                     ┌────▼─────┐
                     │ APPROVED │
                     └────┬─────┘
                          │ execute via adapter + compute
                     ┌────▼─────┐
                     │ RUNNING  │
                     └────┬─────┘
                          │ run evaluation
                ┌─────────▼──────────┐
                │    EVALUATING      │
                └─────────┬──────────┘
                          │ agent interprets
                ┌─────────▼──────────┐
                │     ANALYZED       │
                └─────────┬──────────┘
                          │ extract knowledge
                ┌─────────▼──────────┐
                │      LEARNED       │
                └─────────┬──────────┘
                          │ freeze
                ┌─────────▼──────────┐
                │     ARCHIVED       │ ◄── terminal
                └────────────────────┘

  Any state except ARCHIVED can transition to FAILED.
  FAILED can transition back to DRAFT (retry) or ARCHIVED (abandon).
```

### 10.2 State Behaviors

| State | What Happens | Who Acts |
|---|---|---|
| **DRAFT** | Agent has created a hypothesis + experiment plan. Not yet validated. | Agent |
| **APPROVED** | Validator has confirmed: no duplicate hypothesis, no feature leakage, no illegal metrics, plan is complete. | Engine (automated) |
| **RUNNING** | Job submitted to compute connector. Adapter's `train()` method executing. | Engine → Compute → Adapter |
| **EVALUATING** | Training complete. Adapter's `evaluate()` method running. Metrics being collected. | Engine → Adapter |
| **ANALYZED** | Agent has interpreted the results. Structured analysis attached to experiment. | Agent |
| **LEARNED** | Knowledge atoms extracted and stored in memory. | Agent → KnowledgeSynthesizer |
| **ARCHIVED** | Frozen for reproducibility. Immutable. All artifacts stored. | Engine |
| **FAILED** | Something went wrong. Error details attached. Can retry (→ DRAFT) or abandon (→ ARCHIVED). | Engine |

### 10.3 Why This Matters

LLMs are exploratory but unsafe. Without the state machine:

- An agent could run the same experiment 50 times
- An agent could evaluate with metrics not relevant to the problem
- An agent could skip analysis and never learn
- Results would be unreproducible

The state machine guarantees **reproducibility, governance, and learning enforcement**.

---

## 11. Knowledge Memory

### 11.1 What Makes AgentML Different

Most AutoML systems store experiment results. AgentML stores **generalizable ML knowledge**.

The Knowledge Memory is the key differentiator. It transforms AgentML from "a thing that runs experiments" into "a thing that **learns how to do ML better**."

### 11.2 Knowledge Atom Structure

```json
{
  "id": "ka_01J7K9ABCDEF",
  "context": "classification with high-cardinality categorical features",
  "claim": "gradient boosting outperforms linear models by 8-15% on recall",
  "action": "prioritize tree ensembles (XGBoost, LightGBM) as first candidates",
  "confidence": 0.78,
  "evidence_count": 11,
  "evidence_ids": ["exp_01J7...", "exp_01J8...", "..."],
  "problem_names": ["fraud_detection", "churn_prediction"],
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-15T14:30:00Z",
  "superseded_by": null
}
```

### 11.3 Knowledge Lifecycle

1. **Creation:** After an experiment reaches ANALYZED, the agent is asked to extract generalizable claims.
2. **Reinforcement:** When new experiments confirm an existing atom, its confidence increases and evidence list grows.
3. **Contradiction:** When new experiments contradict an atom, its confidence decreases. If confidence drops below a threshold, the atom is marked for review.
4. **Supersession:** When a new atom better explains the evidence, the old atom's `superseded_by` field points to the replacement.
5. **Cross-domain transfer:** When starting work on a new problem, the agent queries knowledge memory with the new problem's context. Relevant atoms from *other* problems inform the initial hypothesis.

### 11.4 Relevance Scoring (Phase 1 — Simple)

In Phase 1, relevance is determined by **keyword matching** between the query context and atom contexts. This is sufficient for initial use.

In Phase 2, relevance scoring will use **embedding similarity** (e.g., sentence-transformers) for semantic matching across domains.

### 11.5 Cross-Domain Transfer Example

```
Problem A: Fraud Detection (classification, high-cardinality categoricals)
  → Learns: "tree ensembles dominate on high-cardinality categoricals"
  → Confidence: 0.85 (from 14 experiments)

Problem B: Churn Prediction (classification, high-cardinality categoricals)
  → Agent queries knowledge before first experiment
  → Finds relevant atom with confidence 0.85
  → First hypothesis: "try XGBoost" instead of "try logistic regression"
  → Converges faster because it starts from learned knowledge
```

---

## 12. Agent System

### 12.1 Phase 1 — SimpleAgent (Direct LLM Loop)

The Phase 1 agent uses the `anthropic` Python SDK's `tool_runner()` method. This provides an agentic loop where the LLM can call tools iteratively until it decides to stop.

#### Agent Cycle

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Cycle                           │
│                                                         │
│  1. Build context                                       │
│     - Problem description                               │
│     - Recent experiment history (last N)                │
│     - Relevant knowledge atoms                          │
│     - Current best model performance                    │
│                                                         │
│  2. Call LLM with tools                                 │
│     - Tools: design_experiment, query_knowledge,        │
│       compare_experiments, list_features,               │
│       get_dataset_profile                               │
│     - LLM reasons about what to try next                │
│     - LLM may call multiple tools before deciding       │
│                                                         │
│  3. Parse action                                        │
│     - DesignExperiment → create experiment in DRAFT     │
│     - Wait → sleep and retry later                      │
│     - Stop → agent halts                                │
│                                                         │
│  4. Execute action                                      │
│     - Experiment Engine handles lifecycle               │
│     - Agent waits for results                           │
│                                                         │
│  5. Analyze & learn                                     │
│     - Agent called again to interpret results           │
│     - Knowledge atoms extracted                         │
│     - Loop back to step 1                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### System Prompt (Condensed)

```
You are an ML research scientist. You are given a machine learning problem
and your goal is to iteratively improve model performance through systematic
experimentation.

You have access to tools that let you:
- Design experiments with specific hypotheses
- Query your knowledge memory for relevant past learnings
- Compare past experiment results
- Examine available features and data profiles

Rules:
1. Always state a clear hypothesis BEFORE designing an experiment
2. Never repeat an experiment that has already been tried
3. Build on your existing knowledge — check memory before planning
4. Analyze results carefully — a small improvement is still meaningful
5. Extract generalizable lessons, not just problem-specific notes
6. If stuck, try a fundamentally different approach, not minor tweaks
```

#### Budget & Safety Controls (Phase 1)

```python
@dataclass
class AgentConfig:
    max_experiments: int = 50           # Max experiments before stopping
    max_cost_usd: float = 10.0          # Max LLM spend per agent
    max_concurrent_experiments: int = 1  # Parallel experiments
    cycle_delay_seconds: int = 5         # Delay between cycles
    auto_approve: bool = True            # Auto-approve experiments (disable for manual review)
```

### 12.2 Agent Thought Logging

Every LLM interaction is logged as an `AgentThought`:

```python
@dataclass
class AgentThought:
    id: str
    agent_id: str
    timestamp: datetime
    type: str                 # "reasoning", "tool_call", "tool_result", "decision"
    content: str              # Raw text or structured data
    tokens_used: int
    cost_usd: float
```

These are persisted in the agent state repository and surfaced in the UI dashboard, enabling users to **watch the agent think**.

---

## 13. Claude Agent SDK Integration Plan

### 13.1 Why Upgrade to Claude Agent SDK

The Phase 1 `SimpleAgent` uses raw `anthropic` SDK calls. This works but has limitations:

- No built-in multi-agent orchestration
- Manual tool execution loop
- No lifecycle hooks
- No session management

The `claude-agent-sdk` package (from Anthropic) provides:

| Feature | Benefit for AgentML |
|---|---|
| `AgentDefinition` | Define specialized subagents (hypothesis agent, analysis agent, knowledge agent) |
| `@tool` decorator | Clean tool definition with auto-generated schemas |
| `create_sdk_mcp_server()` | Bundle tools as MCP servers |
| Lifecycle hooks (`PreToolUse`, `PostToolUse`, `Stop`) | Enforce experiment state machine at the tool level |
| `max_turns`, `max_budget_usd` | Built-in budget controls |
| Session management | Persistent multi-turn conversations |
| `ClaudeSDKClient` | Bidirectional stateful client for interactive agents |

### 13.2 Phase 2 — ClaudeAgent Architecture

```python
from claude_agent_sdk import (
    AgentDefinition, ClaudeAgentOptions, ClaudeSDKClient,
    tool, create_sdk_mcp_server, HookMatcher,
)

# === Define AgentML-specific tools as MCP tools ===

@tool("design_experiment", "Design a new ML experiment with a hypothesis and plan", {
    "hypothesis": str,
    "algorithm": str,
    "features": list,
    "hyperparameters": dict,
})
async def design_experiment(args):
    experiment = await engine.create_experiment(args)
    return {"experiment_id": experiment.id, "status": "draft"}

@tool("query_knowledge", "Search knowledge memory for relevant learnings", {
    "context": str,
    "limit": int,
})
async def query_knowledge(args):
    atoms = await memory.get_relevant(args["context"], limit=args.get("limit", 5))
    return {"atoms": [atom.to_dict() for atom in atoms]}

@tool("analyze_results", "Analyze the results of a completed experiment", {
    "experiment_id": str,
})
async def analyze_results(args):
    experiment = await storage.get(args["experiment_id"])
    return {"metrics": experiment.results.metrics, "plan": experiment.plan.to_dict()}

# === Bundle tools into MCP server ===

agentml_tools = create_sdk_mcp_server(
    name="agentml-tools",
    version="0.1.0",
    tools=[design_experiment, query_knowledge, analyze_results],
)
```

### 13.3 Multi-Agent Setup

```python
# === Define specialized subagents ===

options = ClaudeAgentOptions(
    system_prompt="You are the AgentML research supervisor.",
    max_turns=100,
    max_budget_usd=5.0,

    mcp_servers={"agentml": agentml_tools},
    allowed_tools=["mcp__agentml__*"],

    agents={
        "hypothesis_agent": AgentDefinition(
            description="Generates hypotheses for ML experiments based on problem context and knowledge",
            prompt="You generate scientific hypotheses for ML experiments. Be creative but grounded in evidence.",
            tools=["mcp__agentml__query_knowledge", "mcp__agentml__design_experiment"],
            model="sonnet",
        ),
        "analysis_agent": AgentDefinition(
            description="Analyzes experiment results and extracts insights",
            prompt="You analyze ML experiment results. Focus on statistical significance and actionable insights.",
            tools=["mcp__agentml__analyze_results", "mcp__agentml__query_knowledge"],
            model="sonnet",
        ),
        "knowledge_agent": AgentDefinition(
            description="Synthesizes generalizable knowledge from experiment history",
            prompt="You extract generalizable ML knowledge from experiments. Focus on claims that transfer across problems.",
            tools=["mcp__agentml__query_knowledge"],
            model="sonnet",
        ),
    },

    # === Lifecycle hooks for governance ===
    hooks={
        "PreToolUse": [
            HookMatcher(
                matcher="mcp__agentml__design_experiment",
                hooks=[validate_experiment_hook],  # enforce state machine
            ),
        ],
        "Stop": [
            HookMatcher(
                matcher="*",
                hooks=[log_agent_stop],
            ),
        ],
    },
)
```

### 13.4 Migration Path: SimpleAgent → ClaudeAgent

The `Agent` Protocol ensures this migration is seamless:

1. `SimpleAgent` and `ClaudeAgent` both implement the same `Agent` Protocol.
2. Configuration determines which implementation is used:
   ```yaml
   agent:
     engine: simple    # Phase 1
     # engine: claude  # Phase 2 — just change this line
   ```
3. The `AgentSupervisor` instantiates the correct agent class based on config.
4. No changes to `ExperimentEngine`, `KnowledgeMemory`, or any other core module.

---

## 14. API Specification

### 14.1 Experiment API

| Method | Path | Description |
|---|---|---|
| `POST` | `/experiments` | Create a new experiment (DRAFT) |
| `GET` | `/experiments` | List experiments (with filters: state, problem, agent) |
| `GET` | `/experiments/{id}` | Get experiment detail |
| `POST` | `/experiments/{id}/approve` | Validate and approve |
| `POST` | `/experiments/{id}/run` | Execute experiment |
| `POST` | `/experiments/{id}/evaluate` | Run evaluation |
| `POST` | `/experiments/{id}/analyze` | Agent analyzes results |
| `POST` | `/experiments/{id}/learn` | Extract knowledge atoms |
| `POST` | `/experiments/{id}/archive` | Archive experiment |
| `GET` | `/experiments/{id}/artifacts` | Get experiment artifacts |

### 14.2 Agent API

| Method | Path | Description |
|---|---|---|
| `POST` | `/agents` | Create and start an agent |
| `GET` | `/agents` | List all agents |
| `GET` | `/agents/{id}` | Get agent detail |
| `GET` | `/agents/{id}/state` | Get current agent state |
| `GET` | `/agents/{id}/thoughts` | Get agent thought history |
| `GET` | `/agents/{id}/experiments` | Get experiments created by this agent |
| `POST` | `/agents/{id}/stop` | Stop an agent |
| `DELETE` | `/agents/{id}` | Remove an agent |

### 14.3 Knowledge API

| Method | Path | Description |
|---|---|---|
| `GET` | `/knowledge` | List all knowledge atoms |
| `GET` | `/knowledge/{id}` | Get knowledge atom detail |
| `GET` | `/knowledge/relevant?context=...` | Get relevant atoms for a context |
| `POST` | `/knowledge/{id}/feedback` | Provide human feedback on an atom |
| `DELETE` | `/knowledge/{id}` | Delete a knowledge atom |

### 14.4 Problem API

| Method | Path | Description |
|---|---|---|
| `GET` | `/problems` | List registered problems |
| `GET` | `/problems/{name}` | Get problem description + features |
| `POST` | `/problems` | Register a new problem adapter |

### 14.5 Health API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Overall system health |
| `GET` | `/health/dependencies` | Health of each dependency (MLflow, compute, LLM) |

---

## 15. CLI Specification

### 15.1 Command Tree

```
agentml
├── start                    # Launch all services
│   ├── --port INT           # FastAPI port (default: 8000)
│   ├── --ui-port INT        # Streamlit port (default: 8501)
│   ├── --mlflow-port INT    # MLflow port (default: 5000)
│   ├── --no-ui              # Skip launching UI
│   └── --no-mlflow          # Skip launching MLflow server
│
├── stop                     # Stop all services
│
├── agent
│   ├── start                # Start an agent
│   │   ├── --problem TEXT   # Problem name (required)
│   │   ├── --max-experiments INT
│   │   └── --max-cost FLOAT
│   ├── stop AGENT_ID        # Stop an agent
│   ├── list                 # List agents
│   └── thoughts AGENT_ID   # Show agent thoughts
│
├── register-problem
│   ├── NAME                 # Problem name
│   └── PATH                 # Path to adapter .py file
│
├── experiment
│   ├── list                 # List experiments
│   ├── show EXPERIMENT_ID   # Show experiment detail
│   └── compare EXP1 EXP2   # Compare two experiments
│
├── knowledge
│   ├── list                 # List knowledge atoms
│   └── show ATOM_ID         # Show atom detail
│
└── config
    ├── show                 # Display current config
    ├── set KEY VALUE        # Set config value
    └── init                 # Create default config file
```

---

## 16. UI Dashboard

### 16.1 Framework

**Phase 1:** Streamlit — fastest to build, Python-only, good enough for observability.
**Phase 2 (optional):** React + Vite — richer UX, real-time websockets, if needed.

### 16.2 Pages

#### Agents Page

- **Agent list** — table with: name, problem, status, experiments run, current best metric
- **Agent detail** — live view of:
  - Current reasoning (streaming thoughts)
  - Next planned experiment
  - Experiment history
  - Token usage / cost

#### Experiments Page

- **Experiment list** — filterable table: state, problem, metric, date
- **Experiment detail** — full view:
  - Hypothesis (what the agent was testing)
  - Plan (features, algorithm, hyperparameters)
  - Results (metrics, artifacts)
  - Analysis (agent's interpretation)
  - Knowledge extracted
- **Experiment comparison** — side-by-side metric comparison with charts

#### Knowledge Page

- **Atom list** — all knowledge atoms, sortable by confidence, evidence count, recency
- **Atom detail** — full atom with all linked experiments
- **Cross-domain view** — which atoms span multiple problems
- **Feedback interface** — mark atoms as useful, incorrect, or needs review

#### Models Page

- **Best models** — per problem, ranked by primary metric
- **Model history** — performance over time chart
- **Model comparison** — across experiments

### 16.3 UI → Backend Communication

The Streamlit frontend communicates with the FastAPI backend via HTTP. The `frontend/api_client.py` module provides a typed client:

```python
class AgentMLClient:
    """HTTP client for the AgentML API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self._client = httpx.AsyncClient(base_url=base_url)

    async def list_agents(self) -> list[dict]: ...
    async def start_agent(self, problem: str, config: dict) -> dict: ...
    async def get_agent_thoughts(self, agent_id: str) -> list[dict]: ...
    async def list_experiments(self, **filters) -> list[dict]: ...
    async def get_experiment(self, exp_id: str) -> dict: ...
    async def list_knowledge(self) -> list[dict]: ...
    # etc.
```

---

## 17. Configuration

### 17.1 Configuration File

Location: `.agentml/config.yaml` (in the working directory)

```yaml
# .agentml/config.yaml

# LLM provider configuration
llm:
  provider: anthropic               # anthropic | openai
  model: claude-sonnet-4-20250514
  api_key: ${ANTHROPIC_API_KEY}     # Env var substitution
  max_tokens: 4096
  temperature: 0.0

# Agent defaults
agent:
  engine: simple                    # simple | claude (Phase 2)
  max_experiments: 50
  max_cost_usd: 10.0
  cycle_delay_seconds: 5
  auto_approve: true

# Compute backend
compute:
  backend: local                    # local | modal
  # modal_token: ${MODAL_TOKEN}    # When backend=modal

# Storage backend
storage:
  backend: filesystem               # filesystem | postgres
  path: .agentml/data               # When backend=filesystem
  # database_url: postgresql://...  # When backend=postgres

# Tracking (MLflow)
tracking:
  backend: mlflow                   # mlflow | file
  backend_store_uri: file:./mlruns  # file: or postgresql://
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

1. Environment variables (`AGENTML_LLM__PROVIDER=anthropic`)
2. `.agentml/config.yaml` in working directory
3. `~/.agentml/config.yaml` (global defaults)
4. Built-in defaults (`config/defaults.py`)

### 17.3 Pydantic Settings

```python
from pydantic_settings import BaseSettings

class LLMSettings(BaseSettings):
    provider: Literal["anthropic", "openai"] = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    api_key: str = ""
    max_tokens: int = 4096
    temperature: float = 0.0

class Settings(BaseSettings):
    llm: LLMSettings = LLMSettings()
    agent: AgentSettings = AgentSettings()
    compute: ComputeSettings = ComputeSettings()
    storage: StorageSettings = StorageSettings()
    tracking: TrackingSettings = TrackingSettings()
    api: APISettings = APISettings()
    ui: UISettings = UISettings()

    model_config = SettingsConfigDict(
        env_prefix="AGENTML_",
        env_nested_delimiter="__",
        yaml_file=".agentml/config.yaml",
    )
```

---

## 18. Phased Implementation Roadmap

### Phase 1 — Foundation (Weeks 1–4)

**Goal:** A working end-to-end loop: agent designs experiment → runs it → analyzes it → stores knowledge. One problem, one agent, all local.

| Week | Deliverable |
|---|---|
| **1** | Project scaffolding, `pyproject.toml`, CLI skeleton (`agentml start`), configuration loading, domain models (Experiment, KnowledgeAtom, AgentThought) |
| **2** | Experiment state machine, filesystem storage (JSON), ExperimentEngine, ProblemAdapter ABC, ProblemRegistry |
| **3** | SimpleAgent (Anthropic `tool_runner`), agent tools (design_experiment, query_knowledge), AgentSupervisor, LLMConnector (Anthropic), LocalCompute connector |
| **4** | KnowledgeMemory + KnowledgeSynthesizer, MLflow tracking connector, FastAPI API (experiments, agents, knowledge), Streamlit UI (basic), example Titanic adapter |

**Phase 1 Tech Stack:**

| Component | Choice |
|---|---|
| LLM | Anthropic Claude (raw `anthropic` SDK) |
| Compute | Local subprocess |
| Storage | JSON files in `.agentml/data/` |
| Tracking | MLflow with file backend |
| UI | Streamlit |
| CLI | Typer |
| API | FastAPI + uvicorn |

**Phase 1 delivers:**

- `pip install agentml && agentml start` works
- Register a problem, start an agent, watch it run experiments
- Knowledge atoms accumulate
- UI shows agent thoughts, experiments, knowledge

### Phase 2 — Scale & Intelligence (Weeks 5–8)

**Goal:** Multi-agent orchestration, Postgres storage, cross-domain transfer, richer UI.

| Week | Deliverable |
|---|---|
| **5** | Postgres storage backend (SQLAlchemy + Alembic migrations), MLflow with Postgres backend |
| **6** | ClaudeAgent implementation (Claude Agent SDK), multi-agent setup (hypothesis/analysis/knowledge subagents), lifecycle hooks |
| **7** | Cross-domain knowledge transfer, embedding-based relevance scoring, multiple concurrent agents on different problems |
| **8** | Enhanced UI (experiment comparison charts, knowledge graph, agent reasoning timeline), OpenAI LLM connector |

**Phase 2 adds:**

| Component | Upgrade |
|---|---|
| Agent | Claude Agent SDK with subagents |
| Storage | PostgreSQL |
| Tracking | MLflow with Postgres |
| Knowledge | Embedding-based relevance |
| LLM | + OpenAI support |

### Phase 3 — Production (Weeks 9–12)

**Goal:** Cloud compute, hardening, deployment-ready.

| Week | Deliverable |
|---|---|
| **9** | Modal compute connector, Ray compute connector |
| **10** | S3 artifact storage, Docker + docker-compose deployment |
| **11** | Authentication, rate limiting, multi-tenant support |
| **12** | Documentation, example adapters (fraud, forecasting, recommendation), performance benchmarks |

**Phase 3 adds:**

| Component | Upgrade |
|---|---|
| Compute | Modal, Ray |
| Artifacts | S3 |
| Deployment | Docker |
| Security | Auth, rate limiting |

### What to ABSOLUTELY DEFER

| Temptation | Why Defer |
|---|---|
| Kubernetes compute | Complexity explosion. Local + Modal covers 95% of cases. |
| Custom deep learning training loops | Users handle this in their adapters. Not AgentML's job. |
| Multi-tenant SaaS | Premature. Single-user local is the right starting point. |
| Real-time streaming UI | Streamlit polling is fine for Phase 1. WebSockets in Phase 2. |
| Embedding-based knowledge search | Keyword matching works for Phase 1. Embeddings in Phase 2. |
| Custom UI framework | Streamlit is "good enough." Only invest in React if Streamlit becomes a bottleneck. |

---

## 19. Success Criteria

### 19.1 Technical Criteria

| # | Criterion | Measurable |
|---|---|---|
| 1 | `pip install agentml && agentml start` launches all services within 30 seconds | ✅ |
| 2 | A new ML problem can be integrated in < 1 hour by implementing ProblemAdapter | ✅ |
| 3 | Agent improves model performance without human intervention over 10+ experiments | ✅ |
| 4 | Swapping compute/storage/tracking requires only config change, zero code changes | ✅ |
| 5 | All experiments are reproducible (full artifact + config preservation) | ✅ |
| 6 | Knowledge atoms are human-readable and auditable | ✅ |

### 19.2 Behavioral Criteria

| Timeframe | Expected Behavior |
|---|---|
| **Within hours** | Agent runs its first experiments, explores basic approaches |
| **Within days** | Agent converges to a strong model, knowledge atoms accumulate |
| **Within weeks** | Agent learns reusable ML strategies, tries creative approaches |
| **Within months** | Cross-domain knowledge transfer produces measurable speedup on new problems |

### 19.3 User Trust Criteria

The system is successful when:

> Users trust it enough to **watch** rather than manually tune.

This requires:

- Every decision the agent makes is observable (thought logs)
- Every experiment is auditable (state machine + archives)
- Every piece of knowledge is inspectable (atoms with evidence links)
- The UI makes all of this accessible without reading logs

---

## 20. Appendix — Dependency Map & Tech Stack

### 20.1 Python Dependencies

```toml
[project]
name = "agentml"
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

    # HTTP client (for UI → API)
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
agentml = "agentml.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 20.2 Module Dependency Graph

```
cli/main.py
  └── imports: config/settings, api/app, utils/process

api/app.py
  └── imports: api/deps, api/routers/*, api/middleware

api/deps.py
  └── imports: config/settings, connectors/registry
  └── creates: Container with all connectors + storage

api/routers/agents.py
  └── imports: core/agent/supervisor

api/routers/experiments.py
  └── imports: core/experiment/engine

api/routers/knowledge.py
  └── imports: core/knowledge/memory

core/agent/supervisor.py
  └── imports: core/agent/base (Protocol)
  └── imports: core/experiment/engine
  └── imports: core/knowledge/memory
  └── uses: AgentConfig from config

core/agent/simple.py
  └── imports: core/agent/base (Protocol)
  └── imports: connectors/llm/base (Protocol)
  └── imports: core/agent/tools

core/experiment/engine.py
  └── imports: core/experiment/state_machine
  └── imports: core/experiment/validator
  └── imports: connectors/compute/base (Protocol)
  └── imports: connectors/tracking/base (Protocol)
  └── imports: storage/base (Protocol)
  └── imports: core/problem/registry

core/knowledge/memory.py
  └── imports: storage/base (Protocol)
  └── imports: core/knowledge/models

connectors/registry.py
  └── imports: config/settings
  └── imports: connectors/compute/local, connectors/compute/modal (conditional)
  └── imports: connectors/llm/anthropic, connectors/llm/openai (conditional)
  └── imports: connectors/tracking/mlflow_tracker (conditional)
  └── imports: storage/filesystem, storage/postgres (conditional)
```

### 20.3 Key Design Decisions Summary

| Decision | Choice | Rationale |
|---|---|---|
| Package layout | `src/` layout | Prevents import-from-cwd bugs |
| Connector abstraction | Python `Protocol` | Structural subtyping, no inheritance coupling |
| Storage migration | Repository pattern + Alembic | Swap filesystem → Postgres without touching domain |
| Agent abstraction | `Agent` Protocol | Swap SimpleAgent → ClaudeAgent via config |
| Configuration | `pydantic-settings` | Type-safe, env vars, YAML, validation |
| CLI framework | Typer | Type hints, auto-help, less boilerplate |
| API framework | FastAPI | Async, OpenAPI auto-docs, dependency injection |
| UI framework (Phase 1) | Streamlit | Fastest MVP, Python-only |
| Logging | structlog | JSON-structured, async-safe |
| Build system | hatchling | PEP 621, simple, fast |
| ID generation | ULID | Sortable, unique, URL-safe |
| Linting | ruff | Replaces flake8 + isort + black, single fast tool |

---

*This document is the single source of truth for AgentML architecture and implementation. All implementation work should reference this PRD.*
