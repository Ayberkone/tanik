# TANIK — admin dashboard (skeleton, Phase 4)

The operator-facing UI that arrives in Phase 4. Sits behind the operator OIDC login (`docs/admin-api.md`), reads from the admin API endpoints, and gives the deploying organisation the surface they need to actually run a TANIK deployment.

> **Status:** skeleton. Captures the planned routes, page shapes, and design constraints ahead of Phase 4 implementation. Final layout and interaction details land during the implementation pass.

---

## Why this is needed

Today's TANIK has no operator surface — it is a kiosk plus an inference service, with no way for the deploying organisation to:

- See who's enrolled.
- Delete a subject when consent is withdrawn.
- Look at recent verification attempts when a user reports they were wrongly rejected.
- Sanity-check that the deployment is running with the expected thresholds and calibration.

A real deployment cannot ship without these. Phase 4's admin dashboard is the surface that closes the gap.

## Scope

**In scope.** A separate Next.js route tree at `/admin/*`, gated by OIDC login, surfacing the data from `/api/v1/admin/*`. Five pages:

1. **Overview** — aggregate metrics + calibration-status callout.
2. **Subjects** — list, search, detail, delete.
3. **Verifications** — recent verify attempts with filters.
4. **Configuration** — read-only view of active thresholds, weights, calibration.
5. **Audit log** — append-only record of mutating operations.

**Out of scope.** Live configuration mutations (env-driven, restart-required — see `docs/admin-api.md`). Multi-tenant management. Custom report builders. Anything that materially expands the operator role beyond "see what the system is doing and remove subjects when needed."

## Architectural decisions

### Same Next.js app, separate route tree

The admin lives at `/admin/*` inside the existing `apps/client/` Next.js app. Two reasons:

- Sharing the Tailwind theme, the shadcn/ui components, and the API client lib is cheaper than a second app.
- A second app means a second deploy URL, second CI workflow, second TLS terminator. Operator surfaces are usually small enough that the same-app approach pays off — and if they grow, splitting them later is a straightforward refactor.

The kiosk and admin layouts diverge sharply (the kiosk is fullscreen single-task; the admin is a sidebar-nav data dashboard). Next.js layout grouping (`app/(kiosk)/` and `app/(admin)/`) makes that clean without runtime overhead.

### Server-rendered pages, client-rendered tables

Pages are rendered server-side (App Router defaults), so the OIDC session check happens server-side and unauthenticated users never see a flash of authenticated content. Tables that need filtering / sorting / pagination flip to client components for interaction.

This matches the existing kiosk pattern and avoids introducing a new state model just for the admin surface.

### Read-mostly is the default mental model

The admin surface is overwhelmingly **read** with a small number of **delete** mutations. No "edit subject" workflow, no "create subject from admin" workflow, no "approve enrolment" workflow. If those become needed they are explicit features with their own design pass.

The narrow surface keeps the audit log tractable — every mutating action is one of a small fixed set, and the operator's deletion reason field captures the *why*.

## Routes and pages

### `/admin` — Overview

The first thing an operator sees after login. One screen, no scrolling on a 1080p admin laptop. Cards arranged in a 4×2 grid:

- **Calibration callout** (full-width banner). When `calibration_status === "placeholder"`, an amber warning banner: *"This deployment is running on placeholder fusion calibration. Measured FAR/FRR is not available. See `docs/fusion.md`."* When `calibrated`, a quiet green confirmation.
- **Enrolment counts (24h)** — total / iris / fingerprint.
- **Verification success rate (24h)** — single big number plus sparkline.
- **PAD failure rate (24h)** — number plus sparkline; Phase 4 only.
- **Median fused score (24h)** — number plus distribution histogram.
- **Recent activity** — last 5 verifications, "see all" link to `/admin/verifications`.

Window selector (24h / 7d / 30d / all) at the top, persisted in URL state.

### `/admin/subjects` — Subjects table

Paginated table, 50 per page, cursor-driven. Columns:

| Column | Notes |
|---|---|
| `display_name` | UX label, sortable |
| `modality` | iris / fingerprint badge |
| `template_version` | "open-iris/1.11.1" etc. |
| `enrolled_at` | relative + tooltip with absolute timestamp |
| Actions | view, delete |

Filters at the top: modality dropdown, display_name search, enrolment date range. Filter state is URL-encoded so it survives reload and is shareable.

### `/admin/subjects/[subject_id]` — Subject detail

Single-subject view. Shows the data from `GET /api/v1/admin/subjects/{id}` plus the most recent 20 verification attempts against this subject (filtered from `GET /api/v1/admin/verifications?subject_id=...`).

A "Delete subject" button at the bottom-right opens a modal that requires:
- The deletion reason (free text, ≤ 256 chars, required — passed to the API as `?reason=`).
- Typing the `subject_id` to confirm (defence against accidental clicks).

