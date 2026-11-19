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

Record significant decisions as ADRs in [`decisions/`](decisions/).
