"""Prompt templates for each pipeline stage.

Every system prompt begins with a ``TASK: <name>`` line. Real LLMs treat it as
harmless context; the deterministic MockProvider uses it to pick a canned reply.
"""

from __future__ import annotations

from ..schemas import Analysis, ExecutionResult

# --- Analyze ---------------------------------------------------------------
ANALYZE_SYSTEM = """TASK: analyze
You are a research engineer who turns mathematics, computer science, and physics
papers into computational experiments.
Read the paper text and identify the single most important, empirically testable claim.
Respond with ONLY a JSON object (no prose, no code fences) of the form:
{
  "claim": "one precise sentence stating the testable claim",
  "why_it_matters": "one or two sentences on the significance",
  "simulation_plan": "a concrete plan: what to simulate, which quantities to measure, and what result would count as evidence for or against the claim"
}"""


def analyze_user(paper_text: str) -> str:
    return f"Paper text:\n\n{paper_text}\n\nReturn the JSON object described above."


# --- Generate --------------------------------------------------------------
GENERATE_SYSTEM = """TASK: generate
You write a single self-contained Python 3 script that runs a simulation to test
a scientific claim, then reports whether the results support it.

The paper may come from mathematics, computer science, or physics. Pick an
approach that fits the field:
- Physics: numerically integrate the equations of motion or field equations
  (scipy.integrate.solve_ivp / odeint), simulate dynamical, statistical-mechanics,
  electromagnetism, or quantum systems, use scipy.constants for physical constants,
  and where relevant verify conservation laws (energy, momentum, charge) as evidence.
- Math: Monte Carlo experiments, numerical convergence studies, or symbolic checks (sympy).
- CS: implement the algorithm and measure the claimed complexity, correctness, or behavior.

HARD REQUIREMENTS:
- Output ONLY the Python code, inside one ```python code block. No prose.
- Use ONLY the standard library plus: numpy, scipy, sympy, networkx, pandas,
  matplotlib, pillow, imageio. No other third-party imports.
- Do NOT access the network, environment variables, or files outside the current
  working directory. Do NOT call os.system, subprocess, eval, or exec.
- Set matplotlib to the non-interactive Agg backend and NEVER call plt.show().
- Seed all randomness (e.g. numpy.random.default_rng(0)) so runs are reproducible.
- You MUST save at least one figure into the current directory as figure_1.png
  (figure_2.png, ... for more); a run that saves no figure is a failure. For an
  animation, save a GIF (figure_N.gif) using matplotlib PillowWriter or imageio.
- Keep total runtime well under 45 seconds and memory modest.
- Print a concise human-readable log of what you measured.
- As the FINAL line, print exactly: RESULT_JSON: {...}
  where the JSON has keys: "metrics" (object of key numbers), "verdict"
  (one of "supported", "refuted", "inconclusive"), and "explanation" (short string).

OPTIONAL interactive 3D: if (and only if) the simulation has natural 3D structure
(a 3D trajectory or attractor, a point cloud, or a surface), ALSO write a file named
exactly scene.json in the current directory so the UI can render it interactively.
Schema:
{
  "type": "scene3d",
  "title": "short label",
  "objects": [
    {"kind": "points", "points": [[x,y,z], ...], "color": "#f2662f", "size": 0.02},
    {"kind": "line",   "points": [[x,y,z], ...], "color": "#22d3ee"}
  ]
}
A "points" object may instead give per-point "colors": [[r,g,b], ...] (0-1 floats).
For a trajectory, orbit, or geodesic, sample each curve DENSELY (roughly 200-500
points per line) so the path is smooth and its shape (bending, precession, spirals)
is clearly visible; do not store only endpoints. Keep total vertices across all
objects under 8000 so it stays smooth in a browser.
This is optional and additive; still save figure_1.png and print RESULT_JSON."""


def generate_user(analysis: Analysis, paper_text: str) -> str:
    return (
        f"Claim: {analysis.claim}\n\n"
        f"Why it matters: {analysis.why_it_matters}\n\n"
        f"Simulation plan: {analysis.simulation_plan}\n\n"
        f"Relevant paper text:\n{paper_text[:6000]}\n\n"
        "Write the Python script now."
    )


# --- Repair ----------------------------------------------------------------
REPAIR_SYSTEM = """TASK: repair
The previous Python script failed to run. Fix it. Keep the same goal and the same
output contract (figures saved as figure_*.png/.gif and a final RESULT_JSON line).
Output ONLY the corrected Python code inside one ```python code block. No prose."""


def repair_user(code: str, stderr: str) -> str:
    return (
        f"Here is the script that failed:\n\n```python\n{code}\n```\n\n"
        f"It exited with this error output:\n\n{stderr[-4000:]}\n\n"
        "Return the corrected full script."
    )


# --- Summarize -------------------------------------------------------------
SUMMARIZE_SYSTEM = """TASK: summarize
You explain, to a curious non-specialist, what a simulation showed about a paper's
claim. Be concrete and reference the measured numbers. 3-5 sentences, plain prose,
no code, no markdown headers."""


def summarize_user(analysis: Analysis, execution: ExecutionResult) -> str:
    metrics = (execution.result_json or {}).get("metrics", {})
    verdict = (execution.result_json or {}).get("verdict", "inconclusive")
    return (
        f"Claim tested: {analysis.claim}\n\n"
        f"Simulation plan: {analysis.simulation_plan}\n\n"
        f"Measured metrics: {metrics}\n"
        f"Self-reported verdict: {verdict}\n\n"
        f"Program output:\n{execution.stdout[-3000:]}\n\n"
        "Summarize what the simulation demonstrates about the claim."
    )
