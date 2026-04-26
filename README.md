# TANIK

> Tanık *(tah-nuhk)* — Turkish for **witness**; the one who attests that something is true.
>
> An open-source, multi-modal biometric authentication kiosk. Iris + fingerprint, fused into a single identity decision, with honest metrics and a clear threat model.

**Status:** Phases 1 + 2 implementation shipped (iris + fingerprint enrollment + verification end-to-end). Phase 3 in progress — unified `/api/v1/verify` shipped with placeholder calibration; measured FAR/FRR pending dataset acquisition. Liveness arrives in Phase 4. See `ROADMAP.md` for phase definitions of done; see `CHANGELOG.md` for history.
**License:** MIT · **Stack:** Next.js 16 · FastAPI · Python 3.10 · OpenJDK 17 (for the SourceAFIS bridge)

---

## What this is

TANIK is a reference implementation of a multi-modal biometric kiosk — the kind of system used at airports, government ID counters, high-security facility entrances, and patient-identification terminals in hospitals. It is intentionally small enough to understand end-to-end in an afternoon, but architected the way a real system would be.

It is not a startup, not a SaaS, and not trying to be a commercial product. It is a serious demonstration piece: if you work in biometric identity and you open this repo, the goal is that you recognize every component, agree with most of the design choices, and find the threat model honest rather than marketing-coated.

## What it is not

- Not a face-recognition system. The two modalities here are iris and fingerprint, deliberately.
- Not a drop-in production deployment. It is a reference system; productionizing it requires certified hardware, a proper HSM-backed key store, and the operational posture that comes with actually holding identity data.
- Not a claim of novel research. Everything here stands on the shoulders of Worldcoin's `open-iris` pipeline and (upcoming) SourceAFIS.

## The intended pipeline

```
Capture → Quality gate → Liveness gate → Feature extraction → Matching → Fusion → Decision
```

Each stage has a single responsibility and can reject the request before passing to the next. Today, **Capture → Feature extraction → Matching → Decision is implemented for both modalities independently** (iris and fingerprint each via their own `/api/v1/{modality}/{enroll,verify}` endpoints; iris and fingerprint are not yet fused). Quality gate, liveness gate, and fusion arrive in Phases 3 and 4. Each phase's definition of done is in `ROADMAP.md`.

## Components — current state

