# TANIK Roadmap

This document defines **what "done" means** for each phase of the project. Phases ship before the next one starts. If something feels like it belongs to a later phase, it goes in `BACKLOG.md` — it does not get silently absorbed into the current phase.

This is a discipline document as much as a planning document. The failure mode for this project is not running out of ideas; it is scope creep killing momentum before anything ships.

---

## Phase 0 — Spike

**Goal:** Prove the iris pipeline runs on my machine and I understand what it does.

**Scope:** A single Jupyter notebook.

**Deliverables:**
- `notebooks/00_iris_spike.ipynb` — loads a sample iris image, runs the full Worldcoin `open-iris` pipeline, visualizes each intermediate stage (segmentation mask, normalized iris, iris code), and computes Hamming distances for same-eye and different-eye pairs.
- `notebooks/README.md` — how to obtain a sample iris dataset legally, how to run the notebook.

**Definition of done:**
- Notebook runs top-to-bottom with no manual intervention on a fresh conda env.
- Same-eye Hamming distances are visibly lower than different-eye distances on a minimum of 10 sample pairs.
- I can explain what an iris code is, what Hamming distance means in this context, and why the distribution of same-eye vs different-eye distances matters — in my own words, without looking it up.

**Out of scope:** Any web stack, any backend, any fingerprint work, any UI.

**Estimated effort:** 1 weekend.

---

## Phase 1 — Iris backend + minimal client

**Goal:** End-to-end iris enrollment and verification through a real web stack, deployed somewhere public.

**Scope:**
- FastAPI inference node with `POST /api/v1/iris/enroll` and `POST /api/v1/iris/verify`.
- Next.js client with two flows: Enroll (capture or upload, name the user) and Verify (capture or upload, see match score).
- SQLite storage for enrolled iris templates. No raw image persistence.
- Pydantic-strict request validation; `run_in_threadpool` for the ML work; `opencv-python-headless` in requirements.
- Zustand state machine with explicit states (`IDLE | CAPTURING | UPLOADING | PROCESSING | SUCCESS | FAILED`).
- Multi-stage Dockerfiles for both services; `docker-compose.yml` with an internal bridge network.
- `docs/sequence-flow.md` (Mermaid) — first version, iris-only.
- `docs/api-contract.md` — first version, iris-only.
- `docs/development.md` — first version.

**Definition of done:**
- `docker compose up --build` starts both services with no manual steps.
- A user can enroll via the UI and then verify against their enrollment, seeing a match score, in under 10 seconds end-to-end.
- A different person's iris image verified against the first user's enrollment produces a clearly non-matching score.
- CI runs the backend unit tests on every push (GitHub Actions).
- README and the three docs above are committed and accurate.
- Deployed to a reachable URL (Railway, Fly, or a cheap VPS).

**Out of scope:** Fingerprint, fusion, liveness, admin dashboard, threshold tuning UI, ROC curves.

**Estimated effort:** 2-3 weekends at ~20 hrs/week.

---

## Phase 2 — Fingerprint modality

**Goal:** Add fingerprint as a second modality, sharing the architectural spine.

**Scope:**
- SourceAFIS integration in the inference node.
- `POST /api/v1/fingerprint/enroll` and `POST /api/v1/fingerprint/verify`.
- A shared `BiometricEngine` interface in the Python code so iris and fingerprint expose the same contract from the service's perspective.
- Client UI extended with a fingerprint upload/capture flow.
- Public fingerprint dataset sourced and documented in `docs/datasets.md`.
- `docs/api-contract.md` extended with fingerprint endpoints.

**Definition of done:**
- Fingerprint enrollment and verification work independently of iris, through the UI.
- Same-finger vs different-finger pairs produce correctly separated scores on a sample from the chosen public dataset.
- The `BiometricEngine` interface is used by both modalities; adding a third (theoretically) would not require touching the API layer.

**Out of scope:** Fusion. The two modalities work independently at this phase; combining them is Phase 3.

**Estimated effort:** 2-3 weekends.

---

## Phase 3 — Fusion, thresholds, honest metrics

**Goal:** Move from "two working modalities" to "one fused decision, with real numbers."

**Scope:**
- A unified `POST /api/v1/verify` endpoint that accepts both modalities and returns a fused decision.
- Score normalization: Hamming distance → [0,1], SourceAFIS similarity → [0,1]. Documented in `docs/fusion.md`.
- Weighted-sum fusion with weights tuned on a held-out calibration set, not guessed. The calibration methodology and the resulting weights go in `docs/fusion.md`.
- `tests/evaluation/` scripts that compute FAR, FRR, and an ROC curve on a held-out test set. Output to `docs/performance.md`.
- Client UI: threshold slider that re-runs the decision live, showing how FAR and FRR move together.

**Definition of done:**
- `docs/performance.md` contains measured FAR and FRR for iris alone, fingerprint alone, and fused — with the test set size and composition documented.
- An ROC curve image is checked into the repo and referenced from the README.
- The threshold slider in the UI, when moved, visibly trades off false accepts vs false rejects in real time on the test set.
- No hand-written magic numbers anywhere in the repo — every threshold and weight has a source in `docs/fusion.md` or `docs/performance.md`.

**Out of scope:** Liveness, admin dashboard.

**Estimated effort:** 2 weekends.

---

## Phase 4 — Liveness (presentation attack detection) + admin

**Goal:** Add the gate that separates toy demos from real biometric systems, and the operator surface that a real kiosk would need.

