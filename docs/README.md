# TANIK documentation index

Every doc in this directory, with a one-line description of what it's for and who should read it. GitHub renders this file when you browse `docs/` so this is the discoverability surface.

For the project as a whole, start with the root [`README.md`](../README.md), then [`ROADMAP.md`](../ROADMAP.md), then [`OWNER-ACTIONS.md`](../OWNER-ACTIONS.md).

---

## Start here

| Doc | What it's for | Read if… |
|---|---|---|
| [`architecture.md`](architecture.md) | Top-to-bottom system walkthrough — the canonical reference | …you have 30 minutes and want to understand the whole system. Sections 1+2+3+8 are the 5-minute version |
| [`api-contract.md`](api-contract.md) | The HTTP contract — source of truth | …you are integrating with TANIK or auditing what the endpoints actually do |
| [`sequence-flow.md`](sequence-flow.md) | State machine + Mermaid sequence diagrams for every flow | …you want to see what happens, in order, on enrol / verify / fused-verify |
| [`development.md`](development.md) | Local dev (native, Docker, hybrid) + every env var | …you want to run TANIK on your own machine |
| [`glossary.md`](glossary.md) | Biometrics vocabulary reference card | …you're software-fluent but new to biometrics terms |

## Phase 3 (in flight)

| Doc | What it's for |
|---|---|
| [`fusion.md`](fusion.md) | Score-normalisation + weighted-sum fusion methodology + the explicit calibration-placeholder caveat |
| [`performance.md`](performance.md) | **Skeleton** for FAR/FRR/ROC reporting; every cell is `TBD`; will be machine-written by `tests/evaluation/` (`#43`) once dataset acquisition (`#11`) lands |
| [`nd-iris-0405-access.md`](nd-iris-0405-access.md) | Step-by-step license-execution checklist for the Phase 3 iris dataset (`#11`) — what only the human owner can do |
| [`datasets.md`](datasets.md) | Every dataset referenced in the repo with source + license + access path |

## Phase 4 prep (working drafts / skeletons)

These are written ahead of Phase 4 implementation deliberately — to lock the framework, give Proline-presentation material immediately, and let the eventual implementation slot into a known shape.

| Doc | What it's for |
|---|---|
| [`threat-model.md`](threat-model.md) | Scope, attacker model, asset inventory, attack-by-attack table with current mitigations and gaps. ISO/IEC alignment |
| [`privacy.md`](privacy.md) | KVKK + GDPR + EU AI Act posture; per-data-category inventory; "templates ARE personal data" precision; explicit gap list |
| [`pad.md`](pad.md) | Phase 4 presentation-attack-detection plan; ISO/IEC 30107 framework; candidate datasets and approaches |
| [`admin-api.md`](admin-api.md) | Phase 4 operator API surface; six endpoints; OIDC + audit log pattern; restart-required configuration mutations by design |
| [`admin-dashboard.md`](admin-dashboard.md) | Phase 4 operator UI surface; five pages inside the existing Next.js app at `/admin/*` |

## Phase 5 prep

| Doc | What it's for |
|---|---|
| [`blog-post-draft.md`](blog-post-draft.md) | Full-length tech-blog draft for an outward-facing publish (dev.to / personal blog / Medium / Hashnode). Three suggested titles; conversational tone |
| [`proline-pitch-deck.md`](proline-pitch-deck.md) | **Marp-compatible** 20-slide deck for a 15-20 minute talk. Render to PDF/HTML/PPTX with `npx @marp-team/marp-cli docs/proline-pitch-deck.md -o tanik-pitch.pdf` |
| [`comparison.md`](comparison.md) | Honest positioning of TANIK vs commercial vendors (Suprema, IDEMIA, NEC), other open-source iris (CVRL OpenSourceIrisRecognition / TripletIris + ArcIris), other open-source fingerprint, and face-recognition systems |

## Outreach

| Doc | What it's for |
|---|---|
| [`outreach/nd-iris-request.md`](outreach/nd-iris-request.md) | Email draft for ND-CVRL access request |
| [`outreach/nd-iris-thanks.md`](outreach/nd-iris-thanks.md) | Reply draft to Adam Czajka (2026-04-25) acknowledging the access pointer + the OpenSourceIrisRecognition pointer |

---

## What's NOT yet here (and why)

Some docs that *will* exist are deliberately not here yet:

- **`docs/figures/`** — ROC curves and other generated images. Arrives when `tests/evaluation/` (`#43`) generates them.
- **`docs/operator-handbook.md`** — runbook for "you've inherited a TANIK deployment, here's what to do day-to-day." Premature without the Phase 4 admin surface; would be half-written caveats.
- **`docs/faq.md`** — anticipated FAQ. Would mostly duplicate the `proline-pitch-deck.md` speaker notes; defer until the project has actually surfaced repeated questions from real readers.
- **`docs/figures/architecture-diagram.svg`** — proper architecture diagram (today's is ASCII art in `architecture.md`). Defer to Phase 5 polish.

Phase-gate discipline applies here too — don't write docs ahead of the actual content the doc would describe.

## Conventions

- Every doc has a clear status (working draft / skeleton / authoritative). Read the front matter.
- Every doc references its sources (papers, standards, upstream repos) at the bottom.
- No invented numbers anywhere. "TBD — awaiting evaluation run" is acceptable; an invented "1 in a million" is not. See `CLAUDE.md` honesty conventions.
