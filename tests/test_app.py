"""
tests/test_app.py — Tests that run in the CI pipeline.
Covers unit tests and integration-style endpoint tests.
"""

import pytest
import sys
import os

# Allow importing app from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, tasks as task_store


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Create a test client with a fresh task store for each test."""
    app.config["TESTING"] = True
    # Reset in-memory store before each test
    task_store.clear()
    task_store.extend([
        {"id": 1, "title": "Buy groceries", "done": False},
        {"id": 2, "title": "Write report",  "done": True},
    ])
    with app.test_client() as c:
        yield c


# ─── Health Check ──────────────────────────────────────────────────────────────

def test_health_endpoint(client):
    """Pipeline readiness check — if this fails, nothing else matters."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


# ─── GET /tasks ────────────────────────────────────────────────────────────────

def test_get_all_tasks_returns_200(client):
    res = client.get("/tasks")
    assert res.status_code == 200

def test_get_all_tasks_returns_list(client):
    res = client.get("/tasks")
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) == 2

def test_get_all_tasks_fields(client):
    task = client.get("/tasks").get_json()[0]
    assert "id" in task
    assert "title" in task
    assert "done" in task


# ─── GET /tasks/<id> ───────────────────────────────────────────────────────────

def test_get_existing_task(client):
    res = client.get("/tasks/1")
    assert res.status_code == 200
    assert res.get_json()["title"] == "Buy groceries"

def test_get_nonexistent_task_returns_404(client):
    res = client.get("/tasks/999")
    assert res.status_code == 404
    assert "error" in res.get_json()


# ─── POST /tasks ───────────────────────────────────────────────────────────────

def test_create_task_success(client):
    res = client.post("/tasks", json={"title": "Deploy app"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "Deploy app"
    assert data["done"] is False

def test_create_task_missing_title_returns_400(client):
    res = client.post("/tasks", json={"done": False})
    assert res.status_code == 400
    assert "error" in res.get_json()

def test_create_task_appears_in_list(client):
    client.post("/tasks", json={"title": "New task"})
    all_tasks = client.get("/tasks").get_json()
    titles = [t["title"] for t in all_tasks]
    assert "New task" in titles


# ─── PUT /tasks/<id> ───────────────────────────────────────────────────────────

def test_update_task_title(client):
    res = client.put("/tasks/1", json={"title": "Updated title"})
    assert res.status_code == 200
    assert res.get_json()["title"] == "Updated title"

def test_mark_task_done(client):
    res = client.put("/tasks/1", json={"done": True})
    assert res.status_code == 200
    assert res.get_json()["done"] is True

def test_update_nonexistent_task_returns_404(client):
    res = client.put("/tasks/999", json={"title": "Ghost"})
    assert res.status_code == 404


# ─── DELETE /tasks/<id> ────────────────────────────────────────────────────────

def test_delete_existing_task(client):
    res = client.delete("/tasks/1")
    assert res.status_code == 200

def test_deleted_task_not_in_list(client):
    client.delete("/tasks/1")
    ids = [t["id"] for t in client.get("/tasks").get_json()]
    assert 1 not in ids

def test_delete_nonexistent_task_returns_404(client):
    res = client.delete("/tasks/999")
    assert res.status_code == 404
