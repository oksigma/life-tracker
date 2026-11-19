---
name: new-spec
description: Draft a new feature specification in docs/specs/ from the template. Use when the user wants to plan, spec out or design a new feature before building it.
argument-hint: <feature idea>
---

Create a new feature spec for: $ARGUMENTS

1. Read `docs/specs/README.md`, `docs/specs/_template.md`, `docs/product/features.md` and any related existing specs.
2. Pick the next number `NNNN` from existing files in `docs/specs/` and a short kebab-case name.
3. If the idea is too vague to fill in the requirements, ask the user up to 3 focused questions first.
4. Write `docs/specs/NNNN-short-name.md` from the template with Status `Draft` and today's date. Fill every section you can; put genuine unknowns under **Open questions** rather than guessing.
5. Add a row to the Index table in `docs/specs/README.md`.
6. Don't write any code. Summarize the spec and list the open questions for the user.
