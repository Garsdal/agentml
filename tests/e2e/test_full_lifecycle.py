"""End-to-end test — the money test."""

from httpx import AsyncClient


async def test_health(client: AsyncClient):
    """GET /health should return ok."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_submit_task_and_get_results(client: AsyncClient):
    """POST /tasks with a prompt → GET /tasks/{id} → verify experiments + result."""
    # 1. POST /tasks
    resp = await client.post("/tasks", json={"prompt": "Compare models on iris"})
    assert resp.status_code == 200
    data = resp.json()
    task_id = data["id"]

    assert data["status"] == "completed"
    assert data["summary"] is not None
    assert len(data["experiments"]) >= 1
    assert data["experiments"][0]["metrics"] is not None

    # 2. GET /tasks/{id}
    resp = await client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    task = resp.json()
    assert task["status"] == "completed"
    assert task["id"] == task_id
    assert len(task["experiments"]) >= 1

    # 3. GET /tasks (list)
    resp = await client.get("/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) >= 1

    # 4. GET /experiments
    resp = await client.get("/experiments")
    assert resp.status_code == 200
    experiments = resp.json()
    assert len(experiments) >= 1

    exp_id = experiments[0]["id"]

    # 5. GET /experiments/{id}
    resp = await client.get(f"/experiments/{exp_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == exp_id

    # 6. GET /health
    resp = await client.get("/health")
    assert resp.json()["status"] == "ok"


async def test_task_not_found(client: AsyncClient):
    """GET /tasks/{nonexistent} should return 404."""
    resp = await client.get("/tasks/nonexistent-id")
    assert resp.status_code == 404


async def test_experiment_not_found(client: AsyncClient):
    """GET /experiments/{nonexistent} should return 404."""
    resp = await client.get("/experiments/nonexistent-id")
    assert resp.status_code == 404


async def test_knowledge_endpoints(client: AsyncClient):
    """Knowledge endpoints should work (empty for PoC)."""
    resp = await client.get("/knowledge")
    assert resp.status_code == 200
    assert resp.json() == []

    resp = await client.get("/knowledge/relevant", params={"query": "test"})
    assert resp.status_code == 200
    assert resp.json() == []
