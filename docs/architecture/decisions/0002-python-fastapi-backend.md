# 0002. Python backend with FastAPI and Uvicorn

- **Status:** Accepted
- **Date:** 2026-11-14

## Context
The backend language was chosen as Python, served with Uvicorn. Uvicorn is an ASGI server and needs a web framework on top.

## Decision
Use FastAPI on Uvicorn, Python 3.12, with dependencies managed by uv and linting by Ruff.

## Alternatives considered
- **Node.js + Express** (original scaffold): would share TypeScript types with the frontend, but Python was preferred.
- **Django / Django REST Framework:** heavier, built around a relational ORM; a poor fit for MongoDB.
- **Starlette alone:** FastAPI adds validation (Pydantic) and automatic API docs on top of it.

## Consequences
- Frontend and backend no longer share a TypeScript types package; the OpenAPI schema becomes the contract.
- Automatic interactive API docs at `/docs`.
