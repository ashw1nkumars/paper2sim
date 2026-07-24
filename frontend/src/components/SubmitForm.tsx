import { useState } from "react";
import { submitPaper } from "../lib/api";

type Mode = "arxiv" | "text" | "pdf";

const SAMPLE = `Title: A Monte Carlo estimate of pi

We claim that estimating pi by sampling random points in the unit square and
counting those inside the quarter circle converges to the true value, with the
absolute error shrinking at a rate proportional to 1/sqrt(N).`;

export default function SubmitForm({ onSubmitted }: { onSubmitted: (id: string) => void }) {
  const [mode, setMode] = useState<Mode>("arxiv");
  const [arxiv, setArxiv] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const payload =
        mode === "arxiv"
          ? { arxiv }
          : mode === "text"
            ? { text }
            : { file };
      const { job_id } = await submitPaper(payload);
      onSubmitted(job_id);
      setArxiv("");
      setText("");
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  const canSubmit =
    !busy &&
    ((mode === "arxiv" && arxiv.trim()) ||
      (mode === "text" && text.trim()) ||
      (mode === "pdf" && file));

  return (
    <form className="card submit" onSubmit={handleSubmit}>
      <h2>Submit a paper</h2>
      <div className="tabs">
        {(["arxiv", "text", "pdf"] as Mode[]).map((m) => (
          <button
            type="button"
            key={m}
            className={mode === m ? "tab active" : "tab"}
            onClick={() => setMode(m)}
          >
            {m === "arxiv" ? "arXiv" : m === "text" ? "Paste text" : "Upload PDF"}
          </button>
        ))}
      </div>

      {mode === "arxiv" && (
        <input
          className="field"
          placeholder="arXiv id or URL, e.g. 1706.03762"
          value={arxiv}
          onChange={(e) => setArxiv(e.target.value)}
        />
      )}

      {mode === "text" && (
        <>
          <textarea
            className="field"
            rows={7}
            placeholder="Paste an abstract or the statement of a claim…"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <button type="button" className="link" onClick={() => setText(SAMPLE)}>
            Use a sample claim
          </button>
        </>
      )}

      {mode === "pdf" && (
        <input
          className="field"
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      )}

      {error && <p className="error">{error}</p>}

      <button className="primary" disabled={!canSubmit} type="submit">
        {busy ? "Submitting…" : "Prove it →"}
      </button>
    </form>
  );
}
