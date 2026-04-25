# /handoff

Close the current session cleanly so a fresh chat can pick up exactly where we left off via `/load`. Run this when the conversation gets heavy (long tool-call history, slow responses) and you want a fresh context.

## Refusal conditions — if any of these are true, stop and tell the user

1. **Uncommitted changes** — `git status --porcelain` is non-empty. Either commit (via `/smart-commit`) or stash. Don't continue with dirty state.
2. **In-flight tool task** — a Bash run_in_background or Monitor that hasn't completed. Either wait for it or stop it explicitly.

If refused, print the blocker clearly and what the user needs to do.

## Steps when not refused

### 1. Survey

Run in parallel:
- `git log --oneline -15` — recent commits
- `git status -sb` — confirm clean
- TaskList tool — current pending / in-progress tasks

### 2. Update `ROADMAP.md` "Current status"

Edit the section at the bottom of `ROADMAP.md` to capture:

- **Phase**: which phase we're in
- **Last commit**: SHA + one-line subject
- **What was done this session**: 2–4 bullets of meaningful changes (not every commit — meaningful units of work)
- **In flight**: anything started but not finished, including tasks marked `in_progress` in the TaskList
- **Next concrete action**: the single most-likely next step in one sentence, with the relevant task ID if applicable
- **Open user-action items**: SIDE tasks waiting on the user (email, deploy, decisions)

Keep the rest of `ROADMAP.md` (phase definitions etc.) untouched.

### 3. Snapshot the task list to `.claude/session-state.md`

Write a fresh `.claude/session-state.md` that the new session can read and rebuild the TaskList from. Format:

```markdown
# Session state — handoff snapshot
**Generated:** YYYY-MM-DD HH:MM TZ
**Last commit:** <SHA> — <subject>
**Branch:** main (N commits ahead of origin)

## Pending tasks (rebuild via TaskCreate on /load)

### [SIDE]
- (#11) [SIDE] Execute ND-IRIS-0405 license agreement at cvrl.nd.edu/projects/data
  — Adam Czajka confirmed 2026-04-25; user action.

### [P1]
- (#19) [P1] Structured logging across endpoints
  — done in commit fa5e764, leave for /load to verify and mark complete.
- ... etc.

### [P2]
- (#34) [P2] Choose + integrate SourceAFIS Python binding
- ...

## Decisions made this session not yet in code/docs

- (none) | or: short list of "we decided X but haven't written it down anywhere durable yet"

## Resume hint

The next concrete action is: <one sentence>. Start by reading ROADMAP.md "Current status" and this file, then ask the user.
```

This file is gitignored — it's a baton, not history.

### 4. Save any new feedback memories

If the user corrected your approach this session in a way you haven't yet captured in `~/.claude/projects/-Users-ayberkbaytok-tanik/memory/`, save those now. Examples:

- A new collaboration preference you learned
- A "don't do X again" rule
- An honesty / scope / phase-gate nuance the user reinforced

Skip this step if you didn't learn anything new about how to collaborate. Don't manufacture memories.

### 5. Final message to the user

Print, in this exact shape:

```
Session handed off.
- Commits this session: N (range a1b2c3d → e4f5g6h)
- ROADMAP "Current status" updated.
- .claude/session-state.md written (M tasks snapshotted).
- Auto-memory entries added: <list, or "none">.

Open a new chat and type: /load
```

Don't say anything after that — the handoff is the end of the session.

## Rules

- NEVER make a real code change in this command. It is a state-capture step only.
- NEVER push or pull. Local state matters; remote state is your concern only via the `git log` snapshot.
- If `ROADMAP.md` or `BACKLOG.md` was changed during the session and not committed, that's an uncommitted-changes refusal — go commit them first.
- Treat the `.claude/session-state.md` file as ephemeral. Overwriting it is correct; merging is not.
