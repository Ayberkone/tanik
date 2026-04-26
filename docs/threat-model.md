# TANIK — threat model (working draft, Phase 4 prep)

This document describes what TANIK defends against, what it does *not* defend against, and how those gaps will close (or remain open with explicit caveats) over Phases 4 and 5. It is honest by design: a biometric system that overstates its security is more dangerous than one that understates it, because operators rely on the documented posture when deciding what controls to layer around it.

> **Status:** working draft. The "current state" sections describe the system as of Phase 3 #41. Phase 4 (`#41`+ liveness + admin) will harden several entries; Phase 5 covers the final pass and outreach. Do not infer claims that are not made here or in `docs/privacy.md`.

---

## 1. Scope

**In scope.** The TANIK kiosk software stack as it ships in this repository:

- The Next.js client (`apps/client/`) — webcam capture, capture state machine, per-modality forms, error rendering.
- The FastAPI inference service (`apps/inference/`) — request validation, biometric pipelines, template storage, fusion.
- The HTTP contract between them (`docs/api-contract.md`).
- Templates at rest in SQLite and in transit across the internal Docker bridge.

**Out of scope.** Things a deployment would need to think about, but which TANIK as a *reference* deliberately does not solve:

- The physical kiosk enclosure and tamper resistance.
- Operator authentication and operator surface (Phase 4 admin).
- Anything network-facing beyond a TLS terminator on the client and the documented CORS origins on the backend.
- Identity-proofing the *initial* enrolment ("how do you know the person enrolling is who they claim to be?") — that is a workflow concern of the deploying organisation, not the kiosk's job.
- Identity-provider integration (OIDC, SAML, etc.).
- Crisis recovery (what happens after a biometric template database is breached).

## 2. Attacker model

We assume an attacker who:

