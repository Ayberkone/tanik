---
name: quick-fix
description: Use for small, well-scoped tasks (< 5 files, no architectural decisions) that don't need the full pm-spec → architect → implementer → qa pipeline. Bug fixes, copy tweaks, dependency bumps, adding a single endpoint field.
---

# /quick-fix — Pipeline-free implementation

Solo, tight tasks. Implement directly, test, done.

## When to use

- Bug fixes
- Small additions (< 5 files): adding a single field to an endpoint, tightening a validator, fixing a doc
- Copy / docstring changes
- Config / env-var additions
- Dependency bumps with no API change

## When NOT to use (use the full pipeline instead)

- New endpoints crossing concerns (auth, storage, validation, pipeline)
- Architectural changes (new module, new abstraction)
- Anything that touches `docs/api-contract.md` non-trivially
- Anything that introduces a new ML dependency (which is forbidden in Phases 1-3 anyway — push back)
- Anything that crosses a phase boundary

## Process

1. **Understand the task.** Read the relevant files, grep for callers/consumers.
2. **Implement.** Follow `CLAUDE.md` conventions — Pydantic v1 on backend, magic-byte validation, `run_in_threadpool` around iris work, no hardcoded thresholds, no raw image persistence.
3. **Test.**
   - Backend: `.venv/bin/pytest apps/inference/tests/test_<module>.py -v`
   - Client: `cd apps/client && pnpm test <file>`
4. **Verify the change end-to-end** if it touches a request path. A real `curl` against a real fixture beats unit tests for endpoint changes.
5. **Pre-completion audit (lightweight):** grep for every consumer of what you changed; eyeball each.
6. **Commit** with `/smart-commit`.

## Anti-patterns

- ❌ Splitting a quick-fix into multiple commits because "the diff got big" — if the diff got big, this was not a quick-fix; back out and run the full pipeline
- ❌ Adding a new pattern without checking the existing pattern first
- ❌ Skipping the end-to-end verification because "the unit test passes" — for endpoint changes, the unit test does not prove the wire format
