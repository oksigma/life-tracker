# LifeTracker — App

| Folder | Purpose |
|---|---|
| `frontend/` | React + Next.js (TypeScript) web app |
| `backend/` | Python FastAPI API, run with Uvicorn |
| `database/` | MongoDB collection docs and seed data |
| `infra/` | docker-compose (MongoDB), Dockerfiles, CI |
| `scripts/` | Dev and maintenance scripts |
| `tests/e2e/` | End-to-end tests across the whole stack |

## Getting started

Needs Node.js, Python 3.12, [uv](https://docs.astral.sh/uv/) and Docker.

```bash
cp .env.example .env
npm install                 # frontend
(cd backend && uv sync)     # backend
npm run db:up               # start MongoDB
npm run dev                 # frontend :3000, backend :8000 (docs at /docs)
```

## Life areas
Clothing, health, movies, food and drinks. Each has matching folders in
`frontend/src/features/<area>`, `frontend/src/app/<area>` and `backend/app/modules/<area>`.
