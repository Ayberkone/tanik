# TANIK

> Tanık *(tah-nuhk)* — Turkish for **witness**; the one who attests that something is true.
>
> An open-source, multi-modal biometric authentication kiosk. Iris + fingerprint, fused into a single identity decision, with honest metrics and a clear threat model.

**Status:** early development · **License:** MIT · **Stack:** Next.js · FastAPI · Python 3.11

---

## What this is

TANIK is a reference implementation of a multi-modal biometric kiosk — the kind of system used at airports, government ID counters, high-security facility entrances, and patient-identification terminals in hospitals. It is intentionally small enough to understand end-to-end in an afternoon, but architected the way a real system would be.

It is not a startup, not a SaaS, and not trying to be a commercial product. It is a serious demonstration piece: if you work in biometric identity and you open this repo, the goal is that you recognize every component, agree with most of the design choices, and find the threat model honest rather than marketing-coated.

## What it is not

- Not a face-recognition system. The two modalities here are iris and fingerprint, deliberately.
- Not a drop-in production deployment. It is a reference system; productionizing it requires certified hardware, a proper HSM-backed key store, and the operational posture that comes with actually holding identity data.
- Not a claim of novel research. Everything here stands on the shoulders of Worldcoin's `open-iris` pipeline and SourceAFIS.

## The pipeline

```
Capture → Quality gate → Liveness gate → Feature extraction → Matching → Fusion → Decision
```

Each stage has a single responsibility and can reject the request before passing to the next. A submission that fails the liveness gate is never matched; a submission that fails the quality gate never reaches liveness. The decision record at the end contains the score from every stage, not just the final verdict.

## Components

| Layer | Tech | Responsibility |
|---|---|---|
| **Client** | Next.js (App Router), React, Zustand, Tailwind, shadcn/ui | Webcam access, capture state machine, UI feedback, calls to the inference API |
| **Inference** | FastAPI, Pydantic, OpenCV (headless) | File validation, liveness check, iris feature extraction, fingerprint matching, score fusion |
| **Iris engine** | [`worldcoin/open-iris`](https://github.com/worldcoin/open-iris) | Segmentation, normalization, iris code generation, Hamming-distance matching |
| **Fingerprint engine** | SourceAFIS (Python binding) | Minutiae extraction, ISO 19794-2 template generation, similarity scoring |
| **Liveness (v1)** | Basic presentation-attack detector (scoped in `docs/pad.md`) | Rejects obviously-spoofed captures (printed photos, replayed video) |
| **Storage** | SQLite | Enrollment templates (not images) |
| **Orchestration** | Docker Compose | Internal bridge network, one-command local boot |

The client and inference node are decoupled intentionally. The inference node never renders UI, the client never runs ML. The only contract between them is the OpenAPI schema in `docs/api-contract.md`.

## Sequence

See `docs/sequence-flow.md` for the full Mermaid diagram. In short: the client captures both modalities under a state machine, liveness is verified on a throttled stream before full-resolution templates are sent, and the inference node offloads CPU-bound work to a thread pool to keep the event loop responsive.

## Security & threat model (summary)

The full threat model lives in `docs/threat-model.md`. In brief:

- **Template storage, not image storage.** Raw captures exist only in RAM during a request; they are never persisted. What is stored is the extracted template (iris code or minutiae set), which is not reversible to a reconstructed image using the open components here. This is a weaker claim than "biometric templates are mathematically irreversible" — that is a research-active area — but it is the claim we can honestly defend.
- **MIME sniffing, not header trust.** Uploaded files are validated against their magic bytes, not their `Content-Type` header. No opportunity for an executable disguised as `.jpg`.
- **Pydantic-strict request models.** The API rejects malformed multipart payloads before any bytes reach OpenCV.
- **Liveness gate before biometric match.** If liveness fails, the biometric pipeline does not run. A spoofed submission costs the server almost nothing.
- **Replay resistance (roadmap).** v2 introduces a session nonce challenge. v1 does not claim replay resistance.
- **KVKK / GDPR posture.** Covered in `docs/privacy.md`. Short version: templates are personal data, they are encrypted at rest, access is logged, retention is configurable per deployment.

## Honest metrics

A biometric system without measured FAR (False Accept Rate) and FRR (False Reject Rate) on a known test set is a demo, not a system. Measured numbers for each modality and for the fused decision live in `docs/performance.md`, generated from the test scripts in `tests/evaluation/`. Numbers in the README are not maintained by hand — if you need current figures, run the evaluation suite.

The fusion weights (iris vs fingerprint) are not pulled from the air. They are tuned on a held-out calibration set; the methodology and the resulting weights are in `docs/fusion.md`.

## Datasets

TANIK is developed and evaluated against publicly available biometric datasets only. Every dataset used, its source, its license, and its access process is documented in `docs/datasets.md`. No proprietary or private biometric data is included in the repo, ever.

## Quickstart

```bash
# Clone
git clone https://github.com/<you>/tanik && cd tanik

# Bring up the full stack
docker compose up --build

# Client:    http://localhost:3000
# API:       http://localhost:8000
# API docs:  http://localhost:8000/docs  (auto-generated OpenAPI)
```

See `docs/development.md` for running the services natively without Docker, and for the conda environment used for iris model work.

## Repository layout

```
tanik/
├── apps/
│   ├── client/          # Next.js frontend
│   └── inference/       # FastAPI backend
├── docs/
│   ├── sequence-flow.md # Mermaid state/sequence diagrams
│   ├── api-contract.md  # Human-readable API reference
│   ├── threat-model.md  # Security posture and known limits
│   ├── performance.md   # FAR/FRR on test set, latency, throughput
│   ├── fusion.md        # Score normalization and weight calibration
│   ├── pad.md           # Presentation Attack Detection: what v1 does, what it doesn't
│   ├── privacy.md       # KVKK/GDPR handling
│   ├── datasets.md      # Every dataset used, with source and license
│   └── development.md   # Local dev, testing, evaluation
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/      # FAR/FRR measurement scripts
├── docker-compose.yml
└── README.md
```

## Roadmap

See `ROADMAP.md` for phased milestones and the definition of "done" for each phase.

## Contributing

This is primarily a personal demonstration project, but thoughtful issues and pull requests are welcome — particularly around the evaluation suite, the threat model, and the PAD module.

## Credits

- [Worldcoin `open-iris`](https://github.com/worldcoin/open-iris) — iris recognition pipeline
- [SourceAFIS](https://sourceafis.machinezoo.com/) — fingerprint matching
- The biometrics research community, whose published FAR/FRR methodologies this project follows

## License

MIT. See `LICENSE`.
