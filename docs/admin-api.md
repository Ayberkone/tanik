# TANIK — admin API (skeleton, Phase 4)

The operator-facing API surface that arrives in Phase 4 alongside the admin dashboard (`docs/admin-dashboard.md`) and the PAD module (`docs/pad.md`). This document captures the planned shape ahead of implementation so the surface isn't designed for the first time under deadline pressure when Phase 4 starts.

> **Status:** skeleton. Phase 4 implementation will revise this against the chosen authentication mechanism and any operator workflow constraints surfaced in user testing.

---

## Scope

**In scope (Phase 4).** Endpoints under `/api/v1/admin/*` that an authenticated operator uses to:

- List, inspect, and delete enrolled subjects.
- Inspect recent verification attempts (audit trail).
- Read aggregate metrics (enrolment count, verification success rate, median PAD/quality scores).
- View the active configuration (thresholds, weights, calibration status).

**Out of scope (Phase 4).** Anything that mutates configuration via the API — thresholds and weights are still env-var driven, restart-required. Live reconfiguration is a Phase 5+ concern that needs a hot-reload story for the matchers and a defensible audit trail for "who changed what."

**Out of scope (TANIK as a reference).** Multi-tenancy. RBAC beyond a single "operator" role. Federation / SSO across multiple deployments. These are productionisation concerns, not reference-system features.

## Authentication model

The reference implementation will use **OIDC against a deploying-organisation identity provider**, with one role: `operator`. The provider is configurable via env (`TANIK_ADMIN_OIDC_ISSUER`, `TANIK_ADMIN_OIDC_CLIENT_ID`, `TANIK_ADMIN_OIDC_CLIENT_SECRET`). Local-dev convenience: a static-token mode (`TANIK_ADMIN_DEV_TOKEN`) bypasses OIDC for development only — clearly logged on startup as insecure.

What this is NOT:

- Not a full IdP integration (no group sync, no SCIM provisioning).
- Not RBAC (no fine-grained permissions; admin is admin).
- Not API-key based (keys for service-to-service calls are not in scope; operator humans only).

A real production deployment hooks the deploying organisation's IdP and may layer additional RBAC; the reference makes that integration the *one* boundary an operator team has to negotiate, rather than baking in a specific provider.

## Common conventions

All admin endpoints:

- Live under `/api/v1/admin/*`.
- Require a valid OIDC bearer token (or the dev token in local dev). 401 on missing/invalid; 403 on valid-but-wrong-role.
- Return `application/json`. Never multipart, never streaming binary, never raw biometric data.
- Are subject to the same `request_id` middleware as the rest of the API.
- Are logged as **audit events** (separate channel from the request log) — see `docs/threat-model.md` §6.

Pagination follows a cursor pattern:

- Query params: `?limit=N&cursor=...`.
- Response: `{ items: [...], next_cursor: "..." | null }`.
- Default `limit=50`, max `limit=200`.

Errors follow the same `ErrorBody` shape as the rest of the API (`request_id`, `error_code`, `message`, `details`). New error codes:

| HTTP | `error_code` | When |
|---|---|---|
| 401 | `UNAUTHORISED` | Missing or invalid bearer token |
| 403 | `FORBIDDEN` | Token valid but role insufficient |
| 404 | `SUBJECT_NOT_FOUND` | Existing code; reused for `GET/DELETE /admin/subjects/{id}` |
| 409 | `SUBJECT_HAS_DEPENDENCIES` | Reserved — for future template-aggregation work |

## Endpoints

### `GET /api/v1/admin/health`

Operator-side counterpart to `GET /api/v1/health`. Returns the same body plus the calibration status of the unified verify endpoint:

```json
{
  "status": "ok",
  "iris_engine": "open-iris/1.11.1",
  "fingerprint_engine": "sourceafis/3.18.1",
  "calibration_status": "placeholder",
  "version": "0.1.0"
}
```

Useful as a smoke test: an admin who logs in and sees `placeholder` knows immediately they're on a deployment that hasn't yet been calibrated.

### `GET /api/v1/admin/subjects`

Paginated list. Each item is the subject row plus the modality and template version (never the template bytes themselves):

```json
{
  "items": [
    {
      "subject_id": "9f4c…",
      "display_name": "Alice",
      "modality": "iris",
      "template_version": "open-iris/1.11.1",
      "metadata": { "eye_side": "left" },
      "enrolled_at": "2026-04-25T14:32:09+00:00"
    },
    ...
  ],
  "next_cursor": "..."
}
```

Optional query params:

- `?modality=iris` / `?modality=fingerprint` — filter by modality.
- `?display_name=Alice` — exact match (case-sensitive); for fuzzy search, use a search service in front of TANIK if needed.
- `?enrolled_after=...` / `?enrolled_before=...` — ISO 8601 timestamps.

### `GET /api/v1/admin/subjects/{subject_id}`

