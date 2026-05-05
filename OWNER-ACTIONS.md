# OWNER ACTIONS — Things only Ayberk can do

The list of TANIK tasks that **require you, the human owner**, and which Claude cannot do. Each entry lists what's blocked, why it needs you specifically, and the smallest next step.

When you complete an item, move it to the **Done** section at the bottom and note the date. When something new lands here, add it to the **Pending** list with the same shape.

---

## Pending

### 1. `#11` Acquire a research-grade iris dataset for evaluation

The previous framing assumed ND-IRIS-0405 was the target. Two discoveries on 2026-04-26 reshaped this:

1. ND-CVRL's license has a hard institutional-signature wall (no individuals, no Gmail) — not navigable solo.
2. CASIA's website (`biometrics.idealtest.org`) is intermittently unreachable from multiple networks.
3. **The IEEE Biometrics Council resources page <https://ieee-biometrics.org/resources/biometric-databases/ocular-iris-periocular/> lists a much better-fit option: the PolyU Cross-Spectral Iris Database hosted by Ajay Kumar at Hong Kong PolyU.** Web-form application, no institutional gate, NIR + visible (paired), 12,540 images from 209 subjects. Genuinely accessible to solo independent authors; Prof. Kumar has historically been supportive of open-source projects.

**The plan is now PolyU-primary, with three honest-ask backups already drafted.**

**1a. PolyU Cross-Spectral (primary).** Read `docs/polyu-iris-access.md`. Open the application form at <http://www4.comp.polyu.edu.hk/~csajaykr/myhome/database_request/polyuiris/>. Paste the field text from `docs/outreach/polyu-iris-request.md`. Submit. Reported response time: a few days. **Estimated effort: 10 minutes.**

**1b. ND-CVRL honest-ask (parallel, sent — awaiting reply).** Email at `docs/outreach/nd-iris-independent-author.md`. Asks whether ND-CVRL has any path for unaffiliated authors. Worst case "no" → costs nothing; best case unblocks the largest NIR iris dataset.

**1c. CASIA when the site becomes reachable.** Draft is ready at `docs/outreach/casia-iris-request.md`. Try the URL `biometrics.idealtest.org` periodically; if/when reachable, send.

**1d. IIT Delhi Iris (smaller, visible-only) and UBIRIS.v2 (no-gate, visible-only).** Documented as further fallbacks in `docs/polyu-iris-access.md`. Only pursue if PolyU refuses — extremely unlikely.

- **Why it's load-bearing.** Phase 3 `#42` and `#43` are both blocked on this. Until a research-grade iris dataset is in hand, `docs/performance.md` cannot ship measured numbers and the unified `/api/v1/verify` endpoint stays at `calibration_status: "placeholder"`.
- **Related files.** `docs/polyu-iris-access.md` (primary path), `docs/outreach/polyu-iris-request.md` (form-field text), `docs/casia-iris-access.md` (CASIA backup), `docs/nd-iris-0405-access.md` (institutional wall, documented), the four outreach email drafts.

### 2. `#11-fingerprint` Acquire an FVC-style fingerprint dataset

- **Why this needs you.** Same shape as item 1 — license verification at acquisition time, possibly an institutional licensee. The specific candidate is FVC2002 / FVC2004 DB1_B (10 fingers × 8 impressions each). The original FVC website is no longer authoritative; sourcing must verify the licence wording at acquisition time.
- **Why it's load-bearing.** MINEX III (currently in use for Phase 2 tests) has only one impression per finger, so it cannot produce same-finger genuine pairs. Without an FVC-style set, the Phase 3 `#43` evaluation harness can compute the iris half but not the fingerprint half.
- **Smallest next step.** Search current academic mirrors for "FVC2002 DB1_B" or "FVC2004 DB1_B" with their licence terms attached. Bologna University's biometric systems lab is the historical source; check whether they still distribute or have pointed at a successor. Alternative: NIST SD27 (latent prints) is a different shape but available in the U.S. public domain.
- **Estimated effort.** Hours of research + correspondence.
- **Related files.** `BACKLOG.md` ("Fingerprint dataset gap for Phase 3 — same-finger pairs"), `docs/datasets.md`.

