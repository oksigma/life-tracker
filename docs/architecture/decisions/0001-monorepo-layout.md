# 0001. Repository layout with docs separated from code

- **Status:** Accepted
- **Date:** 2026-11-14

## Context
We want planning and documentation to live alongside the code without being mixed into it.

## Decision
The project root holds documentation only. All code lives under `life-tracker-app/`, containing `frontend`, `backend`, `database` and `infra`.

## Consequences
- Docs can be edited without touching code tooling.
- One git repository covers docs and code.
