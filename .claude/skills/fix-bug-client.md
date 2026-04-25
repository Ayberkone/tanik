---
name: fix-bug-client
description: Debug and fix a TANIK Next.js client bug. Reproduce with a test, trace component → state → API, fix at the right layer, audit responsiveness and webcam cleanup.
---

# /fix-bug-client — TANIK client debugging

> Applies once `apps/client/` exists (Phase 1 task #23 onward).

## 1. Reproduce with a test

For rendering / state bugs (Vitest + React Testing Library):

```typescript
it('does NOT <the buggy behavior>', () => {
  render(<Component {...buggyProps} />)
  // should FAIL on current code
  expect(screen.queryByText('bug text')).not.toBeInTheDocument()
})
```

For full user flows (Playwright):

```typescript
test('user does NOT experience <the bug>', async ({ page }) => {
  await page.goto('/enroll')
  // steps to reproduce
  await expect(page.getByText('expected')).toBeVisible()
})
```

## 2. Trace the data flow

1. **Route** (`app/[...]/page.tsx`) — server vs client component? right component rendering?
2. **Capture state machine** (Zustand store) — current state? are transitions valid (IDLE → CAPTURING → ... → SUCCESS|FAILED)?
3. **Webcam** (`useEffect` with `getUserMedia`) — does cleanup `.stop()` every track? Is throttling honored (2-3 fps, not full rate)?
4. **API call** (`fetch` against `process.env.NEXT_PUBLIC_API_URL`) — request shape matches `docs/api-contract.md`?
5. **Response handling** — error_code switched on, not error message text?
6. **Render** — loading / error / success states all wired?

## 3. Identify the root cause

- Wrong state in store → check transition guards (forbidden transitions should throw)
- Webcam stays on after navigation → missing `.stop()` in `useEffect` cleanup, **Critical** (kiosk leak)
- Frame submission too aggressive → check throttle / requestAnimationFrame logic
- Wire format mismatch → `docs/api-contract.md` is the source of truth; either contract or code is wrong, not both
- Hydration mismatch → Server vs client component boundary issue; mark client component or move data fetching server-side
- Threshold/score displayed wrong → never invent values client-side; backend returns `hamming_distance` and `threshold`

## 4. Implement at the right layer

- API contract violation → fix the code, not the contract (unless the contract is wrong, in which case update both in the same commit)
- State machine bug → fix the store, not the component
- Layout bug → Tailwind utility, not inline `style={{...}}`

## 5. Verify

```bash
cd apps/client && pnpm test <test-file>
```

## 6. Responsive + accessibility check (lightweight)

- Verify at mobile (< 600px) and desktop (≥ 960px)
- Touch targets ≥ 44px
- Webcam permission denial path renders a message, doesn't hang

## 7. Run the full suite

```bash
pnpm build && pnpm test
```

## TANIK-specific gotchas

- **Always** stop webcam tracks in `useEffect` cleanup — kiosk hardware leak is the #1 expected production bug for this stack
- The capture state machine is **strict** — UI must not allow `verify` submission before the (placeholder) liveness gate passes (real liveness is Phase 4)
- Throttle webcam frame uploads to 2-3 fps, never full rate — bandwidth + backend cost
- All thresholds and scores come from the backend response, never invented client-side
