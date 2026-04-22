# TANIK Backlog

Ideas, follow-ups, and deferred work that is **not** in a current roadmap phase. Items land here so they are captured without contaminating the active phase.

An item in this file is not a commitment. It is a note that, at some point, a decision needs to be made about whether to pull it into a phase or drop it.

When considering an item, either:
- Consciously pull it into the current phase in `ROADMAP.md`, or
- Promote it to a future phase in `ROADMAP.md`, or
- Delete it from this file because it's no longer wanted.

Do not let items rot here indefinitely without a decision.

---

## Phone-as-reader access control — distinct v2 product direction

A separate product direction to the TANIK kiosk: a user's phone presents to a door, gate, or lock; the phone's native secure biometric (Face ID / BiometricPrompt) unlocks a private key in the secure enclave, which signs a BLE challenge from the lock.

Already captured in `ROADMAP.md` under "Larger deferrals — potential v2 product directions → Mobile-phone-as-reader access control." Mirrored here as a reminder that this is a **different product**, not a feature of TANIK: different customer (end consumer / property managers vs. government/enterprise identity buyers), different threat model (decentralized per-device keys vs. centralized server-side templates), different stack (native iOS/Android + BLE firmware vs. web kiosk + backend), different go-to-market.

Revisit only after TANIK Phase 5 ships. When revisited, treat as a ground-up new project — the TANIK codebase does not extend incrementally into this.

## Merge general-purpose conventions from farmalink's CLAUDE.md into TANIK's

The farmalink project has accumulated general-purpose Claude Code conventions (tone, code style, guardrails) that are not farmalink-specific and would also apply here. Audit farmalink's `CLAUDE.md`, identify the portable conventions, and merge them into TANIK's `CLAUDE.md` without duplicating or diluting the TANIK-specific sections (phase-gate discipline, biometric honesty conventions, technical stack rules).

Do this as a focused pass, not incrementally. The risk of an incremental merge is that the TANIK-specific discipline gets blurred by generic guidance — keep the phase-gate section and the honesty section prominent and untouched.
