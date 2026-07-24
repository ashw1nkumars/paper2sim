"""The sandbox must run well-behaved code and contain misbehaving code."""

from app.sandbox import executor, run_code

_VALID = """
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.plot([0, 1, 2], [0, 1, 4])
plt.savefig("figure_1.png")
print('RESULT_JSON: {"metrics": {"x": 1}, "verdict": "supported", "explanation": "ok"}')
"""

_INFINITE = "while True:\n    pass\n"


def test_valid_script_produces_artifact_and_result():
    result = run_code("test-valid", _VALID, attempt=1)
    assert result.returncode == 0, result.stderr
    assert any(a.endswith("figure_1.png") for a in result.artifacts)
    assert result.result_json is not None
    assert result.result_json["verdict"] == "supported"


def test_infinite_loop_is_killed(monkeypatch):
    # Shrink the limit so the test is fast; CPU rlimit / wall timeout stops it.
    monkeypatch.setattr(executor._settings, "sandbox_timeout_seconds", 3)
    result = run_code("test-timeout", _INFINITE, attempt=1)
    assert result.returncode != 0
    assert result.result_json is None
