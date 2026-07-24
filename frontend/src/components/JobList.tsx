import type { Job } from "../lib/api";

export default function JobList({
  jobs,
  selectedId,
  onSelect,
}: {
  jobs: Job[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  if (jobs.length === 0) {
    return <p className="muted">No runs yet. Submit a paper to get started.</p>;
  }
  return (
    <ul className="joblist">
      {jobs.map((job) => (
        <li
          key={job.id}
          className={job.id === selectedId ? "jobitem active" : "jobitem"}
          onClick={() => onSelect(job.id)}
        >
          <span className="jobtitle">{job.title || job.id}</span>
          <span className={`badge ${job.status}`}>{job.status}</span>
        </li>
      ))}
    </ul>
  );
}
