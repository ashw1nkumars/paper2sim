import { useState } from "react";
import { artifactUrl, type Job, type JobStatus } from "../api";
import Scene3D from "./Scene3D";

const STAGES: { key: JobStatus; label: string }[] = [
  { key: "ingesting", label: "Ingest" },
  { key: "analyzing", label: "Analyze" },
  { key: "generating", label: "Generate" },
  { key: "executing", label: "Simulate" },
  { key: "summarizing", label: "Summarize" },
];

const ORDER: JobStatus[] = [
  "queued",
  "ingesting",
  "analyzing",
  "generating",
  "executing",
  "repairing",
  "summarizing",
  "completed",
];

function stageState(job: Job, stageKey: JobStatus): "done" | "active" | "todo" {
  if (job.status === "failed") {
    // Whatever stage was running when it failed is the "active" (errored) one.
    return job.status === stageKey ? "active" : "todo";
  }
  const current = job.status === "repairing" ? "executing" : job.status;
  const ci = ORDER.indexOf(current);
  const si = ORDER.indexOf(stageKey);
  if (job.status === "completed") return "done";
  if (si < ci) return "done";
  if (si === ci) return "active";
  return "todo";
}

function Collapsible({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="collapsible">
      <button className="collapsible-head" onClick={() => setOpen((o) => !o)}>
        {open ? "▾" : "▸"} {title}
      </button>
      {open && <div className="collapsible-body">{children}</div>}
    </div>
  );
}

export default function JobDetail({ job }: { job: Job | null }) {
  if (!job) {
    return (
      <div className="card detail empty">
        <p className="muted">Select a run on the left, or submit a paper.</p>
      </div>
    );
  }

  const running = !["completed", "failed"].includes(job.status);
  const artifacts = job.execution?.artifacts ?? [];

  return (
    <div className="card detail">
      <div className="detail-head">
        <h2>{job.title || job.id}</h2>
        <div className="pills">
          {job.llm_provider && <span className="pill provider">{job.llm_provider}</span>}
          {job.verdict && <span className={`pill verdict ${job.verdict}`}>{job.verdict}</span>}
          <span className={`badge ${job.status}`}>{job.status}</span>
        </div>
      </div>

      <div className="stepper">
        {STAGES.map((s) => {
          const st = stageState(job, s.key);
          return (
            <div key={s.key} className={`step ${st}`}>
              <span className="dot">{running && st === "active" ? "●" : st === "done" ? "✓" : ""}</span>
              <span className="step-label">{s.label}</span>
            </div>
          );
        })}
      </div>

      {job.error && <p className="error">{job.error}</p>}

      {job.analysis && (
        <section className="analysis">
          <h3>Claim</h3>
          <p className="claim">{job.analysis.claim}</p>
          {job.analysis.why_it_matters && (
            <>
              <h4>Why it matters</h4>
              <p>{job.analysis.why_it_matters}</p>
            </>
          )}
          {job.analysis.simulation_plan && (
            <>
              <h4>Simulation plan</h4>
              <p>{job.analysis.simulation_plan}</p>
            </>
          )}
        </section>
      )}

      {job.execution?.scene && (
        <section className="artifacts">
          <h3>Interactive 3D</h3>
          <Scene3D url={artifactUrl(job.execution.scene)} />
        </section>
      )}

      {artifacts.length > 0 && (
        <section className="artifacts">
          <h3>Simulation output</h3>
          <div className="gallery">
            {artifacts.map((a) => (
              <a key={a} href={artifactUrl(a)} target="_blank" rel="noreferrer">
                <img src={artifactUrl(a)} alt={a} loading="lazy" />
              </a>
            ))}
          </div>
        </section>
      )}

      {job.summary && (
        <section className="summary">
          <h3>Conclusion</h3>
          <p>{job.summary}</p>
        </section>
      )}

      {job.code && (
        <Collapsible title="Generated Python">
          <pre className="code">
            <code>{job.code}</code>
          </pre>
        </Collapsible>
      )}

      {job.execution?.stdout && (
        <Collapsible title="Program output (stdout)">
          <pre className="stdout">{job.execution.stdout}</pre>
        </Collapsible>
      )}

      {job.execution?.stderr && job.execution.returncode !== 0 && (
        <Collapsible title="Errors (stderr)">
          <pre className="stderr">{job.execution.stderr}</pre>
        </Collapsible>
      )}
    </div>
  );
}
