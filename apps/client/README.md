# tanik-client

TANIK Next.js client. Operator surface for iris enrollment and verification against the FastAPI inference service in `../inference/`. Contract lives in `../../docs/api-contract.md` — implementation must agree with it.

## Local dev

```bash
cd apps/client
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
# open http://localhost:3000
```

The home page server-renders the backend health probe — if the inference service isn't up, you'll see "unreachable" in the status pill.

## Tests

```bash
npm run test:e2e        # Playwright, headless chromium
npm run test:e2e:ui     # Playwright UI mode (browser inspector)
```

E2e tests intercept all `/api/v1/*` calls so they don't depend on a running backend; backend correctness is covered by pytest in `../inference/tests/`. The webcam capture itself is currently exercised only by the file-upload tab path — webcam permissions / `getUserMedia` mocking is a follow-up.

## Stack

Next.js 16 (App Router, Turbopack) · React 19 · TypeScript strict · Tailwind 4 · shadcn/ui (base-nova) · Zustand 5 · Playwright (chromium).
