# API contract — TANIK Inference

Version: **v1, iris + fingerprint + fused verify** (Phase 3 in progress; iris alone shipped in Phase 1, fingerprint added in Phase 2, unified `POST /api/v1/verify` added in Phase 3 #41 with placeholder calibration).

This document is the source of truth. The FastAPI implementation in `apps/inference/` and the Next.js client in `apps/client/` both read from this. If the implementation diverges, the implementation is wrong — fix the code, not the doc, unless the contract change is explicit and this doc is updated in the same commit.

The OpenAPI schema generated at `GET /docs` (FastAPI's built-in) must agree with everything below.

---

## Conventions

- Base path: `/api/v1`. Future versions get a new prefix; v1 stays stable until deprecated.
- All request/response bodies are JSON unless noted (`enroll` and `verify` accept `multipart/form-data` for the image upload; the response is always JSON).
- Timestamps are ISO 8601 with timezone (`2026-04-25T14:32:09+00:00`).
- IDs are UUID v4 strings.
- Every response includes a `request_id` — server-generated if the client did not provide one. Use it to correlate logs.

## Identity model

Subjects are server-managed. The client never invents an identifier:

- Enroll creates a new subject and returns its `subject_id`.
- Verify is **1:1**: client must supply `subject_id`. There is no 1:N identification endpoint in v1.
- A `display_name` is optional metadata, not an identifier. Two subjects with the same `display_name` are still two distinct subjects.
- Re-enrolling under the same `display_name` creates a *new* subject. Template aggregation (multiple captures per subject) is deferred — see `BACKLOG.md`.

## Image constraints

| | |
|---|---|
| Field name (multipart) | `image` |
| Allowed MIME (magic-byte verified, not header-trusted) | `image/png`, `image/jpeg`, `image/bmp` |
| Max size | 10 MB |
| Color | grayscale or 3-channel — engines convert internally as needed |
| Resolution | no hard limit; very small or low-quality images may fail the pipeline and return `PIPELINE_FAILURE` |

**Raw images are never persisted.** They live only in request-scoped memory. Only the extracted biometric template is stored.

## Endpoints

### `GET /api/v1/health`

Liveness check. Always returns 200 if the service is up; does not touch storage, the iris pipeline, or the JVM (the fingerprint engine version is read from the module constant — JVM startup is deferred to the first actual fingerprint request).

```json
{
  "status": "ok",
  "iris_engine": "open-iris/1.11.1",
  "fingerprint_engine": "sourceafis/3.18.1",
  "calibration_status": "placeholder",
  "version": "0.1.0"
}
```

`calibration_status` is `"placeholder"` until Phase 3 #43 ships measured fusion weights, then `"calibrated"`. Same in-band signal as the unified verify response. A monitoring system that reads this endpoint can flag deployments that are still on placeholder calibration.

### `POST /api/v1/iris/enroll`

Accepts an iris capture, runs the pipeline, stores the resulting template under a newly-created subject.

**Request** — `multipart/form-data`:

| field | type | required | notes |
|---|---|---|---|
| `image` | file | yes | iris capture, see image constraints |
| `display_name` | string | no | UX-only label, ≤ 64 chars; not an identifier |
| `eye_side` | string | no | `"left"` or `"right"`; defaults to `"left"` |

**Response** — 201 Created:

```json
{
  "request_id": "5b2d…",
  "subject_id":  "9f4c…",
  "display_name": "Alice",
  "eye_side": "left",
  "enrolled_at": "2026-04-25T14:32:09+00:00",
  "modality": "iris",
  "template_version": "open-iris/1.11.1"
}
```

The template itself is **not** returned. It is server-side state.

### `POST /api/v1/iris/verify`

Compares a fresh iris capture against the stored template for a known subject (1:1).

**Request** — `multipart/form-data`:

| field | type | required | notes |
|---|---|---|---|
| `image` | file | yes | iris capture, see image constraints |
| `subject_id` | string | yes | UUID returned by a prior enroll |
| `eye_side` | string | no | `"left"` or `"right"`; defaults to the eye_side recorded at enroll |

**Response** — 200 OK:

```json
{
  "request_id": "7a0e…",
  "subject_id":  "9f4c…",
  "modality": "iris",
  "matched": true,
  "hamming_distance": 0.124,
  "threshold": 0.37,
  "decision_at": "2026-04-25T14:32:11+00:00"
}
```

- `hamming_distance` is the raw masked fractional Hamming distance from `iris.HammingDistanceMatcher` (0 = identical, ~0.5 = independent random codes). Lower is better.
- `matched` is exactly `hamming_distance < threshold`.
- `threshold` is server-configured (env var `TANIK_IRIS_MATCH_THRESHOLD`, default `0.37`). Returned for client transparency; the client must not invent its own threshold.

### `POST /api/v1/fingerprint/enroll`

Accepts a fingerprint capture, runs the SourceAFIS extractor, stores the resulting template under a newly-created subject.

**Request** — `multipart/form-data`:

| field | type | required | notes |
|---|---|---|---|
| `image` | file | yes | fingerprint capture, see image constraints |
| `display_name` | string | no | UX-only label, ≤ 64 chars; not an identifier |
| `finger_position` | string | no | one of the 10 ISO-style positions: `right_thumb`, `right_index`, `right_middle`, `right_ring`, `right_little`, `left_thumb`, `left_index`, `left_middle`, `left_ring`, `left_little`. Defaults to `right_index` |

**Response** — 201 Created:

```json
{
  "request_id": "5b2d…",
  "subject_id":  "9f4c…",
  "display_name": "Alice",
  "finger_position": "right_index",
  "enrolled_at": "2026-04-25T14:32:09+00:00",
  "modality": "fingerprint",
  "template_version": "sourceafis/3.18.1"
}
```

The template itself is **not** returned. It is server-side state.

### `POST /api/v1/fingerprint/verify`

Compares a fresh fingerprint capture against the stored template for a known subject (1:1).

**Request** — `multipart/form-data`:

| field | type | required | notes |
|---|---|---|---|
| `image` | file | yes | fingerprint capture, see image constraints |
| `subject_id` | string | yes | UUID returned by a prior fingerprint enroll |
| `finger_position` | string | no | optional; the engine does not actually require it (fingerprint matchers are position-agnostic at scoring time), but the field is accepted for symmetry with iris and may be used in future analytics |

**Response** — 200 OK:

```json
{
  "request_id": "7a0e…",
  "subject_id":  "9f4c…",
  "modality": "fingerprint",
  "matched": true,
  "similarity_score": 184.2,
  "threshold": 40.0,
  "decision_at": "2026-04-25T14:32:11+00:00"
}
```

- `similarity_score` is SourceAFIS's similarity metric. **Higher is better; 0 means no match; the upper bound is open-ended** (typical self-match scores are in the hundreds). Note that this is the inverse direction of the iris `hamming_distance`.
- `matched` is exactly `similarity_score >= threshold`.
- `threshold` is server-configured (env var `TANIK_FINGERPRINT_MATCH_THRESHOLD`, default `40.0`, which corresponds to FMR=0.01% per [SourceAFIS's documented threshold](https://sourceafis.machinezoo.com/threshold)).
- `subject_id` returns 404 `SUBJECT_NOT_FOUND` if the subject does not exist *or* if its modality is not `fingerprint` — cross-modality lookups are deliberately invisible to a probing client.

### `POST /api/v1/verify`

Unified, fused 1:1 verification across iris and fingerprint. Accepts either modality alone or both in a single multipart upload. Each engine-native score is normalised to `[0, 1]` (`0 = no match, 1 = perfect match`); the fused decision is a weighted sum across the modalities supplied. See `docs/fusion.md` for the normalisation curves, weights, and the explicit honesty caveat that the current calibration is **placeholder** until Phase 3 #43 ships measured weights.

**Request** — `multipart/form-data`. At least one modality must be supplied; `image` and `subject_id` for a given modality must be supplied together (a half-supplied modality is a 400 `VALIDATION_ERROR`):

| field | type | required | notes |
|---|---|---|---|
| `iris_image` | file | conditional | iris capture; required if `iris_subject_id` is present |
| `iris_subject_id` | string | conditional | UUID returned by a prior iris enroll; required if `iris_image` is present |
| `iris_eye_side` | string | no | `"left"` or `"right"`; defaults to the eye_side recorded at enroll |
| `fingerprint_image` | file | conditional | fingerprint capture; required if `fingerprint_subject_id` is present |
| `fingerprint_subject_id` | string | conditional | UUID returned by a prior fingerprint enroll; required if `fingerprint_image` is present |
| `fingerprint_finger_position` | string | no | accepted for symmetry; not used by the matcher |

A wrong-modality `subject_id` (e.g. an iris subject_id passed as `fingerprint_subject_id`) returns 404 `SUBJECT_NOT_FOUND`, identical to the per-modality endpoints.

**Response** — 200 OK:

```json
{
  "request_id": "7a0e…",
  "matched": true,
  "fused_score": 0.78,
  "threshold": 0.5,
  "modalities": [
    {
      "modality": "iris",
      "subject_id": "9f4c…",
      "engine_native_score": 0.124,
      "normalised_score": 0.876,
      "weight": 0.5
    },
    {
      "modality": "fingerprint",
      "subject_id": "1d2a…",
      "engine_native_score": 184.2,
      "normalised_score": 0.71,
      "weight": 0.5
    }
  ],
  "calibration_status": "placeholder",
  "calibration_reference": "docs/fusion.md",
  "decision_at": "2026-04-25T14:32:11+00:00"
}
```

- `engine_native_score` — Hamming distance for iris (lower=better, `[0, 1]`) or SourceAFIS similarity for fingerprint (higher=better, open-ended). Same semantics as the per-modality verify responses.
- `normalised_score` — engine-native value mapped onto `[0, 1]` per `docs/fusion.md`.
- `weight` — the renormalised weight this modality contributed to the fused score *for this request*. With only one modality supplied, `weight` is `1.0` and `fused_score` equals `normalised_score`.
- `matched` — exactly `fused_score >= threshold`. Threshold is server-configured (`TANIK_FUSION_DECISION_THRESHOLD`, default `0.5`).
- `calibration_status` — `"placeholder"` until Phase 3 #43 publishes measured weights, then `"calibrated"`. Clients that need measured FAR/FRR must refuse a placeholder response.
- `calibration_reference` — path to the doc describing the active calibration, currently `docs/fusion.md`.

## Error model

All non-2xx responses return:

```json
{
  "request_id": "…",
  "error_code": "INVALID_IMAGE",
  "message": "Uploaded file is not a valid PNG/JPEG/BMP",
  "details": null
}
```

`error_code` is an enum the client can switch on. `details` is optional; structured per error code when present. `message` is human-readable and may change between versions — clients must not match on it.

| HTTP | `error_code` | When |
|---|---|---|
| 400 | `INVALID_IMAGE` | Magic bytes don't match an allowed MIME, or the image cannot be decoded by OpenCV |
| 404 | `SUBJECT_NOT_FOUND` | `verify` references a `subject_id` that does not exist |
| 413 | `PAYLOAD_TOO_LARGE` | Upload exceeds 10 MB |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | `Content-Type` not multipart, or image MIME not allowed |
| 422 | `VALIDATION_ERROR` | Pydantic-level rejection (missing/invalid form field). `details` carries the per-field errors |
| 500 | `PIPELINE_FAILURE` | open-iris returned a non-null `error` (segmentation failed, no iris detected, etc.). `details.stage` names the failing stage when known |
| 503 | `PAD_FAILURE` | Reserved for Phase 4. Not emitted in v1 |

## CORS

`Access-Control-Allow-Origin` is set per request to whatever origin matched the configured allowlist (env var `CORS_ALLOW_ORIGINS`, comma-separated). No wildcard. The client must be served from a listed origin.

## Logging

Every request and response is logged with at minimum: `request_id`, method, path, status, and elapsed time. `subject_id` is logged on enroll/verify; the image content is **never** logged.

## What v1 explicitly does not do

These are out of scope; do not emulate or stub them in the client:

- **Authentication / authorization.** Single-deployment, no users. Added when needed (Phase 4/5).
- **1:N identification.** No "find the matching subject" endpoint. Verify is always 1:1.
- **Calibrated fused decisions** — the unified `/api/v1/verify` endpoint exists (Phase 3 #41) but currently runs on placeholder weights and normalisation knobs. Measured FAR/FRR and tuned weights ship with Phase 3 #43.
- **Cross-modality enrolment under the same subject.** Each enrol creates its own subject row tagged with one modality; one human enrolling both iris and fingerprint produces two distinct `subject_id`s. Linking is deferred along with template aggregation.
- **Liveness / PAD** — Phase 4. The `PAD_FAILURE` error code is reserved but not emitted.
- **Subject deletion / template export.** Will be added when there is a concrete need; not before.
- **Multiple templates per subject (template aggregation).** Captured in `BACKLOG.md`.
