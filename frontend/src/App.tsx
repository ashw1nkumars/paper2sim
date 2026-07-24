import { useCallback, useEffect, useState } from "react";
import { getJob, listJobs, type Job } from "./api";
import JobDetail from "./components/JobDetail";
import JobList from "./components/JobList";
import SubmitForm from "./components/SubmitForm";

function Emblem() {
  return (
    <div className="emblem" aria-hidden="true">
      <span className="brk l">{"<"}</span>
      <div className="ring r1">
        <span className="dot" />
      </div>
      <div className="ring r2" />
      <div className="ring r3" />
      <div className="core">
        <span className="sym">∮</span>
      </div>
      <span className="brk r">{"/>"}</span>
    </div>
  );
}

export default function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  const refreshJobs = useCallback(async () => {
    try {
      setJobs(await listJobs());
    } catch {
      /* transient; next tick retries */
    }
  }, []);

  useEffect(() => {
    refreshJobs();
    const t = setInterval(refreshJobs, 3000);
    return () => clearInterval(t);
  }, [refreshJobs]);

  useEffect(() => {
    if (!selectedId) {
      setSelectedJob(null);
      return;
    }
    let active = true;
    async function tick() {
      try {
        const job = await getJob(selectedId as string);
        if (active) setSelectedJob(job);
      } catch {
        /* ignore */
      }
    }
    tick();
    const t = setInterval(tick, 1500);
    return () => {
      active = false;
      clearInterval(t);
    };
  }, [selectedId]);

  return (
    <div className="app">
      <header className="topbar">
        <span className="wordmark">
          <span className="br">{"<"}</span> paper2sim <span className="br">{"/>"}</span>
        </span>
        <a
          className="ghlink"
          href="https://github.com/ashw1nkumars/paper2sim"
          target="_blank"
          rel="noreferrer"
        >
          GitHub ↗
        </a>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">// paper → simulation</p>
          <h1>
            Don't just read the claim.
            <br />
            <span className="accent">Prove it.</span>
          </h1>
          <p className="lede">
            Drop in a math or CS paper — an <code>arXiv</code> id, a PDF, or pasted text. paper2sim
            extracts the central testable claim, writes a self-contained Python experiment, runs it
            in a sandbox, and shows you the plots, the animation, and a verdict.
          </p>
        </div>
        <Emblem />
      </section>

      <main className="layout">
        <aside className="sidebar">
          <SubmitForm onSubmitted={(id) => setSelectedId(id)} />
          <div className="card">
            <h2>Runs</h2>
            <JobList jobs={jobs} selectedId={selectedId} onSelect={setSelectedId} />
          </div>
        </aside>
        <JobDetail job={selectedJob} />
      </main>

      <footer className="footer">
        built with fastapi · celery · redis · react — MIT licensed
      </footer>
    </div>
  );
}
