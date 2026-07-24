"""Run a generated Python script under resource limits and a wall-clock timeout.

Isolation layers (defence in depth, best-effort for a local MVP):
  * a fresh per-run working directory; the script's cwd is that dir
  * ``python -I`` (isolated mode) + a stripped environment
  * POSIX rlimits on CPU time, address space, output file size, and process count
  * a wall-clock timeout that kills the subprocess

This still runs model-authored code with the worker's OS privileges. That is an
acceptable trade-off for a locally-run personal project; production deployments
should add a container-per-job / gVisor / seccomp layer and block network egress.
See the README's Security section.
"""

from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

from core.config import get_settings
from models.job import ExecutionResult

_settings = get_settings()

_ARTIFACT_GLOBS = ("*.png", "*.gif", "*.jpg", "*.jpeg", "*.svg", "*.mp4", "*.webp")
_MAX_CAPTURE = 8000  # chars of stdout/stderr to retain


def _apply_limits() -> None:
    """Run in the child, just before exec. POSIX only."""
    cpu = _settings.sandbox_timeout_seconds
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 2))

    # RLIMIT_AS is reliable on Linux (where the worker runs); macOS reserves huge
    # virtual ranges for numpy/BLAS and would spuriously OOM, so cap only on Linux.
    if sys.platform.startswith("linux"):
        mem = _settings.sandbox_max_memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))

    fsize = _settings.sandbox_max_output_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))

    nproc = _settings.sandbox_max_procs
    try:
        resource.setrlimit(resource.RLIMIT_NPROC, (nproc, nproc))
    except (ValueError, OSError):
        pass  # not enforceable on every platform; the CPU/time limits still apply

    os.setsid()  # own process group, so a timeout can reap descendants


def _parse_result_json(stdout: str) -> dict | None:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("RESULT_JSON:"):
            try:
                return json.loads(line[len("RESULT_JSON:") :].strip())
            except json.JSONDecodeError:
                return None
    return None


def run_code(job_id: str, code: str, attempt: int = 1) -> ExecutionResult:
    run_dir = Path(_settings.artifacts_dir) / job_id / f"run_{attempt}"
    run_dir.mkdir(parents=True, exist_ok=True)
    script = run_dir / "sim.py"
    script.write_text(code, encoding="utf-8")

    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": str(run_dir),
        "MPLBACKEND": "Agg",
        "MPLCONFIGDIR": str(run_dir / ".mpl"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "OPENBLAS_NUM_THREADS": "2",
        "OMP_NUM_THREADS": "2",
        "MKL_NUM_THREADS": "2",
    }

    preexec = _apply_limits if os.name == "posix" else None
    timeout = _settings.sandbox_timeout_seconds + 5
    timed_out = False
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "sim.py"],
            cwd=str(run_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            preexec_fn=preexec,
        )
        returncode, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = -9
        stdout = exc.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        stderr = (exc.stderr or "")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        stderr += f"\n[sandbox] killed after exceeding {_settings.sandbox_timeout_seconds}s"
    duration = time.time() - start

    artifacts: list[str] = []
    base = Path(_settings.artifacts_dir)
    for pattern in _ARTIFACT_GLOBS:
        for path in sorted(run_dir.glob(pattern)):
            artifacts.append(str(path.relative_to(base)))

    # An optional interactive 3D scene the script may have written.
    scene_file = run_dir / "scene.json"
    scene = str(scene_file.relative_to(base)) if scene_file.is_file() else None

    return ExecutionResult(
        returncode=returncode,
        stdout=stdout[-_MAX_CAPTURE:],
        stderr=stderr[-_MAX_CAPTURE:],
        duration_seconds=round(duration, 3),
        artifacts=artifacts,
        scene=scene,
        result_json=_parse_result_json(stdout),
        attempt=attempt,
        timed_out=timed_out,
    )