### 3. `#33` Phase 1 DoD walkthrough — enrol + verify with your own face

- **Why this needs you.** Literally requires your real iris in front of a webcam. Claude cannot capture biometric data.
- **Why it's load-bearing.** It is the Phase 1 definition of done. Until walked through end-to-end in a real browser, Phase 1 is "implementation complete, DoD unverified" rather than "shipped."
- **Pivoted to local-first dev** at the end of the 2026-04-27 session. Walking through against the deployed Render free-tier was producing 30+ second cold-starts and surfacing two real bugs (camera reset on keystroke; cryptic AbortError on enroll); both shipped in `7034aac`. Local-first is faster and equally good evidence for DoD.
- **Smallest next step (two terminals):**

  ```bash
  # Terminal 1 — backend
  cd /Users/ayberkbaytok/tanik && \
    TANIK_CORS_ALLOW_ORIGINS=http://localhost:3000 \
    /Users/ayberkbaytok/tanik/.venv/bin/uvicorn \
    --app-dir apps/inference \
    tanik_inference.main:app --reload --port 8000

  # Terminal 2 — client
  cd /Users/ayberkbaytok/tanik/apps/client && \
    NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 \
    npm run dev
  ```

  Visit <http://localhost:3000>. Status pill should be green; the amber "fusion calibration: placeholder" hint should also be visible. Click **Enroll iris**, type a display name (camera should now stay live — bug fix `7034aac`), capture, submit. Screenshot the success panel. Then **Verify iris**, paste the `subject_id`, capture again — Hamming distance should be well under 0.37.
- **Estimated effort.** Five minutes once the terminals are up.
- **Walking through the deployed URL instead** is also fine now that the bug fixes are auto-deployed; just live with the 30 s cold-start on the first request.

### 4. (Optional but valuable) Read what's been built

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

### 2026-04-26 — `#32` Deployed TANIK to public URLs

- **Client (Vercel):** <https://tanik.vercel.app>
- **Inference (Render):** <https://tanik.onrender.com> (health: `/api/v1/health`)

Required configuration in place:

| Service | Env var | Value | Why |
|---|---|---|---|
| Render | `TANIK_CORS_ALLOW_ORIGINS` | `https://tanik.vercel.app` (no trailing slash) | Browser CORS — without this the client cannot call the API |
| Vercel | `NEXT_PUBLIC_API_BASE_URL` | `https://tanik.onrender.com` | Baked into the client bundle at build time |
| Vercel | Root Directory | `apps/client` | The Next.js app is in this subdirectory |
| Vercel | Framework Preset | Next.js | Otherwise Vercel falls back to static-site mode and 404s |

Known free-tier trade-offs:
- Render sleeps after 15 min of inactivity. First request after sleep ≈ 30 s.
- Render free tier filesystem is ephemeral. SQLite at `/data/tanik.db` resets on every redeploy. For production: swap to Postgres.
- `next.config.ts` reads `BUILD_STANDALONE=true` to enable `.next/standalone/`; Docker sets it, Vercel leaves it unset. Without this gate, Vercel returned 404 NOT_FOUND on every route (fix in `a1c0b0c`).

Re-deploy from `main`: both platforms have GitHub auto-deploy on the default branch.

---

## Conventions

- **One file, one purpose.** This file is *only* for things that need the human owner. Engineering tasks Claude can do live in the in-session task list (TaskCreate) and in `ROADMAP.md`'s phase definitions.
- **Smallest next step beats long descriptions.** Each entry should let you start without re-reading the whole repo.
- **No invented urgencies.** Items are listed in dependency order, not in panic order.
- **When in doubt, mark blocked.** If an item is blocked on something *you* can do, that's a separate item. Make the dependency explicit so no one waits on the wrong thing.
