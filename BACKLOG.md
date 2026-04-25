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

## Notre Dame CVRL open-source iris algorithms (TripletIris / ArcIris) — comparison + dual-engine angle

Adam Czajka (ND CVRL) pointed at https://github.com/CVRL/OpenSourceIrisRecognition in the ND-IRIS-0405 access reply (2026-04-25). It contains TripletIris and ArcIris — the only two NIST IREX X-leaderboarded open-source iris recognition algorithms in existence (entries `ndcvrl_001` and `ndcvrl_002`; https://pages.nist.gov/IREX10/).

Why this matters: the entire credibility pitch of TANIK is honest, NIST-style benchmarking. Comparing Worldcoin's `open-iris` against ND's NIST-validated algorithms on a shared test set (e.g. ND-IRIS-0405 itself) is a stronger demonstration than evaluating any one engine in isolation — and it is exactly the kind of work that resonates with biometrics-industry engineers.

**Why this is NOT in Phase 1, 2, or 3:** CLAUDE.md explicitly forbids new ML dependencies beyond `open-iris` and SourceAFIS in the first three phases. Pulling TripletIris/ArcIris in now would restructure a working iris engine and detonate Phase 1's deployment path. Wrong time.

**Where it could land later:** A natural Phase 3.5 / Phase 5 follow-up — once `docs/performance.md` exists with measured FAR/FRR for `open-iris`, add a parallel column with the same metrics from TripletIris and ArcIris. This is the kind of comparative, NIST-style table that publishes well as a blog post and is hard for any biometrics engineer to dismiss.

**Distinct v2 product direction:** offer TANIK as a *pluggable iris engine harness* — three engines behind one `BiometricEngine` interface, the operator picks per-deployment. That is a real product differentiator vs. single-engine demos. Decide later; do not let it leak into v1 scope.

## ND-IRIS-0405 license agreement — execution

Adam confirmed (2026-04-25) that the dataset is requestable via the formal license agreement process at https://cvrl.nd.edu/projects/data/. This is the long-pole for Phase 3 evaluation; TANIK cannot ship measured FAR/FRR numbers without a real iris dataset. Tracked as an active SIDE task — see the task list — not as backlog.
