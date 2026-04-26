# TANIK — architecture & system walkthrough

A top-to-bottom explanation of what each piece of TANIK does, why it's built that way, and where the code lives. Written so it doubles as **Proline-presentation material** — read it as if you were going to walk a biometrics engineer through the system on a whiteboard.

If you only have five minutes, read sections 1, 2, 3, and 8.

---

## 1. The 30-second pitch

TANIK is a working multi-modal biometric kiosk: a user presents an iris and a fingerprint, the system fuses both into a single identity decision, and the whole thing is honest about what it does and does not do.

It is the kind of system that runs at airport e-gates, government ID counters, and high-security facility entrances. It is built with two open-source matchers (Worldcoin's `open-iris` for iris, SourceAFIS for fingerprint), a modality-agnostic API layer, and a strict capture state machine in the client. It avoids the most common failure modes of demo biometrics: it does not invent FAR/FRR numbers, it does not overclaim its liveness defences, and it never persists raw biometric images.

**Goal:** be a serious reference implementation that an engineer at Proline (or any other biometrics vendor) can read in an afternoon and not find embarrassing. Not a startup, not a SaaS, not a research paper.

## 2. Why iris + fingerprint, deliberately

Three modality choices were on the table at the start of the project:

| Modality | Pros | Cons | Decision |
|---|---|---|---|
| **Iris** | Highest accuracy of any non-DNA modality (1 in millions FAR achievable); textural detail is essentially identity-level entropy; well-studied since Daugman 1993 | Needs decent capture conditions; webcam captures are weaker than NIR captures | ✅ **Primary modality** — this is the modality biometric engineers respect most |
| **Fingerprint** | Massive deployment history; well-defined ISO standards (19794-2 templates, ANSI/NIST-ITL); huge ecosystem of test data (FVC, NIST SD27, MINEX) | Requires a reader for serious accuracy; smartphone capture is a different threat model | ✅ **Second modality** — adds independent evidence; well-supported by SourceAFIS |
| **Face** | Cheap; everyone has it; ubiquitous on phones | Highest false-accept rate of mainstream biometrics; severe presentation-attack surface (printed photos, screen replays, deepfakes); regulatory scrutiny in EU + Turkey | ❌ **Deliberately out of scope.** Adding face would dilute the credibility pitch — the goal is "serious biometrics," not "another face-recognition demo" |

The two-modality choice also gives us a real reason to do **score-level fusion** (section 8), which is the feature most biometrics-industry engineers actually care about.

## 3. The big picture

```
┌──────────────────────────────┐         ┌──────────────────────────────────────┐
│  Client (Next.js, browser)   │  HTTPS  │  Inference (FastAPI, Python 3.10)    │
│                              │ ──────► │                                      │
│  ─ Webcam capture            │         │  ─ Magic-byte upload validation      │
│  ─ Capture state machine     │         │  ─ open-iris pipeline (threadpool)   │
│  ─ Per-modality forms        │ ◄────── │  ─ SourceAFIS via JPype/JVM          │
│  ─ Result panels             │  JSON   │  ─ SQLite (templates only)           │
│                              │         │  ─ Fusion + unified verify           │
└──────────────────────────────┘         └──────────────────────────────────────┘
        Port 3000                                    Port 8000
                                                          │
                                                          ▼
                                            ┌─────────────────────────┐
                                            │  SQLite — templates     │
                                            │  (raw images NEVER      │
                                            │   touch the disk)       │
                                            └─────────────────────────┘
```

Two services, one bridge network, no shared state other than the HTTP contract documented in `docs/api-contract.md`. The inference node is the only thing that holds biometric data; the client is a stateless surface that captures, displays, and forgets.

The design discipline: **the client never runs ML, the inference node never renders UI.** The contract between them is a JSON HTTP API, nothing else. This is the same separation a real production deployment would have — the kiosk hardware runs the client, a hardened inference cluster runs the matchers.

## 4. The two services and their contract

### Client — `apps/client/`

A Next.js 16 app (App Router) using:

- **React 19 + TypeScript strict** for the UI
- **Tailwind 4 + shadcn/ui** (`base-nova` theme) for styling
- **Zustand** for the capture state machine
- **Playwright** for end-to-end tests

The UI is intentionally minimal: a 4-card home page (iris enroll, iris verify, fingerprint enroll, fingerprint verify), each leading to a single-purpose form. There is no admin dashboard yet (Phase 4), no operator login (single-deployment v1), and no analytics anywhere (privacy posture is load-bearing).

### Inference — `apps/inference/`

A FastAPI service in Python 3.10 (the version is pinned by `open-iris`'s upstream classifiers — 3.11+ is untested upstream). Uses:

- **Pydantic v1** for request/response validation (constrained by `open-iris`'s pin to `pydantic<2`; we follow when upstream upgrades)
- **SQLAlchemy 2** for the templates table
- **`fastapi.concurrency.run_in_threadpool`** for every CPU-bound matcher call — the event loop must not block on Hamming-distance math
- **JPype1 1.7.0** to call the SourceAFIS Java JAR in-process

### The contract

`docs/api-contract.md` is the source of truth. Both sides read from it; if FastAPI's auto-generated OpenAPI at `/docs` disagrees with the contract, the implementation is wrong, not the contract. The endpoints today:

| Endpoint | Status | Notes |
|---|---|---|
| `GET /api/v1/health` | ✅ | Liveness probe; no DB or ML touched |
| `POST /api/v1/iris/{enroll,verify}` | ✅ Phase 1 | Hamming distance; lower=better |
| `POST /api/v1/fingerprint/{enroll,verify}` | ✅ Phase 2 | SourceAFIS similarity; higher=better |
| `POST /api/v1/verify` | ✅ Phase 3 #41 | Unified, fused; `calibration_status: "placeholder"` until #43 |

## 5. The capture state machine (client-side)

The single most common failure mode in kiosk software is illegal UI states — submitting a verify request before the camera is actually streaming, double-submitting because the button wasn't disabled, retaining a webcam track after navigation. TANIK addresses this with a strict Zustand state machine, defined in `apps/client/lib/store.ts`:

```
IDLE ──startCapture──► CAPTURING ──beginUpload──► UPLOADING ──serverProcessing──► PROCESSING
                          │                                                              │
                          └──reset──► IDLE                                                ├─► SUCCESS
                                                                                          └─► FAILED
                                                                                                │
                                                                              SUCCESS,FAILED ──reset──► IDLE
```

Illegal transitions throw in dev (and log in prod — kiosk uptime trumps strictness once you have real users). `UPLOADING` and `PROCESSING` are deliberately separate even though today they're back-to-back; the distinction will earn its keep in Phase 4 when liveness streaming separates "bytes going up" from "server doing work."

Webcam cleanup is non-negotiable: every `MediaStreamTrack` opened in a `useEffect` must be `.stop()`-ed in the cleanup return. Forgetting this causes the kind of memory leak that only manifests after eight hours on actual kiosk hardware. See `apps/client/components/webcam-capture.tsx`.

The full sequence diagrams (enroll, verify, failure paths) are in `docs/sequence-flow.md`.

## 6. The biometric pipelines

Both engines satisfy a single Protocol so the API and storage layers can be modality-agnostic. The Protocol lives in `apps/inference/tanik_inference/engines.py`:

```python
class BiometricEngine(Protocol):
    name: str
    def template_version(self) -> str: ...
    async def encode(self, image_bytes: bytes, **kwargs) -> Tuple[Optional[bytes], Optional[str]]: ...
    async def match(self, probe: bytes, gallery: bytes) -> float: ...
```

Templates always cross the boundary as `bytes`. Each engine owns its own serialization format. `template_version()` records the producer so a mismatched matcher can be detected later (e.g. if you upgrade `open-iris` and try to match an old template against the new code).

### Iris — `apps/inference/tanik_inference/iris_engine.py`

Wraps Worldcoin's [`open-iris`](https://github.com/worldcoin/open-iris):

1. **Decode** the upload to a grayscale numpy array via OpenCV.
2. **Segment** the iris and pupil boundaries (an ONNX model — pre-downloaded into the Docker image).
3. **Normalise** to a polar (rectangular) "iris strip."
4. **Encode** via Daugman-style Gabor filters into a binary iris code (~2,048 bits) with a mask of the unreliable bits.
5. **Match** by computing the masked fractional Hamming distance — the proportion of bits that differ between two codes, ignoring the masked positions.

A Hamming distance of `0.0` means "every bit identical"; statistical independence between two random codes converges on `~0.5`. The default per-modality match threshold is `TANIK_IRIS_MATCH_THRESHOLD=0.37`.

### Fingerprint — `apps/inference/tanik_inference/fingerprint_engine.py`

Wraps [SourceAFIS](https://sourceafis.machinezoo.com/) 3.18.1, which is a Java library, called from Python via JPype:

1. **Start the JVM once per process** (JPype enforces single-JVM-per-process; this lines up with FastAPI's single-worker deployment model).
2. **Detect minutiae** — ridge endings, bifurcations — and their orientations.
3. **Build a template** in SourceAFIS's native CBOR format. ISO 19794-2 export is deferred to a future phase since it's an interop concern, not a matching one.
4. **Match** by aligning two templates and scoring their minutiae correspondence; the score is open-ended (typical strong matches: hundreds; SourceAFIS's documented FMR=0.01% threshold is `40.0`).

### Why both pipelines run in a threadpool

FastAPI is async. The iris pipeline is CPU-bound (segmentation + Gabor convolution) and the fingerprint matcher is JNI-bound (JVM call across the FFI boundary). Either would block the event loop if called inline. Both engines wrap their work in `run_in_threadpool`:

```python
async def encode(image_bytes: bytes, ...) -> ...:
    return await run_in_threadpool(_encode_sync, image_bytes, ...)
```

This is the Python production rule that bites every team learning async: "async" doesn't mean "non-blocking magic" — it means "you have to explicitly hand CPU work to a thread."

## 7. Storage — the modality-agnostic seam

`apps/inference/tanik_inference/storage.py` and the `Subject` model in `db.py`:

```sql
CREATE TABLE subjects (
    subject_id        VARCHAR(36) PRIMARY KEY,    -- UUID v4
    display_name      VARCHAR(64) NULL,           -- UX label, NOT an identifier
    modality          VARCHAR(16) NOT NULL,       -- "iris" or "fingerprint"
    enrolled_at       TIMESTAMP NOT NULL,
    template_version  VARCHAR(64) NOT NULL,       -- e.g. "open-iris/1.11.1"
    template_bytes    BLOB NOT NULL,              -- engine-owned format
    metadata_json     VARCHAR(256) NULL           -- modality-specific (eye_side, finger_position)
);
```

Two design choices to highlight:

- **One subject = one modality.** A human enrolling both iris and fingerprint produces *two* subject rows with two different `subject_id`s. Cross-modality linking is deferred — it's a real product feature (operator workflow) rather than a matching concern.
- **`metadata_json` as a string column,** not a real JSON type, so we stay portable across SQLite (dev) and Postgres (eventual production) without driver-specific tricks.

**Raw images are never written to disk.** They live in request-scoped Python memory and get garbage-collected when the response is sent. Only extracted templates are persisted. This is a stronger privacy posture than most demo biometric systems make, and it's enforced by absence — there's no code path that writes uploads to disk anywhere in the repo.

## 8. Score normalisation + fusion (the most interesting Phase 3 piece)

`apps/inference/tanik_inference/fusion.py` and `routes/verify.py`. Full methodology in `docs/fusion.md`.

**The problem:** iris reports a Hamming distance (lower=better, range `[0, 1]`); fingerprint reports a SourceAFIS similarity (higher=better, open-ended). To fuse them we need a common scale.

**The solution:** map both onto `[0, 1]` where `0 = no match` and `1 = perfect match`, using a piecewise-linear curve **anchored at each modality's existing operating threshold**. The threshold is the only number on each engine's native scale we already trust, so we use it as the anchor: an engine-native threshold maps to a normalised score of exactly `0.5`. That gives the fused decision threshold of `0.5` a clear semantic — *"both modalities sitting right at their per-modality operating point."*

```
Iris (lower=better)                Fingerprint (higher=better)
  HD=0   → 1.0                       score=0    → 0.0
  HD=thr → 0.5                       score=thr  → 0.5
  HD=ceil→ 0.0                       score=ceil → 1.0
```

Fusion is a weighted sum, with weights renormalised over the modalities the request actually supplied — so a single-modality unified call cleanly equals that modality's normalised score (no halving by the absent modality's weight).

**The honesty caveat:** today's weights and ceilings are *placeholders*, not tuned. The unified verify response carries `calibration_status: "placeholder"` as an in-band signal so a downstream system that promises measured FAR/FRR refuses to act on a placeholder. Real calibration ships in Phase 3 #43 once we have the ND-IRIS-0405 dataset (#11) + an FVC-style fingerprint set.

## 9. The honesty discipline (and why it's the credibility argument)

This is the single most important convention in TANIK, encoded in `CLAUDE.md`:

- **No invented FAR/FRR numbers.** If a number hasn't been measured on a real test set, it doesn't appear anywhere — not in the README, not in the API response, not in a doc. "TBD — awaiting evaluation run" is acceptable; "1 in 1,000,000" is not.
- **No overclaiming on liveness.** Phase 4 will add a basic presentation-attack detector. It will be documented as a basic defence, not "military grade." Real iris-PAD requires NIR hardware features that this system does not have.
- **Accurate privacy claims.** Templates are personal data under KVKK/GDPR. "Zero-knowledge" is the wrong phrase because templates *are* stored — the system uses precise language about template-vs-image storage instead.
- **Proper attribution.** Every borrowed methodology (open-iris, SourceAFIS, score normalisation, fusion weighting) is cited in module docstrings and in the README.

The pitch this enables: a Proline engineer reading this repo cannot find a place where the project is dishonest about its capabilities. Every claim has a verification path. That is what differentiates a serious reference implementation from a demo.

## 10. Threat model (current state, honestly)

Where TANIK is *strong* today:

- **Templates only, no raw image persistence.** Reconstructing an image from an `open-iris` template using the open code in this repo is not feasible. (This is weaker than "biometric templates are mathematically irreversible" — that is research-active — but it is the claim we can defend.)
- **MIME sniffing, not header trust.** Uploads are validated against magic bytes via the `filetype` library, not the HTTP `Content-Type` header.
- **Pydantic-strict request models.** Malformed multipart payloads are rejected before any bytes reach OpenCV.
- **No telemetry, no analytics, no third-party calls.** The privacy posture is load-bearing.

Where TANIK is *weak* today (and explicitly admits it):

- **No liveness gate yet.** A printed photo of an enrolled iris will currently match. Phase 4 adds `error_code: PAD_FAILURE`.
- **No replay resistance.** v1 does not claim it; Phase 4+ introduces session nonces.
- **No template encryption at rest.** Templates are JSON in SQLite. Encryption + an HSM-backed key is part of productionising, not v1.
- **No authentication.** Single-deployment, no users.
- **No 1:N identification.** Verify is always 1:1; no "find which subject matches this iris" endpoint.

The full document arrives as `docs/threat-model.md` in Phase 4. Until then, do not infer security claims that are not made in the README, in this document, or in `docs/fusion.md`.

## 11. What's shipped vs what isn't

| Phase | DoD met? | Notes |
|---|---|---|
| **0 — Iris spike notebook** | ✅ | `notebooks/00_iris_spike.ipynb` runs the full open-iris pipeline on sample data |
| **1 — Iris backend + minimal client** | ✅ implementation; ⏳ deploy | Code shipped; deploy (`#32`) and DoD walkthrough (`#33`) deferred per author |
| **2 — Fingerprint modality** | ✅ | SourceAFIS via JPype; `BiometricEngine` interface; client UI; backend CI green |
| **3 — Fusion, thresholds, honest metrics** | ⏳ in progress | `#41` shipped (this session); `#42` + `#43` blocked on dataset acquisition (`#11`) |
| **4 — Liveness + admin** | ⏳ | Out of scope until Phase 3 closes |
| **5 — Polish + release** | ⏳ | Landing page, blog post, outreach to Proline |

The phase-gate discipline — *"phases ship before the next one starts"* — is a direct response to the project's biggest historical failure mode: scope creep killing momentum before anything ships. New ideas go in `BACKLOG.md`, not silently into the active phase.

## 12. How this would scale to real production

This section is what a Proline engineer would want at the end of the walkthrough — *"OK, but is this anywhere near a real deployment?"*

Honest answer: TANIK is a reference, not a deployment. To productionize it you would need:

| Concern | TANIK today | Production reality |
|---|---|---|
| **Capture hardware** | Webcam (iris), upload-only (fingerprint) | Certified NIR iris camera (e.g. IrisGuard, Iritech); certified FAP-30+ fingerprint reader (Suprema, DigitalPersona, Crossmatch) |
| **Liveness** | None today (Phase 4 adds basic) | Hardware liveness features (NIR multi-spectral for iris; capacitive + sweat-pore detection for fingerprint) |
| **Template storage** | SQLite, plaintext JSON | Postgres or a dedicated identity store, AES-256 with HSM-backed keys, separate auditable access log |
| **Scaling** | Single FastAPI worker | Horizontal: multiple inference pods behind a load balancer; per-pod single JVM; templates table sharded by enrolment region |
| **Compliance** | KVKK/GDPR-aware, but template export + audit are TODO | KVKK in Turkey; GDPR + ISO/IEC 24745 (template protection) + ISO/IEC 30107 (PAD reporting) for EU deployments |
| **Operator UX** | Single-deploy, no admin | Multi-tenant admin, RBAC, full audit trail, enrolment workflow with quality re-capture |

The architecture is *deliberately friendly* to those upgrades — the `BiometricEngine` Protocol means swapping `iris_engine` for a vendor SDK is a one-file change; the storage layer is already modality-agnostic; the fusion endpoint is a clean seam for adding face or voice as a third modality if a customer demanded it.

## 13. File map — where each piece of code actually lives

```
apps/inference/                      ← FastAPI service
├── tanik_inference/
│   ├── main.py                      app factory, middleware, router registration
│   ├── config.py                    env-var-driven settings (TANIK_*)
│   ├── db.py                        SQLAlchemy engine + Subject model
│   ├── storage.py                   create/get subject; modality-agnostic
│   ├── engines.py                   BiometricEngine Protocol
│   ├── iris_engine.py               open-iris wrapper (threadpool)
│   ├── fingerprint_engine.py        SourceAFIS via JPype (threadpool)
│   ├── fusion.py                    score normalisation + weighted-sum fuser ★ Phase 3
│   ├── schemas.py                   Pydantic request/response models
│   ├── validators.py                magic-byte upload validation
│   ├── errors.py                    APIError + ErrorCode enum
│   ├── logging.py                   structured (logfmt) logging
│   ├── routes/
│   │   ├── health.py
│   │   ├── iris.py                  /api/v1/iris/{enroll,verify}
│   │   ├── fingerprint.py           /api/v1/fingerprint/{enroll,verify}
│   │   └── verify.py                /api/v1/verify (unified, fused) ★ Phase 3
│   └── vendor/
│       └── sourceafis-3.18.1.jar    ← Java JAR shipped in the wheel
└── tests/
    ├── conftest.py                  fixtures (iris from S3, fingerprint from MINEX)
    ├── test_health.py
    ├── test_validators.py
    ├── test_storage.py
    ├── test_engines_interface.py
    ├── test_iris_endpoints.py
    ├── test_fingerprint_engine.py
    ├── test_fingerprint_endpoints.py
    ├── test_fusion.py               pure normalisation/fusion math ★ Phase 3
    └── test_unified_verify.py       integration tests for /api/v1/verify ★ Phase 3

apps/client/                         ← Next.js 16 app
├── app/
│   ├── layout.tsx                   root layout
│   ├── page.tsx                     home — 4-card grid
│   ├── enroll/page.tsx              iris enroll
│   ├── verify/page.tsx              iris verify
│   └── fingerprint/
│       ├── enroll/page.tsx
│       └── verify/page.tsx
├── components/
│   ├── webcam-capture.tsx           getUserMedia + stream cleanup
│   ├── iris-form.tsx
│   ├── fingerprint-form.tsx
│   └── ui/                          shadcn/ui primitives
└── lib/
    ├── api.ts                       typed fetch client (mirrors api-contract.md)
    ├── store.ts                     Zustand capture state machine
    └── utils.ts

docs/
├── README.md                        directory index — start here for navigation
├── architecture.md                  this document ★ Phase 3
├── api-contract.md                  HTTP contract — source of truth
├── sequence-flow.md                 Mermaid state machine + sequence diagrams
├── development.md                   how to run locally
├── datasets.md                      every dataset used (source + license)
├── glossary.md                      biometrics vocabulary reference
├── nd-iris-0405-access.md           how to obtain the Phase 3 iris dataset ★ Phase 3
├── fusion.md                        fusion methodology + placeholder calibration ★ Phase 3
├── performance.md                   skeleton — auto-written by Phase 3 #43
├── threat-model.md                  Phase 4 prep — working draft
├── privacy.md                       Phase 4 prep — KVKK + GDPR posture
├── pad.md                           Phase 4 prep — PAD plan skeleton
├── admin-api.md                     Phase 4 prep — operator API skeleton
├── admin-dashboard.md               Phase 4 prep — operator UI skeleton
├── comparison.md                    TANIK vs commercial vendors + other open-source
├── blog-post-draft.md               Phase 5 prep — tech-blog draft
├── proline-pitch-deck.md            Phase 5 prep — Marp-renderable slide deck
└── outreach/                        email drafts to dataset providers

OWNER-ACTIONS.md                     things only the human owner can do
ROADMAP.md                           phase definitions of done + current status
BACKLOG.md                           ideas/follow-ups not in any current phase
CHANGELOG.md                         version history (Keep-a-Changelog)
CLAUDE.md                            instructions for the AI pair-programmer
```

## 14. Key references

- Daugman, J. (2004). *How iris recognition works.* IEEE TCSVT — the foundational reference for iris codes and Hamming-distance matching.
- Ross, A. & Jain, A. K. (2003). *Information fusion in biometrics.* Pattern Recognition Letters — the standard taxonomy for score-level fusion (sum-rule, weighted-sum, min/max). The piecewise-linear normalisation in `fusion.py` is the simplest credible variant.
- ISO/IEC 19794-2 — fingerprint minutiae template format. SourceAFIS supports it; TANIK uses native templates internally for fidelity.
- ISO/IEC 30107 — biometric presentation-attack detection terminology and reporting requirements. Will be the reference for `docs/pad.md` in Phase 4.
- Worldcoin `open-iris` — <https://github.com/worldcoin/open-iris>.
- SourceAFIS — <https://sourceafis.machinezoo.com/>; threshold guidance at <https://sourceafis.machinezoo.com/threshold>.

---

**If you got to the end:** the four things to remember are (1) two services with one HTTP contract, (2) modality-agnostic storage and engine interface, (3) score normalisation anchored at the per-modality threshold so fused-decision-threshold-of-0.5 has a clear semantic, and (4) honesty discipline — every claim in the repo has a verification path or a TBD label, never an invented number.
