# CLAUDE.md

Context for Claude Code working on this repository.

## What this is

**Cofre** is a personal portfolio command center — a web app where the user logs in, sees all their stocks/ETFs and registered Canadian accounts (TFSA/RRSP/FHSA/non-reg), and gets an AI analyst layer on top: retirement projections, crash-risk warnings, per-holding deep dives, TFSA/RRSP tax guidance, and rebalancing suggestions. Manual entry plus brokerage sync via SnapTrade.

This is a personal project, not a regulated product. It is not investment advice and must never be presented as such anywhere in the UI, copy, agent output, or marketing.

## Owner

Built by Jesse Moura. Solo project. Evenings and weekends. Don't propose architectures that assume a team — prefer simple, single-developer choices over scalable-but-complex ones.

## Architecture

```
Frontend (React + Vite + Tailwind + Recharts)
   ↓ HTTPS
Backend (FastAPI on Cloud Run)
   ↓
PostgreSQL (Cloud SQL)  ←  Market data jobs (Yahoo, Polygon)
   ↓                      ←  Brokerage sync (SnapTrade)
Claude Managed Agents API for narrative/synthesis
ML services for regime classification and news triage
```

The split that matters:
- **Deterministic math runs in Python services.** Monte Carlo, risk scores, contribution-room calculations, portfolio aggregations.
- **Narrative and synthesis runs in Claude.** Interpretation of pre-computed numbers, news triage, per-holding research.
- **Never let an LLM do arithmetic on retirement numbers.** This is a hard rule.

## Tech stack

- **Frontend:** React 18 + Vite + Tailwind CSS + Recharts. Inter for UI, JetBrains Mono for numbers. Glass/dark aesthetic established in the prototype — match it, don't redesign without discussion.
- **Backend:** FastAPI + async SQLAlchemy + asyncpg. Pydantic for validation. Python 3.11+.
- **Database:** PostgreSQL 14+. Schema in `backend/migrations/001_initial_schema.sql`.
- **Auth:** Firebase Auth (`firebase-admin` server-side).
- **Hosting:** Google Cloud Run (backend), Cloud SQL (database), Firebase Hosting (frontend).
- **AI:** Anthropic SDK (`anthropic` Python package). Use `claude-opus-4-7` for agent calls, `claude-haiku-4-5-20251001` for cheap classification jobs.
- **ML:** scikit-learn for regime classifier. Stored as joblib pickle, version-tagged.
- **Market data:** Yahoo Finance (`yfinance`) free tier for prototype, Polygon.io if upgrading.
- **Brokerage sync:** SnapTrade (better Canadian broker coverage than Plaid).

## Hard rules

1. **No investment advice.** Cofre presents analysis, observations, and probability ranges. It never recommends buying or selling specific securities.
2. **Math in Python, narrative in Claude.** Deterministic in `services/`. Claude only writes interpretation.
3. **Audit every Claude call.** Every call goes to the `agent_runs` table.
4. **Read-only brokerage permissions.** SnapTrade integration must request read-only scope.
5. **Encryption at rest.** No analytics tools on the frontend.
6. **Transactions are the source of truth.** Holdings derived. ACB tracked per holding in CAD.
7. **Disclaimers, real ones.** Every agent narrative output carries the disclaimer.
8. **No paywalled data sources** without owner approval.

## Style

**Python:** type hints, async by default for I/O, Pydantic v2, pure services.
**TypeScript / React:** functional components + hooks, Tailwind utilities inline, `useMemo` for derived values, no global state library.
**DB:** raw SQL migrations, FK with `ON DELETE CASCADE` where ownership applies, `uuid_generate_v4()` for IDs.
**Naming:** snake_case (Python/SQL/JSON), camelCase (TS/React), pluralized table names.
