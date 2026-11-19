# 0003. MongoDB as the database

- **Status:** Accepted
- **Date:** 2026-11-14

## Context
Tracked entries vary a lot between life areas (an outfit, a movie, a meal), and their fields are likely to change as the app evolves.

## Decision
Use MongoDB, run locally in Docker, accessed from the backend with PyMongo's async client.

## Alternatives considered
- **PostgreSQL** (original scaffold): stronger relational guarantees, but needs schema migrations for every field change.

## Consequences
- Flexible documents per life area; schema is enforced by Pydantic models in the backend.
- Collections and indexes are documented in `life-tracker-app/database/schema.md`.
- No database-level foreign keys; references between collections are checked in the backend.
