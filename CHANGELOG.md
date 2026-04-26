# Changelog

All notable changes to TANIK go here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres roughly to [Semantic Versioning](https://semver.org/) at the per-phase level — there is no formal release cadence yet, so the sections below are organised by **roadmap phase** rather than by version tag.

The first tagged release will land at the end of Phase 5.

---

## [Unreleased]

### Added — Phase 3 (in progress)

- **Unified `POST /api/v1/verify` endpoint** ([cc48ace](https://github.com/Ayberkone/tanik/commit/cc48ace), task #41). Accepts iris and/or fingerprint in a single multipart upload; returns one fused decision plus a per-modality breakdown. Backed by:
  - `tanik_inference/fusion.py` — pure normalisation + weighted-sum fusion. Piecewise-linear normalisation anchored at each modality's per-modality threshold (engine-native threshold maps to normalised `0.5`).
  - Configurable knobs via env (`TANIK_FUSION_*`, `TANIK_IRIS_HD_*`, `TANIK_FINGERPRINT_SCORE_CEIL`).
  - In-band `calibration_status: "placeholder"` honesty signal until task #43 ships measured weights.
- **`docs/fusion.md`** — methodology, the choice between min-max / z-score / piecewise-linear, the renormalisation scheme over present modalities, the placeholder caveat, and references (Ross & Jain 2003 score-level fusion taxonomy).
- **`docs/architecture.md`** — top-to-bottom system walkthrough; doubles as Proline-presentation material.
- **`docs/nd-iris-0405-access.md`** — step-by-step license-execution checklist for the Phase 3 iris dataset (task #11).
- **`CHANGELOG.md`** (this file) — backfilled from git history.
- 18 new unit tests in `tests/test_fusion.py` (anchor points, monotonicity, clamping, fusion identities) + 9 integration tests in `tests/test_unified_verify.py` (iris-only, fingerprint-only, both, impostor pair, half-supplied request, cross-modality `subject_id` 404, calibration-status surfacing). Backend: 39 + 22 tests pass on CI.

### Added — Phase 3 dataset prep

- **`docs/performance.md`** (skeleton) — locks the structure of the FAR/FRR/ROC report ahead of `#11` (ND-IRIS-0405) + the FVC-style fingerprint dataset landing. Every numeric cell is `TBD`; the harness in `tests/evaluation/` (`#43`) writes them when the data is available. Includes the explicit honesty pledge that no number in the document has ever been hand-typed.
- Outreach: `docs/outreach/nd-iris-request.md` repo URL placeholder filled in (repo is now public).

### Added — Phase 4 prep documentation (Phase 3 in-flight)

- **`docs/threat-model.md`** (working draft) — scope, attacker model, asset inventory, attack surface, and a concrete attack-by-attack table with current mitigations and gaps. Honest about what TANIK defends and what it doesn't (presentation attack, replay, template theft, template inversion, DoS, side-channels, image-decoder vulnerabilities). Maps gaps to specific Phase 4 work and to ISO/IEC 19795 / 24745 / 30107.
- **`docs/privacy.md`** (working draft) — KVKK + GDPR + EU AI Act posture. Per-data-category inventory of what's stored, where, and for how long. Calls out that templates *are* personal data ("zero-knowledge" is the wrong phrase); enumerates the gaps (consent UI, retention period, subject access portal, encryption at rest) and where they get closed.
- **`docs/pad.md`** (skeleton) — Phase 4 presentation-attack-detection plan. ISO/IEC 30107 framework (APCER/BPCER), candidate datasets (NDIris3D, CASIA-Iris-Fake, LivDet-Iris/Fingerprint), candidate approaches (heuristics → small CNN → vision foundation model). Honest about what software-only PAD cannot defend against (NIR replay, patterned contact lenses, high-quality silicone spoofs). API surface for `PAD_FAILURE` is now spec'd ahead of implementation.
- **`docs/admin-api.md`** (skeleton) — Phase 4 operator-facing API. Six endpoints under `/api/v1/admin/*` (health, subjects list/detail/delete, verifications, metrics, configuration). OIDC against deploying-org IdP; one role (`operator`); restart-required for configuration mutations by design. Audit log written for every mutating action with operator identity + reason. Honest gap list at the bottom (template export, bulk operations, webhooks — all left to Phase 4 implementation pass).
- **`docs/admin-dashboard.md`** (skeleton) — Phase 4 operator-facing UI. Five pages (overview, subjects, verifications, configuration, audit log) inside the same Next.js app at `/admin/*`. Read-mostly; deletion is the only mutation. Calibration callout when `placeholder` is the active fusion status. Same Next.js app rather than a separate one (cheaper share of theme + components; easy to split later if needed).

### Added — Phase 5 prep

- **`docs/blog-post-draft.md`** — full-length tech-blog draft reshaping `docs/architecture.md` for a non-academic biometric-engineer audience. Conversational tone, code snippets, "the interesting twist" framing on the calibration_status placeholder signal. Three suggested titles; "what I'd love feedback on" section ending with three concrete questions for biometric-industry readers. Publishable when the author is ready (with or without measured numbers).
- **`docs/proline-pitch-deck.md`** — Marp-compatible 20-slide deck for a 15-20 minute technical talk to biometric-industry engineers. Renders to PDF/HTML/PPTX via `npx @marp-team/marp-cli`. Speaker notes embedded in HTML comments. Closes the user's "I want presentation material for Proline" request alongside the long-form `architecture.md` and the article-form `blog-post-draft.md`.
- **`docs/glossary.md`** — biometrics vocabulary reference (modalities, iris-specific terms, fingerprint-specific terms, performance metrics, architecture concepts, standards bodies, privacy regulation, TANIK-specific honesty discipline). Doubles as Proline-conversation anchor.
- **`docs/comparison.md`** — honest positioning of TANIK against (a) commercial vendors (Suprema, IDEMIA, NEC), (b) other open-source iris (CVRL OpenSourceIrisRecognition / TripletIris + ArcIris), (c) other open-source fingerprint (NIST NBIS, OpenBR, MCC research code), (d) face-recognition-only systems (and why TANIK doesn't compete there). Sets up the post-Phase-3 comparative study against TripletIris + ArcIris as the project's most valuable single publishable artefact.

### Added — Owner-side checklist

- **`OWNER-ACTIONS.md`** (root-level) — consolidates the tasks Claude cannot do (institutional license signatures, account creation, real-face DoD walkthrough, dataset acquisition) into one checklist with "smallest next step" framing. Five pending items; empty Done section ready to grow.

### Changed — Phase 3 iris-dataset plan revised again (PolyU primary)

User found the IEEE Biometrics Council resources page <https://ieee-biometrics.org/resources/biometric-databases/ocular-iris-periocular/> while CASIA's site was unreachable. The page surfaces the **PolyU Cross-Spectral Iris Database** hosted by Ajay Kumar at Hong Kong PolyU — web-form application, no institutional gate, **NIR + visible (paired)**, 12,540 images from 209 subjects. Strictly better fit for an unaffiliated solo author than ND-IRIS-0405 or CASIA, and the bi-spectral nature opens follow-up cross-spectral evaluation paths.

New files:
- `docs/polyu-iris-access.md` — primary access guide; comparison table of all five candidate iris datasets surfaced through this exploration; license terms (no commercial use; no redistribution; cite Ramaiah & Kumar 2017) documented and verified compatible with TANIK's MIT-licensed open-source posture.
- `docs/outreach/polyu-iris-request.md` — exact form-field text to paste into the PolyU web form. Independent-researcher affiliation stated honestly; intended-use paragraph specifically lists FAR/FRR/EER plus the optional cross-spectral follow-up; redistribution and citation handling explicit.

`OWNER-ACTIONS.md` item 1 rewritten as a four-tier plan: PolyU primary, ND-CVRL honest-ask parallel (already sent by user), CASIA when reachable, IIT Delhi / UBIRIS as further fallbacks. Previous CASIA-primary framing was correct given the information available at the time but is now superseded by the PolyU discovery.

### Changed — Phase 3 iris-dataset plan revised (CASIA primary, superseded)

User-feedback driven: the original `#11` framing assumed the ND-IRIS-0405 license could be navigated. Reading the license carefully showed a hard institutional-signature wall (no students, no postdocs, no non-delegated faculty, no Gmail submissions) — as a solo independent author this is a wall, not a friction point.

New plan (later superseded by PolyU discovery — see entry above):

- **Primary: CASIA-Iris-V4.** Application-based but individuals are eligible in practice. New `docs/casia-iris-access.md` (the access guide) and `docs/outreach/casia-iris-request.md` (a ready-to-adapt application email).
- **Parallel honest-ask: ND-CVRL.** New `docs/outreach/nd-iris-independent-author.md` puts the question to `cvrl@nd.edu` plainly — does ND-CVRL have any path for unaffiliated open-source authors, or is the institutional wall hard? Ask once cleanly; the answer (likely "no") informs whether to chase institutional sponsorship or stay on CASIA.
- **No-gate fallback: UBIRIS.v2.** If both CASIA and ND-CVRL refuse, UBIRIS registration is open. Visible-light captures rather than NIR — documented trade-off.

`OWNER-ACTIONS.md` rewritten under item 1 to reflect the three-way ask. `docs/nd-iris-0405-access.md` opens with a status note flagging the institutional wall and pointing readers at the CASIA primary path.

### Changed — audit-driven consistency pass

- **Health endpoint extended.** `GET /api/v1/health` now returns `fingerprint_engine` (e.g. `"sourceafis/3.18.1"`) and `calibration_status` (`"placeholder"` today) alongside the existing `iris_engine` + `version`. JVM startup is *not* triggered by `/health` — the version string comes from a module constant. Contract + client `Health` type updated to match. A monitoring system polling `/health` can now flag deployments still on placeholder calibration without parsing the unified-verify response.
- **Home page surfaces calibration-placeholder.** The status pill now shows both engine versions and renders an amber "fusion calibration: placeholder" line when the backend reports `placeholder`. The honest in-band signal is now visible at the kiosk's top-level surface, not buried in the API response.
- **`docs/architecture.md` file-map sync.** Several Phase 4 prep docs were marked as "arrives in Phase 4" but had already shipped this session. Tree updated and reordered to match `docs/README.md`'s grouping.
- **`README.md` threat-model wording.** Said "the full threat model document arrives in Phase 4" — corrected to reflect that the working draft now exists and will be revised through Phase 4.

### Notes

- `#42` (threshold-slider UI) and `#43` (FAR/FRR/ROC harness) remain blocked on dataset acquisition (`#11`). Until then, `calibration_status` in unified-verify responses stays `"placeholder"`.
- Phase 4 prep docs are written ahead of Phase 4 implementation deliberately, to give Proline-presentation material immediately and to lock the framework in. They are explicitly marked as drafts/skeletons; the implementation pass in Phase 4 will revise them against the chosen PAD model and admin surface.

---

## Phase 2 — Fingerprint modality (shipped 2026-04-25, CI-verified 2026-04-25 → 2026-04-26)

### Added

- **SourceAFIS via JPype** ([944aaa2](https://github.com/Ayberkone/tanik/commit/944aaa2), task #34). In-process JVM, vendored `sourceafis-3.18.1.jar`, threadpool-offloaded `encode` + `match`. Mirrors `iris_engine`'s shape so adding fingerprint to the rest of the stack is a clean swap.
- **`BiometricEngine` Protocol** ([2bbf3e1](https://github.com/Ayberkone/tanik/commit/2bbf3e1), task #36). `runtime_checkable` contract with `name`, `template_version()`, `encode()`, `match()`. Storage refactored to be modality-agnostic — `subjects` table now carries `(modality, template_bytes, metadata_json)` instead of iris-shaped fields.
- **NIST MINEX III as fingerprint test fixture** ([4005a87](https://github.com/Ayberkone/tanik/commit/4005a87), `docs/datasets.md`, task #5). U.S. public domain validation imagery; six images across two subjects; downloaded into the gitignored fixture cache and transcoded raw `.gray` → PNG in `conftest.py`.
- **FingerprintEngine + discrimination tests** ([5711c86](https://github.com/Ayberkone/tanik/commit/5711c86), task #37). Self-match scores well above SourceAFIS's documented 40 (FMR=0.01%); three parametrised cross-subject pairs all score below it.
- **`/api/v1/fingerprint/{enroll,verify}` endpoints** ([daf9e48](https://github.com/Ayberkone/tanik/commit/daf9e48), task #38). Separate `FingerprintEnrollResponse` / `FingerprintVerifyResponse` schemas, `finger_position` enum, env-driven threshold (default `40.0`), cross-modality lookup → `404 SUBJECT_NOT_FOUND`, contract documented in `docs/api-contract.md`. Seven new endpoint tests.
- **Client UI for fingerprint** ([2b0eed0](https://github.com/Ayberkone/tanik/commit/2b0eed0), task #9). Separate `/fingerprint/{enroll,verify}` pages (upload-only — webcam capture not feasible for fingerprints). Home page restructured to a 4-card grid. `EnrollResult` / `VerifyResult` are now discriminated unions; pages narrow by modality. Five new Playwright tests; existing 10 still green.

### Fixed / Changed

- **Backend CI surfaces pytest failures publicly** ([ba85e81](https://github.com/Ayberkone/tanik/commit/ba85e81)). Promotes pytest failures to `::error::` workflow annotations readable via the public `check-runs/{id}/annotations` endpoint without GitHub auth — useful when the user is away and Claude needs to debug remotely.
- **JPype `convertStrings=False` flag dropped.** It worked locally but caused the first CI failure; let JPype's default win. Bytes inputs to `JArray(JByte)` are now wrapped in explicit `bytes(...)` to remove memoryview/bytearray ambiguity at the FFI boundary.

### Notes

- Phase 2 was started with Phase 1 `#32` (deploy) + `#33` (DoD walkthrough) still open — a deliberate exception the author signed off on (deploy paused on author's decision, not a technical blocker). Phase 2 itself is closed against ROADMAP's stated DoD modulo the FVC same-finger-pair gap (BACKLOG entry).

---

## Phase 1 — Iris backend + minimal client (shipped implementation 2026-04-25; deploy deferred)

### Added

- **FastAPI inference service** with `/health`, `/api/v1/iris/{enroll,verify}` ([d5002fa](https://github.com/Ayberkone/tanik/commit/d5002fa), [d0800ee](https://github.com/Ayberkone/tanik/commit/d0800ee)). Pydantic-strict request models, magic-byte upload validation, threadpool-offloaded iris pipeline, structured request logging.
- **Next.js 16 client** ([2159a7d](https://github.com/Ayberkone/tanik/commit/2159a7d), [8af05be](https://github.com/Ayberkone/tanik/commit/8af05be), [33f54bc](https://github.com/Ayberkone/tanik/commit/33f54bc)). App Router, React 19, TypeScript strict, Tailwind 4, shadcn/ui (`base-nova`), Zustand 5. Capture state machine with explicit transitions; webcam component with strict `getUserMedia` cleanup; enroll + verify pages.
- **End-to-end test suites + GitHub Actions CI** ([e473cf0](https://github.com/Ayberkone/tanik/commit/e473cf0), [7e8e4e8](https://github.com/Ayberkone/tanik/commit/7e8e4e8), [ee30b3e](https://github.com/Ayberkone/tanik/commit/ee30b3e)). Backend pytest with in-memory SQLite + Worldcoin public iris fixtures; Playwright e2e for the client with browser-real webcam tests.
- **Multi-stage Dockerfiles + Docker Compose orchestration** ([5ed0504](https://github.com/Ayberkone/tanik/commit/5ed0504), [6027e97](https://github.com/Ayberkone/tanik/commit/6027e97)). Internal bridge network, named volume for SQLite, healthchecks on both services, `docs/development.md` covering native + hybrid + Compose flows.
- **Documentation lock-in** ([c3ef0f4](https://github.com/Ayberkone/tanik/commit/c3ef0f4), [6027e97](https://github.com/Ayberkone/tanik/commit/6027e97)). `docs/api-contract.md` (source of truth for the HTTP API); `docs/sequence-flow.md` (Mermaid state machine + sequence diagrams); `docs/development.md`.
- **Outreach captured** ([b4c76ee](https://github.com/Ayberkone/tanik/commit/b4c76ee)). Adam Czajka (ND CVRL) confirmed the ND-IRIS-0405 access path and pointed at <https://github.com/CVRL/OpenSourceIrisRecognition> (TripletIris + ArcIris — both NIST IREX X-leaderboarded). Filed in `BACKLOG.md` as a Phase 3.5 / Phase 5 follow-up.

### Fixed

- **Structured (logfmt) logging across endpoints** ([fa5e764](https://github.com/Ayberkone/tanik/commit/fa5e764)).
- **CI hardening**: `setup-uv` pinned to `v8.1.0` (no moving `v8` tag exists), legitimate React 19 lint warnings suppressed, `sqlite:///:memory:` env value correctly quoted in YAML ([d055ec9](https://github.com/Ayberkone/tanik/commit/d055ec9), [45a73aa](https://github.com/Ayberkone/tanik/commit/45a73aa), [e90ac7a](https://github.com/Ayberkone/tanik/commit/e90ac7a)).

### Pending

- `#32` Deploy to a public URL (Vercel client + Railway backend recommended). Paused per author decision.
- `#33` Phase 1 DoD verification — needs the deploy URL + a 5-minute real-browser walkthrough with the author's actual face.

---

## Phase 0 — Iris pipeline spike (shipped 2026-04-22)

### Added

- **`notebooks/00_iris_spike.ipynb`** ([e3879f4](https://github.com/Ayberkone/tanik/commit/e3879f4)) — runs the full Worldcoin `open-iris` pipeline on a sample iris image, visualises each intermediate stage (segmentation mask, normalised iris, iris code), and computes Hamming distances for same-eye and different-eye pairs. Same-eye distances are visibly lower than different-eye distances on the sampled pairs.
- **Project scaffolding** — `README.md`, `LICENSE` (MIT), `ROADMAP.md`, `BACKLOG.md`, `CLAUDE.md`, repo directory layout ([fe12452](https://github.com/Ayberkone/tanik/commit/fe12452) → [40f461b](https://github.com/Ayberkone/tanik/commit/40f461b)).

---

## Engineering tooling (separate from the application changelog)

- **`/handoff` + `/load` slash commands** ([a565e5f](https://github.com/Ayberkone/tanik/commit/a565e5f), [dfd7098](https://github.com/Ayberkone/tanik/commit/dfd7098), [336b04a](https://github.com/Ayberkone/tanik/commit/336b04a)) — clean session boundaries for Claude Code; renamed from `/resume` after collision with the built-in command. Lives in `.claude/skills/`.
- **Engineering tooling ported from farmalink** ([b4429ef](https://github.com/Ayberkone/tanik/commit/b4429ef)) — agents, skills, hooks, commands.
