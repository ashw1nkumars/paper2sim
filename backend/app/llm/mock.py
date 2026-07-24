"""Deterministic, offline LLM provider.

It keys off the ``TASK:`` line in each system prompt and returns a fixed, mutually
consistent set of responses built around one classic result: Monte Carlo
estimation of pi and the law of large numbers. The generated script always runs
successfully under the sandbox, so `docker compose up` yields a real, rendered
result with no API key required.
"""

from __future__ import annotations

_ANALYSIS_JSON = """{
  "claim": "Monte Carlo estimation converges to the true value of an integral, with the error shrinking at a rate proportional to 1/sqrt(N) as the number of samples N grows.",
  "why_it_matters": "This O(1/sqrt(N)) rate is the backbone of randomized numerical methods in physics, finance, and machine learning, and it holds regardless of the dimension of the problem.",
  "simulation_plan": "Estimate pi by sampling N random points in the unit square and measuring the fraction that land inside the quarter circle. Track the running estimate as N grows, compare it to the true value of pi, and fit the decay of the absolute error on a log-log scale to check that the exponent is close to -0.5."
}"""

# A self-contained script that only uses the allowlisted libraries and always
# produces figure_1.png, figure_2.gif, and a final RESULT_JSON line.
_SIMULATION_CODE = '''import json

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

rng = np.random.default_rng(0)
N = 20000
pts = rng.random((N, 2))
inside = (pts[:, 0] ** 2 + pts[:, 1] ** 2) <= 1.0
pi_estimate = 4.0 * inside.mean()

# --- Figure 1: the "dartboard" view -----------------------------------------
fig1, ax1 = plt.subplots(figsize=(6, 6))
sample, sin = pts[:4000], inside[:4000]
ax1.scatter(sample[sin, 0], sample[sin, 1], s=3, color="#2563eb", alpha=0.6, label="inside")
ax1.scatter(sample[~sin, 0], sample[~sin, 1], s=3, color="#ef4444", alpha=0.6, label="outside")
theta = np.linspace(0, np.pi / 2, 200)
ax1.plot(np.cos(theta), np.sin(theta), color="black", lw=2)
ax1.set_aspect("equal")
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.set_title("Monte Carlo estimate of pi (points in the quarter circle)")
ax1.legend(loc="upper right")
fig1.savefig("figure_1.png", dpi=120, bbox_inches="tight")
plt.close(fig1)

# --- Convergence data -------------------------------------------------------
ns = np.unique(np.logspace(1, np.log10(N), 60).astype(int))
running = np.array([4.0 * inside[:n].mean() for n in ns])
error = np.abs(running - np.pi)

# --- Figure 2: animated convergence to pi -----------------------------------
fig2, ax2 = plt.subplots(figsize=(7, 4.5))
ax2.axhline(np.pi, color="#16a34a", lw=2, ls="--", label="true pi")
ax2.set_xscale("log")
ax2.set_xlim(ns.min(), ns.max())
ax2.set_ylim(2.6, 3.7)
ax2.set_xlabel("number of samples (log scale)")
ax2.set_ylabel("estimate of pi")
ax2.set_title("Law of large numbers: the estimate converges to pi")
(line,) = ax2.plot([], [], color="#2563eb", lw=2, marker="o", ms=3, label="running estimate")
ax2.legend(loc="upper right")


def _update(i):
    line.set_data(ns[: i + 1], running[: i + 1])
    return (line,)


anim = FuncAnimation(fig2, _update, frames=len(ns), interval=80, blit=True)
anim.save("figure_2.gif", writer=PillowWriter(fps=12))
plt.close(fig2)

# --- Does the 1/sqrt(N) error law hold? -------------------------------------
mask = ns > 50
slope = float(np.polyfit(np.log(ns[mask]), np.log(error[mask] + 1e-12), 1)[0])
abs_error = float(abs(pi_estimate - np.pi))

print("Samples:", N)
print("Estimate of pi:", round(float(pi_estimate), 5))
print("Absolute error:", round(abs_error, 5))
print("Fitted error-decay exponent (theory = -0.5):", round(slope, 3))

verdict = "supported" if abs_error < 0.05 and abs(slope + 0.5) < 0.35 else "inconclusive"
print("RESULT_JSON:", json.dumps({
    "metrics": {
        "samples": int(N),
        "pi_estimate": round(float(pi_estimate), 5),
        "absolute_error": round(abs_error, 5),
        "error_decay_exponent": round(slope, 3),
    },
    "verdict": verdict,
    "explanation": "Monte Carlo integration converges to pi with error shrinking at the theoretical O(1/sqrt(N)) rate.",
}))
'''

_SUMMARY = (
    "The simulation reconstructs the paper's claim from scratch: it throws tens of "
    "thousands of random darts at a unit square and counts how many land inside the "
    "quarter circle. That fraction, scaled by four, estimates pi to within a few "
    "thousandths, and the animated convergence plot shows the running estimate homing "
    "in on the true value as more samples arrive. Fitting the shrinking error on a "
    "log-log scale recovers a slope near -0.5, exactly the O(1/sqrt(N)) rate the claim "
    "predicts. The evidence supports the claim."
)


class MockProvider:
    name = "mock"

    def complete(self, system: str, user: str) -> str:
        task = system.splitlines()[0].replace("TASK:", "").strip().lower() if system else ""
        if task == "analyze":
            return _ANALYSIS_JSON
        if task in ("generate", "repair"):
            return f"```python\n{_SIMULATION_CODE}```"
        if task == "summarize":
            return _SUMMARY
        return _SUMMARY