- Can interact with the kiosk in person (present a photo, present another person's iris/finger, attempt to spoof).
- Can interact with the HTTP API directly (the kiosk client is not the only client; assume the URL leaks).
- Can read the contents of the template database if they obtain a copy of it (no encryption at rest in v1).
- **Cannot** read network traffic in transit (we assume TLS terminates correctly in front of the client; the inference service trusts the bridge network).
- **Cannot** execute arbitrary code on the inference host (we assume host hardening, container isolation, and standard OS-level controls).
- **Has no insider access** (no operator account, no DB credential leak). Insider-threat is a Phase 4+ concern alongside admin and audit.

What this attacker is after, in priority order:

1. **Identity impersonation** — "make the system say I am someone else." Highest impact: full authentication bypass.
2. **Identity disclosure / linkage** — "learn whether person X is enrolled" or "link two interactions to the same person across deployments."
3. **Denial of service** — "make the kiosk unavailable for legitimate users."
4. **Template theft for off-system use** — "exfiltrate templates that I can use against another biometric system."

## 3. Asset inventory

| Asset | Sensitivity | Stored where | Retention |
|---|---|---|---|
| **Raw biometric image** (iris or fingerprint) | KVKK / GDPR special category | Request-scoped Python memory only | Garbage-collected when the response is sent. Never written to disk. |
| **Biometric template** | KVKK / GDPR special category | SQLite, `subjects.template_bytes` | Until explicit deletion (no retention policy in v1; gap noted in `docs/privacy.md`) |
| **Subject metadata** (display_name, modality, finger_position, eye_side) | Low — UX label, not an identifier on its own | SQLite, `subjects` row | Same as template |
| **Request/response logs** | Low — `request_id`, method, path, status, elapsed_ms, `subject_id` on enroll/verify | stdout (logfmt) | Whatever the host's log retention says; not managed by TANIK |
| **Operator credentials** | High (Phase 4) | Not present in v1 | n/a yet |
| **HSM-backed encryption keys** | Critical (Phase 4+ productionisation) | Not present in v1 | n/a yet |

Note that the raw image's "retention" is *zero by design* — there is no code path in this repo that writes an upload to disk. This is a stronger privacy posture than most demo biometric systems make and is enforced by absence rather than by policy.

## 4. Attack surface

### HTTP API (`apps/inference/tanik_inference/routes/`)

Five endpoints today (listed in `docs/api-contract.md`). Every multipart upload is:

1. Capped at 10 MB (`TANIK_MAX_UPLOAD_BYTES`) — beyond which Starlette returns 413 before the bytes are buffered.
2. Validated against PNG/JPEG/BMP magic bytes via the `filetype` library — *not* against the `Content-Type` header (which a hostile client trivially controls).
3. Rejected with 400 `INVALID_IMAGE` if OpenCV cannot decode the bytes.

Pydantic models validate every form field; a missing or malformed field returns 422 `VALIDATION_ERROR` with per-field details.

### Persistence (`apps/inference/tanik_inference/storage.py`, `db.py`)

SQLAlchemy 2 with parameterised queries — no string concatenation into SQL; SQL injection is not a credible vector unless an attacker controls SQLAlchemy itself. The `Subject` table stores templates as `LargeBinary`; nothing in the schema allows arbitrary SQL fragments through it.

### JNI / JVM bridge (`apps/inference/tanik_inference/fingerprint_engine.py`)

Fingerprint matching crosses into the JVM via JPype. The JVM is started once per process with a single classpath entry — the vendored `sourceafis-3.18.1.jar`. Risk: any memory-safety issue in SourceAFIS or in JPype could be reachable from a crafted fingerprint image. Mitigation today: rely on upstream SourceAFIS quality and the fact that fingerprint images are decoded on the Java side, not via OpenCV.

### Static dependencies

- **`worldcoin/open-iris`** — pulls `opencv-python` (we swap to `opencv-python-headless` in Docker), TensorFlow Lite, and ONNX runtime. Each is a real dependency surface; Phase 5 will add Dependabot or equivalent.
- **`SourceAFIS` JAR** — vendored, version-pinned. Replacing the JAR is a deliberate operation; it does not auto-update.

## 5. Attacks, current mitigations, gaps

### 5.1 Presentation attack (printed photo, replay video, prosthetic)

**Vector.** Attacker presents a printed photo of an enrolled iris (or a high-resolution screen replay) to the kiosk camera. Without a liveness gate, the iris pipeline cannot tell a real eye from a sufficiently sharp photograph.

**Today.** No defence. A printed photo of an enrolled iris will currently match.

**Phase 4 (`docs/pad.md`).** A basic image-domain PAD detector trained on a public PAD dataset (e.g. NDIris3D, CASIA-Iris-Fake, LivDet-Iris). The PAD gate runs *before* the biometric pipeline; failure returns 503 with `error_code: PAD_FAILURE` (already reserved in `errors.py`).

**Honest limit.** The Phase 4 PAD module will be a *basic* defence — it will not stop a determined attacker with NIR-capable replay equipment or with realistic patterned contact lenses. Real iris-PAD requires multi-spectral NIR hardware features that this system does not have. `docs/pad.md` documents this in plain language.

### 5.2 Replay attack on the API

**Vector.** Attacker captures a legitimate verify request (enrolled user's iris bytes + their `subject_id`) and re-sends it later from a different machine. The server has no way to distinguish a fresh capture from a recorded one.

**Today.** No defence. The API does not bind a request to a fresh challenge.

**Phase 4+.** Introduce a challenge-response pattern: the client requests a server-issued nonce immediately before capture, signs the upload with the nonce, and the server rejects requests where the nonce is missing, stale, or already consumed. This is the standard pattern (e.g. WebAuthn assertion model).

### 5.3 Template theft from storage

**Vector.** Attacker obtains a copy of the SQLite file (compromised host, leaked backup, insider).

**Today.** Templates are stored as plaintext bytes in SQLite (`subjects.template_bytes`). With the file in hand and the open-source matchers in this repo, an attacker can attempt match-vs-other-systems attacks — although the *iris* template is engine-specific (open-iris's serialised IrisTemplate JSON), so cross-system reuse is non-trivial. Fingerprint templates are SourceAFIS native CBOR, with similar engine-specific structure.

**Production.** Templates encrypted at rest (AES-256) with keys held in an HSM (e.g. AWS KMS, Azure Key Vault, on-prem HSM). Per-template encryption with rotation. ISO/IEC 24745 (template protection) gives the framework. Out of scope for v1 because key management is the most operationally heavy part of biometrics, and a reference system that gets it wrong would mislead operators.

### 5.4 Template inversion (reconstructing the image from a template)

**Vector.** Attacker steals templates and attempts to reconstruct an image suitable for presenting to *another* biometric system.

**Today.** The repo contains no code that performs inversion, and reconstructing an image from an `open-iris` template using the open components here is not feasible. **This is a weaker claim than "biometric templates are mathematically irreversible"** — that is a research-active question, with published partial-inversion results against several iris and fingerprint template formats. The defence here is "no inversion code path in this repo," not "inversion is impossible."

**Mitigation that would change the picture.** Template protection schemes from ISO/IEC 24745 (cancellable biometrics, biocryptosystems, secure sketches) make a stolen template substantially less useful. Phase 5 / productionisation work.

### 5.5 Denial of service

**Vector.** Attacker floods the API with large multipart uploads or with malformed images that nonetheless pass magic-byte validation but tax the iris pipeline.

**Today.** The 10 MB upload cap and the magic-byte rejection knock out the easiest vectors. There is no rate limiting at the application layer — a deploy is expected to put a rate limiter in the front-of-house (e.g. Cloudflare, an nginx limit_req zone, or Railway/Vercel platform throttles).

**Production.** Per-IP and per-`subject_id` rate limiting; circuit breakers around the iris pipeline; graceful degradation when the threadpool queue is saturated.

### 5.6 Side-channel timing attacks

**Vector.** An attacker probes verify endpoints with carefully chosen `subject_id` values and measures response time to learn (a) whether a `subject_id` exists, or (b) information about the stored template.

**Today.** Cross-modality lookups deliberately return `404 SUBJECT_NOT_FOUND` (same as a missing subject) so a probing client cannot distinguish "exists in another modality" from "does not exist." However, the subsequent biometric pipeline runtime varies with image content; a sufficiently careful attacker could potentially learn coarse-grained information from response time. This is a research-active threat surface and not a practical concern for v1.

**Mitigation that would close it more tightly.** Constant-time comparison primitives, response-time padding to a fixed budget. Out of scope for v1.

### 5.7 Image-decoder vulnerabilities

**Vector.** Crafted PNG/JPEG/BMP that triggers a memory-safety bug in OpenCV's decoder.

**Today.** We rely on upstream OpenCV and on the magic-byte validation reducing the malformed-decode surface. There is no sandbox around OpenCV.

**Production.** Decode in a separate process or under a seccomp profile; eject any decoded image that exceeds expected dimension bounds.

## 6. What a production deployment would add (and why TANIK doesn't)

| Concern | Production answer | Why TANIK skips it |
|---|---|---|
| **Template encryption at rest with HSM-backed keys** | AES-256-GCM per-template; key in HSM with rotation policy; access audit | Key management is the operationally heaviest part of biometrics; a reference that gets it wrong misleads operators. Productionisation work. |
| **Operator authentication + RBAC + audit trail** | OIDC integration, role definitions (operator / admin / auditor), every mutating operation written to an append-only log | Single-deployment v1 has no operators. Phase 4 adds the admin dashboard and the audit trail at the same time, since they're entangled. |
| **Network segmentation** | Inference service in a private subnet, not internet-facing; client behind a TLS terminator + WAF | Architectural pattern, not a code change. Documented in deploy notes when `#32` ships. |
| **Vulnerability management** | Dependabot or Renovate; SBOM generation; periodic scan against CVEs in OpenCV / SourceAFIS / open-iris | Phase 5 polish. |
| **Backup & disaster recovery** | Encrypted snapshots of the templates DB; recovery drill cadence | Operational; out of scope for the reference. |

## 7. Standards alignment

Where the eventual production version of TANIK would seek alignment:

- **ISO/IEC 19795** — performance testing and reporting (FAR, FRR, ROC, etc.). `tests/evaluation/` (Phase 3 #43) targets this.
- **ISO/IEC 24745** — biometric template protection (cancellable biometrics, secure sketches). Frames the template-theft mitigation roadmap.
- **ISO/IEC 30107** — presentation attack detection terminology, error rates (APCER, BPCER), reporting requirements. Frames `docs/pad.md` (Phase 4).
- **NIST IR 8311 / NIST SP 800-76** — U.S. federal biometric guidance; useful as a sanity check for fingerprint format and threshold choices.
- **KVKK** (Türkiye) and **GDPR** (EU) — biometric data is special category; lawful basis, consent, retention, data-subject rights. See `docs/privacy.md`.
- **ISO 19794-2** — fingerprint minutiae template format, for interoperability. Native CBOR is used internally; ISO export is deferred (BACKLOG).

## 8. Known unknowns

Things this document does not yet have a confident answer for:

- The exact PAD model and dataset for `docs/pad.md` (Phase 4). The right choice depends on what's licensable and what generalises beyond its training set.
- The exact admin authn story — OIDC against a deploying-organisation IdP is the obvious choice, but the reference shouldn't bake in a specific provider.
- The right framing for the ISO/IEC 24745 template-protection layer — cancellable biometrics changes the matcher contract, which has knock-on effects through `BiometricEngine`.

These are flagged so that a Proline engineer reading this document can immediately ask the right questions rather than assume the gaps don't exist.