Single subject detail. Same shape as a list item; returns 404 `SUBJECT_NOT_FOUND` for missing.

### `DELETE /api/v1/admin/subjects/{subject_id}`

Hard-delete. Removes the row and the template bytes. Returns 204 on success, 404 on missing. Audit-logged with the operator's identity and the reason (`?reason=...` query param required, ≤ 256 chars — captured in the audit log as the operator's stated rationale; not validated for content).

This is the GDPR Art. 17 / KVKK Art. 7 "right to erasure" implementation. There is no soft-delete — once erased, the template is gone, which is the point.

### `GET /api/v1/admin/verifications`

Paginated audit trail of recent verification attempts. Each item:

```json
{
  "request_id": "7a0e…",
  "subject_id": "9f4c…",
  "modality": "iris" | "fingerprint" | "fused",
  "outcome": "matched" | "not_matched" | "pad_failure" | "pipeline_failure" | "subject_not_found",
  "scores": {
    "engine_native": 0.124,
    "normalised": 0.876,
    "pad": 0.04
  },
  "decision_at": "2026-04-25T14:32:11+00:00"
}
```

Optional filters: `?subject_id=...`, `?modality=...`, `?outcome=...`, `?from=...&to=...`.

### `GET /api/v1/admin/metrics`

Aggregate metrics across configurable windows. Default window: last 24h. Override via `?window=24h | 7d | 30d | all`.

```json
{
  "window": "24h",
  "enrollments": {
    "iris": 12,
    "fingerprint": 9,
    "total": 21
  },
  "verifications": {
    "total": 184,
    "matched": 167,
    "not_matched": 12,
    "pad_failure": 3,
    "pipeline_failure": 2,
    "success_rate": 0.907
  },
  "scores": {
    "median_normalised_iris": 0.91,
    "median_normalised_fingerprint": 0.88,
    "median_fused": 0.89,
    "median_pad": 0.04
  }
}
```

This is the data the Phase 4 admin dashboard renders on its overview page (see `docs/admin-dashboard.md`).

### `GET /api/v1/admin/configuration`

Read-only view of the live configuration. Lets an operator confirm what thresholds and weights the deployment is actually running:

```json
{
  "iris": {
    "match_threshold": 0.37,
    "hd_floor": 0.0,
    "hd_ceil": 0.5
  },
  "fingerprint": {
    "match_threshold": 40.0,
    "score_ceil": 200.0
  },
  "fusion": {
    "iris_weight": 0.5,
    "fingerprint_weight": 0.5,
    "decision_threshold": 0.5,
    "calibration_status": "placeholder",
    "calibration_reference": "docs/fusion.md"
  },
  "pad": {
    "model_version": "tanik-pad/0.1.0",
    "iris_threshold": 0.5,
    "fingerprint_threshold": 0.5
  },
  "uploads": {
    "max_bytes": 10485760
  }
}
```

Mutating any of these requires a restart with a new env var — by design. See "Out of scope (Phase 4)" above.

## Audit log

Every mutating admin operation (today: only `DELETE /api/v1/admin/subjects/{id}`) writes an audit record:

```json
{
  "audit_id": "...",
  "operator_id": "operator@example.com",
  "operator_idp": "https://idp.example.com",
  "action": "subject.delete",
  "target_id": "9f4c…",
  "reason": "Subject withdrew consent",
  "request_id": "...",
  "at": "2026-04-25T14:35:00+00:00"
}
```

Stored in a separate `audit_events` table (append-only, no UPDATE / DELETE permissions in production). Surface for reading the audit log: `GET /api/v1/admin/audit-log` with the same pagination + filter conventions.

## Honest gaps to revisit during Phase 4 implementation

1. **No template export.** GDPR Art. 20 may apply for some processing bases. Adding `GET /api/v1/admin/subjects/{id}/template` would meet portability — but exporting raw template bytes makes off-system use easier, which weakens the template-theft mitigation. The right answer probably depends on the deploying organisation's lawful basis. Revisit.
2. **No bulk operations.** Delete-many would be useful for retention policy enforcement. Until there's a documented retention policy (BACKLOG / `docs/privacy.md` §5), this is premature.
3. **No webhooks for verification events.** A real deployment may want to push verify outcomes to a downstream identity store. Out of scope for v1 admin; could land in Phase 5 if asked for.
4. **No API for changing per-subject metadata.** Today the only mutation is deletion. If a `display_name` correction is needed, the workflow is delete + re-enrol. This is intentional — it keeps the audit trail simple — but worth revisiting if it produces operational pain.

## References

- OpenID Connect Core 1.0 — <https://openid.net/specs/openid-connect-core-1_0.html>. The reference for the OIDC integration.
- ISO/IEC 24745 — biometric template protection. Frames the export-vs-no-export decision in (1) above.
- GDPR Art. 17 (right to erasure), Art. 20 (data portability) — the directives the delete endpoint and the (deferred) export endpoint implement.
