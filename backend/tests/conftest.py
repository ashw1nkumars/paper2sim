"""Test configuration. Runs before any app module is imported so that Settings
(cached) pick up a writable temp data dir and the offline mock LLM provider."""

import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="paper2sim-test-"))
os.environ.setdefault("UPLOADS_DIR", str(_tmp / "uploads"))
os.environ.setdefault("ARTIFACTS_DIR", str(_tmp / "artifacts"))
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("SANDBOX_TIMEOUT_SECONDS", "30")
# A DB the app will never actually reach in tests (Redis calls are monkeypatched).
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

Path(os.environ["UPLOADS_DIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["ARTIFACTS_DIR"]).mkdir(parents=True, exist_ok=True)