On success, redirect to `/admin/subjects` with a toast confirming deletion.

### `/admin/verifications` — Verification history

Same shape as the subjects table, against `GET /api/v1/admin/verifications`. Filters: subject_id (with autocomplete from /admin/subjects), modality, outcome, time range.

Outcome column uses badges: green (matched), grey (not_matched), red (pad_failure), red (pipeline_failure), amber (subject_not_found).

Each row expands to show the full score breakdown:

```
fused: 0.78 ≥ 0.50 → matched
  iris   engine 0.124  normalised 0.876  weight 0.50
  finger engine 184.2  normalised 0.71   weight 0.50
  pad    iris 0.04 / fp 0.06
```

### `/admin/configuration` — Active configuration

Read-only display of `GET /api/v1/admin/configuration`. Useful to confirm "is this deployment actually running with the expected thresholds?"

The display uses the same field labels as the env vars (e.g. `TANIK_FUSION_DECISION_THRESHOLD`) so an operator can directly cross-reference what they set in their deployment configuration.

A "How to change these" callout points at `docs/development.md` and explains that mutation requires restart by design.

### `/admin/audit-log` — Audit history

Append-only record of mutating admin operations (today, only subject deletions). Same table shape as verifications.

Each row shows: `at` timestamp, `operator_id`, `action`, `target_id` (linkable to `/admin/subjects/[id]`), `reason`. No edit, no delete — append-only by both schema and UI.

## Auth flow

```
1. Unauthenticated request to /admin/*
   → server checks for valid session cookie
   → none found, redirect to /admin/login

2. /admin/login renders the OIDC initiation
   → "Sign in with [IdP name]" button
   → click triggers the OIDC redirect with state + nonce

3. IdP authenticates the user and redirects back to /admin/auth/callback
   → server validates the OIDC response, exchanges code for tokens
   → server sets an HTTP-only session cookie (signed; rotates on each interaction)
   → redirect to the originally requested URL (or /admin if none)

4. Subsequent requests to /admin/*
   → server validates session cookie
   → if valid + role=operator, render the page
   → if expired, refresh via OIDC refresh token (silent if possible)
   → if anything fails, back to step 1
```

In dev mode (`TANIK_ADMIN_DEV_TOKEN` set), `/admin/login` shows a single "Sign in (dev)" button that posts the dev token directly. The page renders an unmissable banner across the top: *"DEV MODE — admin auth bypass active. Do not use in production."*

## Design constraints

### Density vs. cleanliness

Admin dashboards drift toward over-density (every metric, every filter, every dropdown). The kiosk surface is the opposite: minimum density, maximum focus. The admin surface should be *readable* density — closer to Linear or Vercel's dashboard than to a Bloomberg terminal.

Concretely: every page should pass the *"can a Proline engineer look at this for 30 seconds and understand the deployment's state?"* test.

### No vanity metrics

The Overview cards are operationally useful — calibration status, enrolment counts, success rates, PAD failure rates. Not "total verifications since deployment," not "average response time" (that's an SRE concern, not an operator one), not "uptime" (the deployment platform reports that).

### Honest about what's not yet there

When PAD hasn't shipped (Phase 4), the PAD-failure-rate card displays *"PAD module not yet enabled"* rather than a misleading "0% PAD failures." Same for any field that requires data the harness hasn't generated yet.

### Mobile is not a kiosk's problem, but it might be an admin's

The kiosk is fixed-installation; mobile responsiveness is irrelevant. The admin dashboard might be opened from an operator's phone in an incident response scenario. So: collapse the sidebar to a hamburger at narrow widths, allow tables to horizontal-scroll, but don't invest in a fully mobile-first redesign — the use case is "glance at the overview" rather than "full management workflow."

## What this skeleton does NOT specify

- The exact card components and chart library (Recharts vs. visx vs. Chart.js — pick during Phase 4 implementation; preference for the shadcn/ui chart wrappers if they exist by then).
- The exact OIDC library (`next-auth` is the obvious default; revisit if its v5 migration story bites us).
- The audit log's retention. Probably "forever" (it's an audit log) but should be confirmed against `docs/privacy.md`'s retention policy when that crystallises.
- Whether the admin surface ships in the same Docker image as the kiosk client, or whether the static `/admin` route tree is built into a separate stage. Probably the same image — see "same Next.js app, separate route tree" above.

## References

- `docs/admin-api.md` — the contract this dashboard renders.
- `docs/threat-model.md` §6 — how this admin surface fits into the larger productionisation picture.
- `docs/privacy.md` §5 — the gaps this dashboard closes (subject access portal, deletion endpoint, retention enforcement surface).
- shadcn/ui dashboard examples — <https://ui.shadcn.com/examples/dashboard> — pattern reference, not a literal copy.