**Scope:**
- A PAD module that runs before the biometric pipeline. For v1, honestly scope what this is: a basic printed-photo / replay-video detector trained on a public PAD dataset, or an integration with an existing PAD model. The limitations go in `docs/pad.md` in plain language — no overclaiming.
- Failsafe rule: if the PAD score is below a documented threshold, the biometric pipeline does not run, and the API returns a structured rejection with `error_code: "PAD_FAILURE"`.
- Admin dashboard: enrollment count, recent verification attempts with timestamps and outcomes, aggregate quality and liveness scores.
- `docs/pad.md` — what v1 detects, what it doesn't, what real iris-PAD and fingerprint-PAD would require.
- `docs/threat-model.md` — first complete version, including the replay-attack roadmap.
- `docs/privacy.md` — KVKK/GDPR handling, template-vs-image distinction, retention, access logging.

**Definition of done:**
- A printed photo of an enrolled user's iris is rejected at the PAD gate, not at the biometric gate.
- The admin dashboard shows at least: total enrollments, total verification attempts, success rate, median liveness score, median quality score.
- All four docs above are committed and internally consistent with the code.

**Out of scope:** Challenge-response liveness (blink, head turn) — that's v2.

**Estimated effort:** 2 weekends.

---

## Phase 5 — Polish and release

**Goal:** Make this findable, readable, and credible to a stranger.

**Scope:**
- A landing page (can be Vercel-hosted, separate from the app) explaining what TANIK is and linking to the demo and repo.
- A technical blog post walking through the architecture and the fusion methodology, with the measured numbers from `docs/performance.md`.
- Posted to dev.to, Hacker News, Turkish tech LinkedIn groups, relevant subreddits.
- Repo pinned on GitHub profile, linked from LinkedIn and CV.
- Targeted outreach: a short, peer-to-peer message to an engineer at Proline asking for technical feedback. Not before this phase is complete. Not to recruiters, not to HR, not as a job pitch.

**Definition of done:**
- Landing page live.
- Blog post published and shared on at least three platforms.
- At least one conversation — via GitHub issues, email, or LinkedIn — with someone working in biometrics, about the project, not about a job.

**Estimated effort:** 2 weekends.

---

## Things explicitly deferred to a theoretical v2 or later

Kept here so they are acknowledged and therefore no longer tempting to sneak into earlier phases.

### Smaller deferrals

- Face recognition as a third modality
- Challenge-response liveness (blink, head turn, smile)
- True iris-PAD using near-infrared hardware features
- Hardware integration with real fingerprint scanners (Suprema, DigitalPersona, etc.)
- Proper HSM-backed template encryption
- Multi-tenant admin, RBAC, audit logging for enterprise
- On-device inference for edge deployments
- Training a custom iris segmentation model
- Contributing upstream to `worldcoin/open-iris`

### Larger deferrals — potential v2 product directions

#### Mobile-phone-as-reader access control

Instead of a kiosk with its own biometric hardware, the user presents their phone to a door, gate, or lock. The phone uses its native secure biometric (Face ID on iOS, BiometricPrompt on Android) to unlock a private key stored in the phone's secure enclave; that key signs a challenge issued by the lock over Bluetooth LE; the lock verifies the signature and opens.

Why this is a distinct product, not a feature:

- Different customer (end consumer / property managers vs. government and enterprise identity buyers).
- Different threat model (decentralized per-device keys vs. centralized server-side templates).
- Different stack (native iOS/Android + BLE firmware vs. web kiosk + backend).
- Different go-to-market (hardware SKU + app vs. platform integration).

Why it's worth preserving the idea anyway:

- The Turkish market has no dominant player in phone-based smart access control; international options (Latch, August, HID Mobile Access) have limited local presence.
- A co-founder with CNC manufacturing capability is already in the picture from an earlier project context, which changes the economics of producing the lock hardware.
- TANIK's server-side fusion and threat-model work transfers conceptually, even if little code does.

Critical technical notes to not forget when revisiting:

- A browser-based (website / PWA) face scan is not viable as the authentication step — there is no hardware attestation that the camera stream is a live person rather than replayed media. Must be a native app using platform biometric APIs.
- The phone's Face ID or fingerprint should unlock the signing key, not be transmitted. The biometric never leaves the secure enclave. This is the same model as FIDO2/WebAuthn and Apple Home Key.
- BLE messages must be challenge-response with a fresh nonce per attempt to resist replay. A $30 BLE sniffer defeats any protocol that doesn't do this.
- Multi-factor by construction: something-you-have (the enrolled phone) plus something-you-are (the biometric that unlocks the enclave).

If this is ever pursued, it is a ground-up new project — it does not extend kiosk TANIK incrementally.

#### Mobile PWA companion to the kiosk

A narrower, more defensible extension: a PWA that pairs with a deployed TANIK kiosk for administrative functions (remote enrollment initiation, viewing one's own access history, admin dashboard on mobile). No biometric authentication done on the phone itself — the phone is just a management surface. This would be a plausible genuine v2 of TANIK, as opposed to the phone-as-reader concept above which is a different product.

---

None of the items in this section are bad ideas. All of them are v2. They do not justify delaying earlier phases.

---

## Current status

**Phase:** 0 (not started)

**Next action:** Set up conda env, obtain a sample iris dataset, scaffold `notebooks/00_iris_spike.ipynb`.
