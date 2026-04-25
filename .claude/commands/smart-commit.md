---
name: smart-commit
description: Analyze staged + unstaged changes and create a well-formatted conventional commit
---

# /smart-commit

Analyze staged + unstaged changes and create a well-formatted conventional commit.

## Steps

1. Run `git status` and `git diff` to see all changes.
2. Determine the conventional commit type:
   - `feat` — new feature
   - `fix` — bug fix
   - `refactor` — code restructuring without behavior change
   - `test` — adding or updating tests
   - `docs` — documentation only
   - `chore` — maintenance, deps, config
   - `perf` — performance
   - `ops` — deployment / CI / Docker
3. Determine the scope from the changed paths:
   - `(inference)` — `apps/inference/` changes
   - `(client)` — `apps/client/` changes
   - `(notebooks)` — `notebooks/` changes
   - `(phase-N)` — when the change advances roadmap Phase N (`feat(phase-1):`)
   - Omit the scope if the change is cross-cutting
4. Draft a 1-line subject (≤72 chars) + optional body explaining **why**, not what.
5. Present to the user for approval before staging + committing.
6. Stage only the relevant files (review the staged diff — never `git add -A` blindly).

## Format

```
type(scope): concise subject

Optional body: motivation, not implementation. Reference roadmap
phase, BACKLOG entry, or the relevant CLAUDE.md rule when useful.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

## Rules

- NEVER commit `.env`, `.venv/`, `notebooks/data/`, `*.db`, `node_modules/`, or `.next/`
- NEVER use `git add -A` or `git add .` blindly
- NEVER push (the user does push manually)
- Subject under 72 chars, lowercase after the type
- Body explains the why; the diff already explains the what
- For Phase-boundary commits, also flag whether `ROADMAP.md` "Current status" needs updating in the same commit
