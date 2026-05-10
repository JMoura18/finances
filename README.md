# Cofre

Personal portfolio command center. See [CLAUDE.md](./CLAUDE.md) for the full context.

## Layout

```
backend/   FastAPI + SQLAlchemy + deterministic services
frontend/  Vite + React + TS + Tailwind, mobile-first responsive
```

## Run locally

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`.

## Disclaimer

Cofre provides portfolio analytics and information. It does not provide
investment, tax, or legal advice. Consult a licensed advisor before making
investment decisions.
