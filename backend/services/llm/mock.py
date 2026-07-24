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
# produces figure_1.png, figure_2.gif, scene.json (interactive 3D), and RESULT_JSON.
_SIMULATION_CODE = '''import json

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

rng = np.random.default_rng(0)
N = 40000
pts = rng.random((N, 3))
inside = (pts ** 2).sum(axis=1) <= 1.0
# The unit-cube octant (volume 1) contains the unit-sphere octant (volume pi/6).
pi_estimate = 6.0 * inside.mean()

# --- Interactive 3D scene: the Monte Carlo point cloud ----------------------
scene_pts = pts[:4000]
scene_inside = inside[:4000]
inside_rgb, outside_rgb = [0.949, 0.4, 0.184], [0.133, 0.827, 0.933]
colors = np.where(scene_inside[:, None], inside_rgb, outside_rgb)
scene = {
    "type": "scene3d",
    "title": "Monte Carlo points: inside vs outside the unit sphere",
    "objects": [
        {
            "kind": "points",
            "points": scene_pts.round(4).tolist(),
            "colors": colors.round(3).tolist(),
            "size": 0.02,
        }
    ],
}
with open("scene.json", "w") as fh:
    json.dump(scene, fh)

# --- Figure 1: 3D scatter (static) ------------------------------------------
fig1 = plt.figure(figsize=(6, 6))
ax1 = fig1.add_subplot(111, projection="3d")
smp, sin = pts[:3000], inside[:3000]
ax1.scatter(smp[sin, 0], smp[sin, 1], smp[sin, 2], s=4, color="#f2662f", alpha=0.5, label="inside")
ax1.scatter(smp[~sin, 0], smp[~sin, 1], smp[~sin, 2], s=4, color="#22d3ee", alpha=0.25, label="outside")
ax1.set_title("Monte Carlo estimate of pi (3D unit sphere)")
ax1.legend(loc="upper left")
fig1.savefig("figure_1.png", dpi=120, bbox_inches="tight")
plt.close(fig1)

# --- Convergence data -------------------------------------------------------
ns = np.unique(np.logspace(1, np.log10(N), 60).astype(int))
running = np.array([6.0 * inside[:n].mean() for n in ns])
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
    "explanation": "Monte Carlo integration in 3D converges to pi with error shrinking at the theoretical O(1/sqrt(N)) rate.",
}))
'''

_SUMMARY = (
    "The simulation reconstructs the paper's claim from scratch: it scatters tens of "
    "thousands of random points inside a unit cube and counts how many fall within the "
    "unit sphere. That fraction, scaled to the sphere's volume, estimates pi to within a "
    "few thousandths, and the animated convergence plot shows the running estimate homing "
    "in on the true value as more samples arrive. You can rotate and zoom the 3D point "
    "cloud to see the sphere emerge. Fitting the shrinking error on a log-log scale "
    "recovers a slope near -0.5, exactly the O(1/sqrt(N)) rate the claim predicts. The "
    "evidence supports the claim."
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
