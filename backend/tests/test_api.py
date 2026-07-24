"""API surface: submit creates a job, status endpoints behave."""

from fastapi.testclient import TestClient

from app import store as store_mod
from app.celery_app import celery_app
from app.main import app, rate_limit


def _client(monkeypatch) -> tuple[TestClient, dict]:
    saved: dict = {}
    app.dependency_overrides[rate_limit] = lambda: None
    monkeypatch.setattr(store_mod, "save_job", lambda job: saved.__setitem__(job.id, job))
    monkeypatch.setattr(store_mod, "get_job", lambda jid: saved.get(jid))
    monkeypatch.setattr(celery_app, "send_task", lambda *a, **k: None)
    return TestClient(app), saved


def test_health():
    client = TestClient(app)
    assert client.get("/api/health").json() == {"status": "ok"}


def test_submit_text_creates_job(monkeypatch):
    client, saved = _client(monkeypatch)
    resp = client.post("/api/papers", data={"text": "A testable claim about convergence."})
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    assert job_id in saved
    assert client.get(f"/api/jobs/{job_id}").status_code == 200
    app.dependency_overrides.clear()


def test_submit_requires_input(monkeypatch):
    client, _ = _client(monkeypatch)
    assert client.post("/api/papers", data={}).status_code == 400
    app.dependency_overrides.clear()


def test_missing_job_is_404(monkeypatch):
    monkeypatch.setattr(store_mod, "get_job", lambda jid: None)
    client = TestClient(app)
    assert client.get("/api/jobs/does-not-exist").status_code == 404
