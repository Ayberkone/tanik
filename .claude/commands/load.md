# /load

Open a new chat with this command after a previous session ran `/handoff`. Bootstraps context fast and stops before doing any real work.

> **Naming note.** Originally called `/resume`, but Claude Code has a built-in `/resume` that opens a session picker — the built-in always wins, so the project command never fires. Renamed to `/load` to avoid the collision.

## Steps

### 1. Read state in this order

1. `CLAUDE.md` — already auto-loaded; reaffirm the phase-gate + honesty conventions are top-of-mind
2. `ROADMAP.md` "Current status" — what phase, what was done, next action
3. `BACKLOG.md` — deferred items (don't act on them)
4. `.claude/session-state.md` if it exists — the previous session's task snapshot

### 2. Reconstruct the working picture

Run in parallel:
- `git log --oneline -15` — recent commits, confirm against ROADMAP claims
- `git status -sb` — should be clean (the previous /handoff refused otherwise)
- `git rev-parse HEAD` — confirm current commit matches the one ROADMAP claims

If reality doesn't match what `ROADMAP.md` "Current status" or `.claude/session-state.md` claims (e.g., commits exist that the state file doesn't mention, or vice versa), **stop and tell the user**. Do not assume the state file or your reading is correct — surface the divergence so the user can resolve it.

### 3. Rebuild the TaskList

For every task listed in `.claude/session-state.md` (if present), recreate it via `TaskCreate` so the session-local task tracker matches what's pending. Preserve the `[PHASE]` prefix and the description/activeForm.

If `.claude/session-state.md` does not exist (fresh start without prior `/handoff`), skip this step — the user is starting clean.

### 4. Produce the load summary

Print, in five sentences:

1. What TANIK is (one sentence — pulled from CLAUDE.md / README).
2. Current phase + last commit SHA + subject.
3. What was done last session (one or two bullet-style points if needed, in one sentence).
4. What's pending and why it's pending (deploy decision? user action? in-flight bug?).
5. The very next concrete action — name the task, name the file or files involved.

Then ask: **"Continue with that, or different?"**

### 5. Wait

Do not start any tool calls beyond the read-only ones above until the user replies. The point of `/load` is to load context, not to do work.

## Rules

- READ-ONLY in this command. No `Edit`, no `Write`, no `Bash` that mutates state.
- If `ROADMAP.md` "Current status" looks stale or wrong, say so explicitly — don't paper over it.
- If the user asks "what was the last thing you did?", trust git history over the state file (history is canonical, state file is a hint).
- The TaskList rebuild is best-effort. If a task description in `.claude/session-state.md` doesn't make sense in the current context, ask before recreating it verbatim.
