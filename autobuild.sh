#!/usr/bin/env bash
#
# autobuild.sh — fresh-context resume loop for TANIK (≡ "/clear then /load-and-ship", repeated).
#
# Ported from ~/sahibinden/auto-build.sh. Each iteration runs `claude -p "$PROMPT"`
# in headless mode. Headless starts with ZERO prior context (that is the /clear),
# and the default prompt makes Claude re-read the on-disk handoff — ROADMAP.md
# "Current status" + .claude/session-state.md + BACKLOG.md — and ship the next
# unit of work end-to-end. When the process exits, the next iteration starts from
# a clean slate. So this is the /clear + resume cadence, automated, with no manual
# typing between features.
#
# TANIK NOTE: the interactive /load skill deliberately loads state and then STOPS
# and waits. That is wrong for an unattended loop, so the default PROMPT below
# loads the same handoff but keeps going — while explicitly honoring the
# phase-gate discipline in CLAUDE.md (never pull work forward from a later phase;
# scope drift is this project's #1 failure mode). If the only remaining work is
# blocked (e.g. awaiting datasets), it does a docs/test-hardening pass instead of
# inventing scope, and makes no commit if there is genuinely nothing safe to ship.
#
# ─────────────────────────────────────────────────────────────────────────────
# SAFETY — READ THIS
#   • Runs UNATTENDED with --dangerously-skip-permissions: no approval prompts.
#     TANIK's standing rules still apply (they live in CLAUDE.md, and the
#     .claude/hooks/pre-tool-safety.sh hook still fires regardless of permission
#     mode), but there is no human gate, so only run this on a repo + branch you
#     are happy to let it drive autonomously.
#   • It does NOT cap turns within an iteration — a half-finished branch would be
#     worse than a long run — so each iteration runs a full unit of work to
#     completion. It caps the NUMBER of iterations instead (MAX_ITERS).
#   • Stop it cleanly at any time:  touch .stop-build   (ends after the current
#     iteration finishes). Ctrl-C also works but may interrupt mid-feature.
# ─────────────────────────────────────────────────────────────────────────────
#
# Usage:
#   ./autobuild.sh                  # loop forever until `touch .stop-build`
#   ./autobuild.sh 10               # ship at most 10 iterations, then stop
#   MAX_ITERS=10 ./autobuild.sh     # same thing via env var
#   PROMPT="continue, but only the docs consistency pass" ./autobuild.sh
#   SLEEP_SECS=30 ./autobuild.sh    # longer breather between iterations
#
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR" || exit 1

# TANIK resume-and-ship prompt (the /load convention, but proceed instead of wait).
DEFAULT_PROMPT='Resume autonomously from the on-disk handoff and ship the next unit of work end-to-end. \
(1) Read CLAUDE.md, ROADMAP.md "Current status", BACKLOG.md, and .claude/session-state.md to rebuild the picture \
(this is the /load convention, but do NOT stop and wait — proceed). \
(2) Pick the next actionable task from the CURRENT phase in ROADMAP.md. Honor the phase-gate discipline: never pull \
work forward from a later phase. If the only remaining work is blocked (e.g. awaiting datasets), do a docs consistency \
or test-hardening pass instead — do not invent scope. \
(3) Implement it, run the relevant tests, and commit with a conventional message per CLAUDE.md. \
(4) Update ROADMAP.md "Current status" and .claude/session-state.md so the next iteration resumes cleanly. \
If there is genuinely nothing safe to ship, make NO commit and say so.'

# A bare positional integer is a convenience alias for MAX_ITERS (so `./autobuild.sh 10` works).
if [[ "${1:-}" =~ ^[0-9]+$ ]]; then
  MAX_ITERS="$1"
fi

PROMPT="${PROMPT:-$DEFAULT_PROMPT}"
MAX_ITERS="${MAX_ITERS:-0}"          # 0 = unlimited
SLEEP_SECS="${SLEEP_SECS:-5}"        # breather after a productive iteration
STOP_FILE="$REPO_DIR/.stop-build"
LOG_FILE="$REPO_DIR/.autobuild.log"

# Backoff guard (carried over from sahibinden's 2026-06-29 incident: ~30 empty
# iterations burned in 6-min loops). An iteration is a "no-op" when it ships no
# commit (HEAD unchanged). Consecutive no-ops back off exponentially and, past
# MAX_NOOP, stop the loop so it surfaces to a human fast rather than spinning.
MAX_NOOP="${MAX_NOOP:-5}"                     # give up after this many idle iterations in a row
MAX_BACKOFF_SECS="${MAX_BACKOFF_SECS:-1800}"  # cap on exponential backoff between no-ops