| Layer | Tech | State |
|---|---|---|
| **Client** (`apps/client/`) | Next.js 16 (App Router, Turbopack), React 19, TypeScript strict, Tailwind 4, shadcn/ui (base-nova), Zustand 5 | ✅ Iris (webcam + upload) and fingerprint (upload-only) flows; capture state machine; 4-card home page |
| **Inference** (`apps/inference/`) | FastAPI, Pydantic v1 (constrained by open-iris), SQLAlchemy 2, JPype1 | ✅ Iris + fingerprint enrol + verify endpoints behind a shared `BiometricEngine` interface; magic-byte upload validation; both pipelines run in a thread pool |
| **Iris engine** | [`worldcoin/open-iris`](https://github.com/worldcoin/open-iris) | ✅ Pre-warmed in the Docker image; matches via masked fractional Hamming distance |
| **Fingerprint engine** | [SourceAFIS](https://sourceafis.machinezoo.com/) 3.18.1 (Java JAR vendored, called via JPype) | ✅ In-process JVM, native CBOR templates, similarity scoring against the documented FMR=0.01% threshold |
| **Liveness (v1)** | Basic presentation-attack detector | ⏳ Phase 4 |
| **Fusion** | Weighted-sum normalisation + unified `/api/v1/verify` | ✅ endpoint shipped (Phase 3 #41); weights are placeholder until #43 publishes measured calibration — see `docs/fusion.md` |
| **Storage** | SQLite (templates only, never raw images) | ✅ Modality-agnostic `subjects` table — `(subject_id, modality, template_bytes, metadata_json, ...)` — engines own their own template format |
| **Orchestration** | Docker Compose | ✅ Internal bridge network, named volume for SQLite, healthchecks on both services |
| **CI** | GitHub Actions | ✅ Backend pytest (incl. fingerprint suite against Temurin 17) + Playwright e2e on every push |

The client and inference node are decoupled intentionally. The inference node never renders UI, the client never runs ML. The only contract between them is `docs/api-contract.md`.

## Sequence

See `docs/sequence-flow.md` for the full state-machine + sequence diagrams (Mermaid). In short: the client captures a single frame under a strict state machine (`IDLE → CAPTURING → UPLOADING → PROCESSING → SUCCESS|FAILED`), and the inference node offloads the CPU-bound iris pipeline to a thread pool to keep the FastAPI event loop responsive.

## Security & threat model — honest as of v1

- **Template storage, not image storage.** Raw captures exist only in RAM during a request; they are never written to disk. What is stored is the iris template (the bit-quantized Gabor response). Reconstructing an image from this template using the open components here is not possible. This is a weaker claim than "biometric templates are mathematically irreversible" — that is research-active — but it is the claim we can defend.
- **MIME sniffing, not header trust.** Uploaded files are validated against magic bytes via `filetype`, not the `Content-Type` header.
- **Pydantic-v1 strict request models.** Malformed multipart payloads are rejected before any bytes reach OpenCV.
- **No liveness gate yet.** A printed photo of an enrolled iris will currently match. Phase 4 adds a PAD gate that returns `error_code: PAD_FAILURE` before the biometric pipeline runs.
- **No replay resistance.** v1 does not claim it. Phase 4+ introduces session nonces.
- **No template encryption at rest.** v1 stores templates as JSON in SQLite. Encryption (and an HSM-backed key) is part of the productionization story, not v1.
- **No authentication.** Single-deployment, no users.
- **KVKK / GDPR posture.** Templates are personal data; documented properly when `docs/privacy.md` lands in Phase 4.

The full threat model document arrives in Phase 4 (`docs/threat-model.md`). Do not infer security claims that are not made in this README or that document.

## Honest metrics

A biometric system without measured FAR (False Accept Rate) and FRR (False Reject Rate) on a known test set is a demo, not a system. Measured numbers will live in `docs/performance.md`, generated from `tests/evaluation/` — both arrive in Phase 3. **No FAR/FRR numbers appear anywhere in the repo until they have been measured on a real test set.** "TBD — awaiting evaluation run" is the correct placeholder; an invented "1 in 1,000,000" is not.

The fusion weights (iris vs fingerprint) will not be pulled from the air. They will be tuned on a held-out calibration set; the methodology lives in `docs/fusion.md` (Phase 3).

## Datasets

Currently in use: **MMU Iris Database** (Phase 0 spike notebook), Worldcoin's public iris demo set (downloaded as backend test fixtures), and **NIST MINEX III** validation imagery (Phase 2 fingerprint test fixtures, U.S. public domain). Source, license, and access notes for every dataset are in `docs/datasets.md`. No proprietary or private biometric data is included in the repo, ever — `notebooks/data/` and the test fixture cache are gitignored. ND-IRIS-0405 access is in progress for Phase 3 iris evaluation; an FVC-style fingerprint set with multiple impressions per finger is the parallel Phase 3 dependency on the fingerprint side.

## Quickstart

```bash
git clone https://github.com/Ayberkone/tanik && cd tanik

# Bring up the full stack (first build downloads ~600 MB of deps + the ONNX iris model)
docker compose up --build

# Client:   http://localhost:3000
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs  (auto-generated OpenAPI)
```

See `docs/development.md` for native dev, hybrid (backend in Docker, client native), and test commands.

The Phase 0 iris pipeline notebook lives at `notebooks/00_iris_spike.ipynb` — see `notebooks/README.md` for environment setup.

## Repository layout

```
tanik/
├── apps/
│   ├── client/              # Next.js 16 — operator surface
│   └── inference/           # FastAPI — iris enrollment + verification
├── docs/
│   ├── architecture.md      # Top-to-bottom system walkthrough (presentation-grade)
│   ├── api-contract.md      # Source of truth for the HTTP API
│   ├── sequence-flow.md     # State machine + Mermaid diagrams
│   ├── development.md       # Local dev, tests, foot-guns
│   ├── datasets.md          # Every dataset used, with source + license
│   ├── nd-iris-0405-access.md  # Step-by-step license execution for the Phase 3 iris dataset
│   ├── fusion.md            # Phase 3 fusion methodology + placeholder calibration caveat
│   ├── outreach/            # Email drafts to dataset providers
│   ├── threat-model.md      # Working draft (Phase 4 prep)
│   ├── privacy.md           # Working draft (Phase 4 prep) — KVKK + GDPR posture
│   ├── pad.md               # Skeleton (Phase 4) — presentation-attack-detection plan
│   ├── admin-api.md         # Skeleton (Phase 4) — operator API surface
│   ├── admin-dashboard.md   # Skeleton (Phase 4) — operator UI surface
│   ├── blog-post-draft.md   # Phase 5 prep — tech-blog draft (publishable when ready)
│   └── performance.md       # Skeleton; arrives in Phase 3 #43 (auto-generated)
├── notebooks/
│   ├── 00_iris_spike.ipynb  # Phase 0 walkthrough of the open-iris pipeline
│   └── README.md
├── tests/                   # repo-wide test harness — backend tests live in apps/inference/tests/
├── .claude/                 # agents, skills, hooks, commands for Claude Code
├── docker-compose.yml
├── ROADMAP.md
├── BACKLOG.md
├── CHANGELOG.md
└── README.md
```

## Roadmap

See `ROADMAP.md` for phased milestones and the definition of "done" for each phase. Items deliberately deferred (mobile-phone-as-reader, custom iris segmentation training, ND CVRL algorithm comparison, etc.) live in `BACKLOG.md`.

## Contributing

This is primarily a personal demonstration project, but thoughtful issues and pull requests are welcome — particularly around the evaluation suite, the threat model, and the PAD module once they land.

## Credits

- [Worldcoin `open-iris`](https://github.com/worldcoin/open-iris) — iris segmentation, normalization, and matching pipeline.
- [SourceAFIS](https://sourceafis.machinezoo.com/) — fingerprint matching (Phase 2 onward).
- [University of Notre Dame CVRL](https://cvrl.nd.edu/) — ND-IRIS-0405 dataset (Phase 3 evaluation; access in progress).
- [Multimedia University, Malaysia](http://pesona.mmu.edu.my/) — MMU Iris Database (Phase 0 / test fixtures).
- The biometrics research community, whose published FAR/FRR methodologies this project follows.

## License

MIT. See `LICENSE`.
