"""End-to-end pipeline run using the offline mock provider and an in-memory store."""

from pathlib import Path

from app import store as store_mod
from app.config import get_settings
from app.pipeline import tasks
from app.schemas import JobRecord, JobStatus


def test_pipeline_end_to_end_with_mock(monkeypatch):
    settings = get_settings()
    jobs: dict[str, JobRecord] = {}

    monkeypatch.setattr(store_mod, "get_job", lambda jid: jobs.get(jid))
    monkeypatch.setattr(store_mod, "save_job", lambda job: jobs.__setitem__(job.id, job))

    def _set_status(job, status):
        job.status = status
        jobs[job.id] = job
        return job

    monkeypatch.setattr(store_mod, "set_status", _set_status)

    uploads = Path(settings.uploads_dir)
    uploads.mkdir(parents=True, exist_ok=True)
    (uploads / "job1.txt").write_text("We claim that Monte Carlo estimation converges.")

    now = store_mod.now_iso()
    jobs["job1"] = JobRecord(
        id="job1",
        status=JobStatus.queued,
        source_kind="text",
        source_ref="job1.txt",
        title="test",
        created_at=now,
        updated_at=now,
    )

    outcome = tasks.run_pipeline.apply(args=["job1"]).get()
    final = jobs["job1"]

    assert outcome == "completed"
    assert final.status == JobStatus.completed
    assert final.analysis and final.analysis.claim
    assert final.code
    assert final.execution and final.execution.returncode == 0
    assert any(a.endswith(".gif") for a in final.execution.artifacts)
    assert final.execution.scene and final.execution.scene.endswith("scene.json")
    assert final.verdict == "supported"
    assert final.summary
