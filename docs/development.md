# Development

How to run TANIK locally — natively, in Docker, or in a hybrid mode (one in Docker, the other on the host).

The full stack is two services: a Python 3.10 FastAPI inference node (`apps/inference/`) and a Next.js 16 client (`apps/client/`). They talk over HTTP; the contract is `docs/api-contract.md`.

## Quickest path — Docker Compose

Boots both services with one command. Best for a smoke test or to demo the kiosk.

```bash
docker compose up --build       # first run downloads ~600MB of deps + the ONNX iris model
# client: http://localhost:3000
# api:    http://localhost:8000/docs
```

Templates persist across restarts in the named volume `tanik-inference-data`. To wipe:

```bash
docker compose down -v
```

## Native — backend

You'll need [`uv`](https://github.com/astral-sh/uv) to manage Python and the venv. Mac/Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# venv at the repo root, shared with the Phase 0 notebook
uv venv .venv --python 3.10

# open-iris must be installed with IRIS_ENV=SERVER (its setup.py requires it)
IRIS_ENV=SERVER uv pip install --python .venv/bin/python \
    "git+https://github.com/worldcoin/open-iris.git"

# backend (editable, with dev extras for pytest + httpx)
uv pip install --python .venv/bin/python -e "apps/inference[dev]"

# run
.venv/bin/uvicorn tanik_inference.main:app --reload --port 8000
```

First boot triggers a ~56 MB download of the segmentation ONNX model into `~/.cache/huggingface/`.

### Backend env vars

All optional, prefixed `TANIK_`:

| var | default | meaning |
|---|---|---|
| `TANIK_LOG_LEVEL` | `INFO` | stdlib log level |
| `TANIK_CORS_ALLOW_ORIGINS` | `http://localhost:3000` | comma-separated; no wildcards |
| `TANIK_DB_URL` | `sqlite:///./tanik.db` | SQLAlchemy URL; `:memory:` for tests |
| `TANIK_IRIS_MATCH_THRESHOLD` | `0.37` | Hamming distance below which iris verify returns `matched: true` |
| `TANIK_FINGERPRINT_MATCH_THRESHOLD` | `40.0` | SourceAFIS similarity at or above which fingerprint verify returns `matched: true` (FMR=0.01% per upstream) |
| `TANIK_MAX_UPLOAD_BYTES` | `10485760` | reject uploads larger than this with 413 |

#### Phase 3 fusion (unified `/api/v1/verify`)

These knobs control score normalisation and weighted-sum fusion. **All defaults are placeholders** — they're chosen so the unified endpoint runs end-to-end, not tuned. See `docs/fusion.md` for the methodology and `docs/performance.md` (skeleton) for where calibrated values will land.

| var | default | meaning |
|---|---|---|
| `TANIK_IRIS_HD_FLOOR` | `0.0` | Iris HD at or below this maps to normalised `1.0` |
| `TANIK_IRIS_HD_CEIL` | `0.5` | Iris HD at or above this maps to normalised `0.0` (statistical-independence boundary) |
| `TANIK_FINGERPRINT_SCORE_CEIL` | `200.0` | Fingerprint score at or above this maps to normalised `1.0` |
| `TANIK_FUSION_IRIS_WEIGHT` | `0.5` | Iris weight in the fused sum (renormalised over present modalities) |
| `TANIK_FUSION_FINGERPRINT_WEIGHT` | `0.5` | Fingerprint weight, same renormalisation |
| `TANIK_FUSION_DECISION_THRESHOLD` | `0.5` | Fused score at or above this returns `matched: true` |

Anchoring rule: each per-modality match threshold (`TANIK_IRIS_MATCH_THRESHOLD`, `TANIK_FINGERPRINT_MATCH_THRESHOLD`) is the value that maps to a normalised score of exactly `0.5`. Move the per-modality threshold and the normalisation curve moves with it; you do not need to retune the floor and ceil to keep the anchor consistent.

### Java runtime (Phase 2 onwards)

Phase 2 added SourceAFIS for fingerprint matching, called from Python via JPype. The vendored JAR (`apps/inference/tanik_inference/vendor/sourceafis-3.18.1.jar`) is loaded into an in-process JVM the first time any fingerprint endpoint or test runs.

- **Docker / CI**: handled — `default-jre-headless` is installed in the inference image and OpenJDK 17 (Temurin) in CI.
- **Native, Linux/x86_64**: install any OpenJDK ≥ 11 (`apt-get install default-jre-headless`); JPype1 wheels are prebuilt for manylinux.
- **Native, macOS Intel**: install OpenJDK ≥ 11 (`brew install openjdk@17` and follow the symlink hint Homebrew prints); JPype1 ships an x86_64 wheel.
- **Native, macOS Apple Silicon**: JPype1 1.7.0 ships **no arm64 macOS wheel** — `pip install jpype1` will try to build from source. You either need Xcode Command Line Tools + a JDK + Apache Ant available at install time, or skip native fingerprint dev and use Docker (`docker compose up inference`) for any work that touches `fingerprint_engine`. The backend test suite skips fingerprint tests cleanly when JPype isn't importable, so the rest of the suite still runs natively.

### Backend tests

```bash
.venv/bin/pytest apps/inference/tests        # 15 tests, ~5 s after first model download
```

The test suite uses an in-memory SQLite (`StaticPool`) and downloads three Worldcoin public iris fixtures into a gitignored cache on first run. CI in `.github/workflows/backend.yml` runs the same suite.

## Native — client

Node 20+ (24 used here). No global pnpm/yarn — npm is fine.

```bash
cd apps/client
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
# open http://localhost:3000
```

The home page server-renders the backend health probe. If you see "unreachable" in the status pill, the backend isn't running on the URL you set.

### Client tests

```bash
cd apps/client
npm run test:e2e        # Playwright headless chromium, 7 tests (~3 s)
npm run test:e2e:ui     # Playwright UI mode (browser inspector)
npm run lint
npm run build
```

E2e tests intercept all `/api/v1/*` calls — no backend required. CI in `.github/workflows/client.yml` runs lint + build + e2e on every push.

## Hybrid — backend in Docker, client native

Useful when you want the deps-heavy backend isolated but the client iterating fast with HMR.

```bash
docker compose up --build inference        # backend only
cd apps/client
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## Notebooks

The Phase 0 spike notebook (`notebooks/00_iris_spike.ipynb`) runs against the same `.venv` as the backend. See `notebooks/README.md` for setup.

## Known foot-guns

- **`~/.npm` permission errors.** If `npm install` complains about EACCES on `~/.npm/_cacache`, the cache has root-owned files from a previous sudo install. Fix once with: `sudo chown -R $(whoami) ~/.npm`. Or work around per-command with `NPM_CONFIG_CACHE=/tmp/npm-cache-tanik npm install`.
- **`opencv-python` vs `opencv-python-headless`.** open-iris pulls `opencv-python`, which needs `libGL.so.1` and breaks in slim Docker images. The backend Dockerfile swaps it for `opencv-python-headless` after install. Local dev is unaffected.
- **First Docker build is slow.** ~5–10 minutes because of open-iris install + ONNX model pre-download. Subsequent builds reuse the layers.
- **Webcam + HTTPS in production.** Browsers require HTTPS for `getUserMedia` outside `localhost`. The deploy story (Railway / Fly / VPS) needs a TLS terminator in front of the client; deploy task (#32) covers this.
- **Telemetry is off.** No analytics, no Next telemetry, no third-party calls. Privacy posture is load-bearing on a biometric system.
