---
name: implement-spec
description: Implement an approved feature spec from docs/specs/ end to end across shared, database, backend and frontend.
argument-hint: <spec file or number>
disable-model-invocation: true
---

Implement the spec: $ARGUMENTS

1. Find and read the spec in `docs/specs/`. If its status is `Draft`, stop and ask the user whether to approve it first.
2. Read `life-tracker-app/CLAUDE.md` and the CLAUDE.md in each workspace you'll touch.
3. Set the spec status to `In progress`.
4. Work through the **Implementation checklist** in order (backend schemas → database → backend module → frontend → tests), ticking items in the spec as each is done.
5. Run `uv run pytest` and `uv run ruff check .` for backend changes, and lint and type checks for frontend changes; fix failures before moving on.
6. If you have to deviate from the spec, update the spec and note why.
7. When all acceptance criteria pass, set status to `Done`, update the spec index, and update `life-tracker-app/database/schema.md` / `docs/architecture/overview.md` if they changed.
8. Report what was built, what was tested, and anything left open.
