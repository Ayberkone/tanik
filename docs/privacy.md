# TANIK — privacy posture (working draft, Phase 4 prep)

This document describes how TANIK handles personal data — specifically biometric data, which is **special-category personal data** under both Türkiye's KVKK and the EU's GDPR. Reading this against the code should produce no surprises; if it does, the document is wrong (or the code drifted) and needs updating in the same commit.

> **Status:** working draft. The system today (Phase 3 #41) implements the data-minimisation posture below but does not yet expose data-subject rights as user-facing controls — those land in Phase 4 alongside the admin dashboard.

---

## 1. The legal regime, briefly

| Jurisdiction | Statute | Biometrics treated as |
|---|---|---|
| Türkiye | **KVKK** (Kişisel Verilerin Korunması Kanunu, Law No. 6698) — esp. Art. 6 | Özel nitelikli kişisel veri (special category personal data) |
| EU | **GDPR** (Regulation 2016/679) — esp. Art. 9 | Special category personal data |
| EU | **AI Act** (Regulation 2024/1689) — biometric identification systems | Risk-tiered; remote real-time biometric ID is heavily restricted |

Both KVKK and GDPR require:

- An explicit **lawful basis** for processing — for biometrics, the practical answer is **explicit, informed consent** (KVKK Art. 6 §3, GDPR Art. 9(2)(a)).
- **Data minimisation** — collect and retain the minimum necessary for the purpose.
- **Purpose limitation** — data collected for "kiosk authentication" cannot be repurposed for marketing analytics.
- **Storage limitation** — retain only as long as necessary; have a documented retention period.
- **Data subject rights** — access, rectification, erasure, portability, objection.
- **Notification of breach** — within statutory windows (72h under GDPR; KVKK has its own notification requirements).

A biometric system that doesn't have a story for each row above is non-compliant by default. TANIK as a *reference* makes the technical choices that make compliance cheap; the *operational* choices (lawful basis paperwork, the retention period, the breach response plan) belong to the deploying organisation.

## 2. Data inventory

The following table lists every category of data TANIK touches and the technical handling.

| Data | Personal data? | Stored? | Where | How long |
|---|---|---|---|---|
| **Raw iris image** | ✅ special category | ❌ never | Request-scoped Python memory only | Garbage-collected when response is sent. **No code path in this repo writes uploads to disk.** |
| **Raw fingerprint image** | ✅ special category | ❌ never | Same | Same |
| **Iris template** (open-iris IrisTemplate JSON, ~10 KB) | ✅ special category — biometric data even though derived | ✅ | SQLite, `subjects.template_bytes` | Until explicit deletion (no retention policy in v1 — *gap*) |
| **Fingerprint template** (SourceAFIS CBOR, variable size) | ✅ special category | ✅ | Same | Same |
| **`display_name`** (operator-supplied label, ≤ 64 chars) | ⚠️ may be PII if operator chose a real name | ✅ | SQLite, `subjects.display_name` | Same as template |
| **`subject_id`** (UUID v4) | ✅ pseudonymous identifier — personal data when combined with the template | ✅ | SQLite primary key | Same |
| **`metadata_json`** (`eye_side`, `finger_position`) | ❌ not personal data on its own; ⚠️ becomes so when joined with `subject_id` | ✅ | SQLite, `subjects.metadata_json` | Same |
| **Request log** (`request_id`, method, path, status, elapsed_ms) | ❌ not personal data | ✅ | stdout (logfmt) | Whatever the host's log retention is — *out of TANIK's control* |
| **`subject_id` in log lines** | ✅ pseudonymous | ✅ | stdout | Same |
| **Source IP address** | ✅ pseudonymous (GDPR Recital 30) | ❌ not logged by TANIK | n/a | n/a |
| **Image content in logs** | n/a | ❌ never | n/a | n/a |

The technically critical row is the first one: **the raw image is in memory for the duration of one request, and that's it.** This is enforced by absence — there's no code path that writes an upload to disk anywhere in the repository. `grep -rn "save\|write\|to_file" apps/inference/tanik_inference/` produces no hits against the upload bytes.

## 3. Templates *are* personal data — call this precisely

A common misframing: "we only store templates, so the system is privacy-safe." This is wrong on two counts.

1. **Templates are personal data.** Both KVKK and GDPR consider biometric templates derived from a person to be personal data — and the same special-category designation applies. Storing only the template is data-minimisation, not data-elimination. (See e.g. EDPB Guidelines 3/2019 on processing of personal data through video devices, §75; the same reasoning applies to other biometric modalities.)
2. **"Zero-knowledge" is the wrong phrase.** Some marketing material in the biometrics space describes template-only systems as "zero-knowledge biometrics." The cryptographic term "zero-knowledge" has a precise meaning that does not apply here — TANIK demonstrably knows the template (it's in the SQLite database), and the matcher knows enough about the template to compute a similarity score. The accurate phrase is "no raw image persistence."

Use precise language. Operators reading the documentation will base their compliance posture on it.

## 4. What TANIK does today (technical handling)

### Raw images

- Read into a Python `bytes` object inside the FastAPI route handler.
- Passed by reference to `validate_image_bytes` (magic-byte check) and to `engine.encode(...)` (which decodes to a NumPy array via OpenCV inside a thread).
- Both the `bytes` object and the NumPy array are released when the request handler returns. No `tempfile`, no `with open(...)`, no Pillow `.save()` against the upload bytes.

### Templates

- Returned from `engine.encode(...)` as opaque `bytes` (engine-specific format).
- Passed to `storage.create_subject(...)` which inserts a row into `subjects` with `template_bytes = ...`.
- Read back in `verify` via `storage.get_subject(...)`.
- Never logged. Never returned in API responses. Never written anywhere except SQLite.

### Logging

The `request_context` middleware in `apps/inference/tanik_inference/main.py` emits one log line per request with:

```
request_id, method, path, status, elapsed_ms
```

`subject_id` is logged at INFO level on enroll/verify. Image content is never logged (the bytes object is referenced inside the handler but is not part of the structured log fields). There is no logging of `display_name` or `metadata_json` content.

### Network

- The client and inference service talk over the internal Docker bridge in dev. In production, both go behind a TLS terminator. The internal bridge is *not* TLS-secured — the assumption is that anything on the bridge is already inside the trust boundary.
- CORS is allow-list driven (`TANIK_CORS_ALLOW_ORIGINS`, default `http://localhost:3000`). No wildcard origin.

### Persistence

- SQLite file at `./tanik.db` in dev; production-recommended swap is Postgres (the SQLAlchemy URL is the only thing that needs to change).
- Templates are stored as `LargeBinary` (BLOB). **No encryption at rest in v1** — the productionisation story is HSM-backed AES-256 per template with rotation. Documented in `docs/threat-model.md` §5.3.

## 5. What TANIK does NOT yet do (the honest gap list)

These are gaps that an operator reading this document needs to be aware of, *and* that map to specific Phase 4 work or operational policy:

| Gap | Concrete impact | Where it gets closed |
|---|---|---|
| **No consent UI** | The kiosk does not present a consent dialog before capturing biometric data. A real deployment must layer one on top. | Phase 4 admin / Phase 5 polish |
| **No retention period** | Templates persist until explicit deletion. There is no scheduled deletion job. | Phase 4 admin (retention policy as a config value) |
| **No subject access portal** | A data subject cannot request "what do you have on me?" through any TANIK surface. | Phase 4 admin endpoint |
| **No subject deletion endpoint** | The schema supports row deletion, but there is no API for it. | Phase 4 admin endpoint (`DELETE /api/v1/subjects/{id}`) |
| **No template export (portability)** | GDPR Art. 20 requires data portability for some processing bases. | Phase 4 if needed by the deploying org |
| **No encryption at rest** | A copy of the SQLite file = templates in clear. | Productionisation (post-Phase 5) — HSM-backed |
| **No documented breach response plan** | KVKK and GDPR both require notification within statutory windows. | Operator policy — TANIK provides the technical controls (audit trail in Phase 4); the playbook is operational |
| **No documented sub-processor list** | Any cloud provider, monitoring service, or analytics tool must be enumerated for GDPR. | TANIK has none today (no analytics, no telemetry, no third-party calls) — this is the right answer for the privacy posture |

## 6. Cross-border transfer

Today TANIK is a single SQLite-backed deployment; the dataset never leaves the host. Cross-border concerns become real when:

- The deployment uses a cloud region outside the EU (for an EU-resident subject) or outside Türkiye (for a KVKK-covered subject).
- Logs are shipped to a SaaS log aggregator hosted in another jurisdiction.

The standard answer for GDPR is Standard Contractual Clauses (SCCs) plus a Transfer Impact Assessment; for KVKK, transfer outside Türkiye requires KVKK Board approval or one of the limited exceptions in Art. 9. This is operator policy; TANIK's job is to make the data set you're transferring as small and well-defined as possible.

## 7. The non-claims

What TANIK does **not** claim:

- It is **not** "zero-knowledge." Templates are stored. Use "no raw image persistence" instead.
- It is **not** "GDPR-compliant" or "KVKK-compliant." A *system* cannot be compliant on its own — compliance is a property of the *deployment* (with consent, retention, subject-rights handling, breach response). TANIK provides the technical building blocks that make compliance achievable; the rest is operator work.
- It is **not** "privacy-preserving" in the cryptographic sense (homomorphic, secure-MPC, zero-knowledge proofs). It is data-minimising and template-only.
- It does **not** prevent template inversion. See `docs/threat-model.md` §5.4.

## 8. Why this posture matters for the project's pitch

The whole credibility argument for TANIK rests on being honest about what it does. Saying "we do not persist raw images" and being able to show that there is no `.save()` call against the upload bytes anywhere in the codebase is much stronger than saying "biometric data is fully protected" and having a reader find a `tempfile.mkstemp(suffix=".png")` ten files later. The privacy posture is load-bearing on the project's reason to exist.
