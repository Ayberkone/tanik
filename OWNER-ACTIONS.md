# OWNER ACTIONS — Things only Ayberk can do

The list of TANIK tasks that **require you, the human owner**, and which Claude cannot do. Each entry lists what's blocked, why it needs you specifically, and the smallest next step.

When you complete an item, move it to the **Done** section at the bottom and note the date. When something new lands here, add it to the **Pending** list with the same shape.

---

## Pending

### 1. `#11` Execute the ND-IRIS-0405 license agreement

- **Why this needs you, not Claude.** Requires (a) an institutional point of contact with contracting authority, (b) submission from an institutional email address (cvrl@nd.edu does not accept Gmail/Yahoo), (c) a signed legal document. Claude cannot do any of these.
- **Why it's load-bearing.** Phase 3 `#42` (threshold-slider UI) and `#43` (FAR/FRR/ROC harness) are both blocked on this. Without it, `docs/performance.md` cannot ship measured numbers and the unified `/api/v1/verify` endpoint stays at `calibration_status: "placeholder"` forever.
- **Smallest next step.** Read `docs/nd-iris-0405-access.md` end-to-end — it's the step-by-step. The first decision is **who signs**: independent-researcher route (email Adam at `cvrl@nd.edu` first to ask about the path for unaffiliated open-source authors) vs. institutional route (find a Turkish university research group or Proline R&D legal contact willing to be the named licensee). Adam already replied once (2026-04-25) and gave the access pointer; this is the natural follow-up.
- **Estimated effort.** Hours of human time; weeks of calendar time waiting for institutional signatures and ND-CVRL review.
- **Related files.** `docs/nd-iris-0405-access.md`, `docs/outreach/nd-iris-request.md`, `docs/outreach/nd-iris-thanks.md`.

### 2. `#11-fingerprint` Acquire an FVC-style fingerprint dataset

- **Why this needs you.** Same shape as item 1 — license verification at acquisition time, possibly an institutional licensee. The specific candidate is FVC2002 / FVC2004 DB1_B (10 fingers × 8 impressions each). The original FVC website is no longer authoritative; sourcing must verify the licence wording at acquisition time.
- **Why it's load-bearing.** MINEX III (currently in use for Phase 2 tests) has only one impression per finger, so it cannot produce same-finger genuine pairs. Without an FVC-style set, the Phase 3 `#43` evaluation harness can compute the iris half but not the fingerprint half.
- **Smallest next step.** Search current academic mirrors for "FVC2002 DB1_B" or "FVC2004 DB1_B" with their licence terms attached. Bologna University's biometric systems lab is the historical source; check whether they still distribute or have pointed at a successor. Alternative: NIST SD27 (latent prints) is a different shape but available in the U.S. public domain.
- **Estimated effort.** Hours of research + correspondence.
- **Related files.** `BACKLOG.md` ("Fingerprint dataset gap for Phase 3 — same-finger pairs"), `docs/datasets.md`.

### 3. `#32` Deploy TANIK to a public URL

- **Why this needs you, not Claude.** Requires you to create accounts at the target hosts (Vercel for the client, Railway / Fly / a cheap VPS for the backend), to add billing details, and to plug in environment variables that include real (non-localhost) URLs. Claude cannot create accounts on your behalf.
- **Why it's load-bearing.** Phase 1 `#33` (DoD walkthrough) cannot happen without a public URL; the entire project being externally reachable depends on this; the Proline pitch is much more impactful if "look at the code" is accompanied by "click here and try it."
- **Smallest next step.** Pick the split. Recommended: **Vercel** for the client (the project is Next.js-native, Vercel build is one click), **Railway** for the backend (supports the Java + Python combo via a Dockerfile cleanly, persistent volume available for SQLite). Sign up for both; create a Vercel project pointing at this repo's `apps/client/` directory; create a Railway service from the `apps/inference/Dockerfile`. Plug in `NEXT_PUBLIC_API_BASE_URL` on Vercel pointing at the Railway URL once both are up.
- **Estimated effort.** A few hours, mostly waiting for the first Docker build on Railway and configuring CORS/environment plumbing.
- **Related files.** `apps/inference/Dockerfile`, `apps/client/Dockerfile`, `docker-compose.yml`, `docs/development.md`.

### 4. `#33` Phase 1 DoD walkthrough — enrol + verify with your own face

- **Why this needs you.** Literally requires your real iris in front of a webcam. Claude cannot capture biometric data.
- **Why it's load-bearing.** It is the Phase 1 definition of done. Until walked through end-to-end in a real browser, Phase 1 is "implementation complete, DoD unverified" rather than "shipped."
- **Smallest next step.** After `#32` is up: open the deployed client URL in a browser, enroll your own iris under a display name, then go to verify and confirm the matched score is sensible (HD < 0.37, well under the threshold). If it works on the first try, take a screenshot for the README; if it doesn't, the failure mode is itself useful information.
- **Estimated effort.** Five minutes once the deploy is up.

### 5. (Optional but valuable) Read what's been built

- **Why this is here.** You said "i cannot catch up with you." The only way that catches up is reading the docs that already exist, end-to-end.
- **Smallest next step (in order).**
  1. `docs/architecture.md` — top-to-bottom system walkthrough. Sections 1+2+3+8 are the 5-minute version.
  2. `docs/fusion.md` — the actually-interesting Phase 3 piece (score normalisation + weighted-sum fusion).
  3. `docs/blog-post-draft.md` — same content as architecture but reshaped for an outward-facing tech blog.
  4. `docs/threat-model.md` and `docs/privacy.md` — Proline-relevant honesty discipline.
  5. `ROADMAP.md` "Current status" — the catalogue of what's shipped vs. pending.
- **Estimated effort.** Two hours of focused reading. Doesn't have to be in one sitting.

---

## Done

*(Move items here when complete. Format: `### [date completed] — title` plus a one-line note on what was done.)*

*(Empty — first entry will land when you complete one of the above.)*

---

## Conventions

- **One file, one purpose.** This file is *only* for things that need the human owner. Engineering tasks Claude can do live in the in-session task list (TaskCreate) and in `ROADMAP.md`'s phase definitions.
- **Smallest next step beats long descriptions.** Each entry should let you start without re-reading the whole repo.
- **No invented urgencies.** Items are listed in dependency order, not in panic order.
- **When in doubt, mark blocked.** If an item is blocked on something *you* can do, that's a separate item. Make the dependency explicit so no one waits on the wrong thing.