command -v claude >/dev/null 2>&1 || { echo "error: 'claude' CLI not found on PATH" >&2; exit 1; }

# A leftover sentinel from a previous run would stop us instantly — clear it and
# warn, so an intentional `touch .stop-build` is always a fresh signal.
if [[ -f "$STOP_FILE" ]]; then
  echo "note: removing stale $STOP_FILE so the loop can start" >&2
  rm -f "$STOP_FILE"
fi

trap 'echo; echo "[autobuild] interrupted — exiting after Ctrl-C"; exit 130' INT

iter=0
noop_streak=0
echo "[autobuild] starting in $REPO_DIR (max_iters=$MAX_ITERS, max_noop=$MAX_NOOP). touch .stop-build to stop." | tee -a "$LOG_FILE"

while :; do
  if [[ -f "$STOP_FILE" ]]; then
    echo "[autobuild] .stop-build present — stopping." | tee -a "$LOG_FILE"
    rm -f "$STOP_FILE"
    break
  fi
  if [[ "$MAX_ITERS" -gt 0 && "$iter" -ge "$MAX_ITERS" ]]; then
    echo "[autobuild] reached MAX_ITERS=$MAX_ITERS — stopping." | tee -a "$LOG_FILE"
    break
  fi

  iter=$((iter + 1))
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  echo "" | tee -a "$LOG_FILE"
  echo "════════ [autobuild] iteration $iter @ $ts ════════" | tee -a "$LOG_FILE"

  # Capture this iteration's output separately so we can inspect it for hard-block
  # signals, and snapshot HEAD so we can tell whether the iteration actually shipped.
  iter_out="$(mktemp "${TMPDIR:-/tmp}/autobuild.XXXXXX")"
  head_before="$(git rev-parse HEAD 2>/dev/null || echo none)"

  # Fresh context every iteration (no --continue/--resume) = the /clear.
  claude -p "$PROMPT" --dangerously-skip-permissions 2>&1 | tee -a "$LOG_FILE" "$iter_out"
  rc=${PIPESTATUS[0]}

  head_after="$(git rev-parse HEAD 2>/dev/null || echo none)"
  echo "[autobuild] iteration $iter exited rc=$rc" | tee -a "$LOG_FILE"

  # Classify the outcome (label only changes the log line; all non-progress
  # outcomes share the same exponential backoff + MAX_NOOP stop).
  #   progress  → HEAD moved (a feature/docs commit landed): reset the streak.
  #   spend     → "spend limit" message — usually a SPURIOUS bug, needs a human.
  #   transient → 503 / 529 / overloaded / generic API error: should self-clear.
  #   idle      → exited cleanly but shipped nothing (e.g. nothing to do).
  if [[ "$head_after" != "$head_before" ]]; then
    outcome="progress"
  elif grep -qiE 'spend limit|usage limit|out of credit' "$iter_out"; then
    outcome="spend"
  elif grep -qiE 'api error|overloaded|\b503\b|\b529\b|status code' "$iter_out"; then
    outcome="transient"
  else
    outcome="idle"
  fi
  rm -f "$iter_out"

  if [[ "$outcome" == "progress" ]]; then
    noop_streak=0
    echo "[autobuild] progress: HEAD $head_before → $head_after — breather ${SLEEP_SECS}s." | tee -a "$LOG_FILE"
    sleep "$SLEEP_SECS"
    continue
  fi

  # No progress — escalate.
  noop_streak=$((noop_streak + 1))
  if [[ "$noop_streak" -ge "$MAX_NOOP" ]]; then
    echo "[autobuild] $noop_streak consecutive no-op iterations (last=$outcome) — stopping to avoid spinning. Fix the block, then restart." | tee -a "$LOG_FILE"
    break
  fi

  # 2^streak * SLEEP_SECS, capped — e.g. 10,20,40,80s ... up to MAX_BACKOFF_SECS.
  backoff=$(( SLEEP_SECS * (1 << noop_streak) ))
  [[ "$backoff" -gt "$MAX_BACKOFF_SECS" ]] && backoff="$MAX_BACKOFF_SECS"
  echo "[autobuild] no-op ($outcome, streak $noop_streak/$MAX_NOOP) — backing off ${backoff}s (Ctrl-C or touch .stop-build to stop)." | tee -a "$LOG_FILE"
  sleep "$backoff"
done

echo "[autobuild] loop ended after $iter iteration(s)." | tee -a "$LOG_FILE"
