# Contributing to paper2sim

Thanks for your interest - **contributions are welcome and appreciated!** 🎉

paper2sim is an open-source, MIT-licensed project. Bug fixes, new LLM providers,
better prompts, sandbox hardening, tests, docs, and example runs are all great
ways to help.

## Ways to contribute

- 🐛 **Report a bug** - open an issue with steps to reproduce.
- 💡 **Suggest a feature** - open an issue describing the idea and the use case.
- 🔧 **Send a PR** - fix a bug, add a provider, improve prompts, harden the sandbox, or improve docs.
- 📄 **Add an example** - a neat paper → simulation run for the gallery.

Not sure where to start? Look at the **Roadmap** and **Extending paper2sim**
sections in the [README](README.md), or open an issue to discuss.

## Development setup

Requirements: Docker + Docker Compose (for the full stack), or Python 3.12 and
Node 22 for running pieces directly.

```bash
git clone https://github.com/ashw1nkumars/paper2sim.git
cd paper2sim
docker compose up --build          # full stack at http://localhost:5173
```

Backend (without Docker):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Everything runs with **no API key** thanks to the deterministic mock provider, so
you can develop and test offline.

## Before you open a PR

Please make sure the same checks CI runs pass locally:

```bash
# Backend
cd backend
ruff check .        # lint (ruff format . to auto-format)
pytest              # tests (uses the mock provider; no key/Redis needed)

# Frontend
cd frontend
npm run build       # type-checks with strict TypeScript
```

Or use the Makefile: `make lint`, `make test`.

## Guidelines

- **Keep it focused** - one logical change per PR; describe *what* and *why*.
- **Match the surrounding style** - the backend follows `ruff` (config in
  `backend/pyproject.toml`); the frontend uses strict TypeScript.
- **Add tests** for new backend behavior where it makes sense.
- **Update docs** - if you change config, the API, or behavior, update the README.
- **Never commit secrets** - no API keys, tokens, or `.env` files. `.env` is gitignored.
- **Be respectful** - see the [Code of Conduct](CODE_OF_CONDUCT.md).

## Commit & PR flow

1. Fork the repo and create a branch: `git checkout -b feat/my-change`.
2. Make your change; run the checks above.
3. Push and open a PR against `main` with a clear description.
4. CI will run `ruff` + `pytest` + the frontend build on your PR.

By contributing, you agree that your contributions are licensed under the
project's [MIT License](LICENSE).
