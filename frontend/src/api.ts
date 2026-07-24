// Typed client for the paper2sim API. Uses same-origin relative URLs so it works
// behind the nginx proxy in Docker and the Vite dev proxy locally.

export type JobStatus =
  | "queued"
  | "ingesting"
  | "analyzing"
  | "generating"
  | "executing"
  | "repairing"
  | "summarizing"
  | "completed"
  | "failed";

export interface Analysis {
  claim: string;
  why_it_matters: string;
  simulation_plan: string;
}

export interface ExecutionResult {
  returncode: number;
  stdout: string;
  stderr: string;
  duration_seconds: number;
  artifacts: string[];
  result_json: Record<string, unknown> | null;
  attempt: number;
  timed_out: boolean;
}

export interface Job {
  id: string;
  status: JobStatus;
  source_kind: string;
  source_ref: string;
  title: string;
  created_at: string;
  updated_at: string;
  llm_provider: string;
  error: string | null;
  paper_excerpt: string;
  analysis: Analysis | null;
  code: string;
  execution: ExecutionResult | null;
  verdict: string;
  summary: string;
}

export const TERMINAL: JobStatus[] = ["completed", "failed"];

export interface SubmitInput {
  arxiv?: string;
  text?: string;
  title?: string;
  file?: File | null;
}

export async function submitPaper(input: SubmitInput): Promise<{ job_id: string }> {
  const form = new FormData();
  if (input.file) form.append("file", input.file);
  if (input.arxiv) form.append("arxiv", input.arxiv);
  if (input.text) form.append("text", input.text);
  if (input.title) form.append("title", input.title);

  const resp = await fetch("/api/papers", { method: "POST", body: form });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail || `Request failed (${resp.status})`);
  }
  return resp.json();
}

export async function listJobs(): Promise<Job[]> {
  const resp = await fetch("/api/jobs");
  if (!resp.ok) throw new Error(`Failed to load jobs (${resp.status})`);
  return resp.json();
}

export async function getJob(id: string): Promise<Job> {
  const resp = await fetch(`/api/jobs/${id}`);
  if (!resp.ok) throw new Error(`Failed to load job (${resp.status})`);
  return resp.json();
}

export function artifactUrl(relPath: string): string {
  return `/api/artifacts/${relPath}`;
}
