# Architecture Overview

```
[ Next.js frontend ]  --HTTP/JSON-->  [ FastAPI backend (Uvicorn) ]  -->  [ MongoDB ]
     :3000                                  :8000  /api, /docs
```

- **Frontend:** React + Next.js (App Router), TypeScript — `life-tracker-app/frontend`
- **Backend:** Python 3.12, FastAPI, served by Uvicorn, managed with uv — `life-tracker-app/backend`
- **Database:** MongoDB via PyMongo async; collections documented in `life-tracker-app/database/schema.md`
- **Contract:** the backend's OpenAPI schema (`/openapi.json`) defines request/response shapes for the frontend
- **Infra:** docker-compose for local MongoDB, CI config — `life-tracker-app/infra`
- **Same-origin API:** the browser calls `/api/*` on the frontend; Next.js rewrites it to the backend (`BACKEND_URL`, default `http://localhost:8000`)
- **Login:** one app password (spec 0006); auth middleware checks a signed session cookie on every `/api` route except health and auth

## Deployed (ADR 0004)
```
[ Browser ] --> [ Vercel: Next.js ] --/api rewrite--> [ Vercel: FastAPI function ] --> [ MongoDB Atlas ]
```
Setup steps: [`deployment.md`](deployment.md).

Record significant decisions as ADRs in [`decisions/`](decisions/).
