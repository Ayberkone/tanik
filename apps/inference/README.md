# tanik-inference

FastAPI service that runs the iris (and later, fingerprint) biometric pipeline. Source of truth for the API contract is `../../docs/api-contract.md` — implementation must agree with it.

## Local dev

Uses the repo-root `.venv` (Python 3.10, with `open-iris` already installed via `IRIS_ENV=SERVER`). See `../../notebooks/README.md` for the venv setup if you have not done it yet.

```bash
# from repo root
uv pip install --python .venv/bin/python -e "apps/inference[dev]"

# run the service
.venv/bin/uvicorn tanik_inference.main:app --reload --port 8000

# health check
curl http://localhost:8000/api/v1/health
# -> {"status":"ok","iris_engine":"open-iris/1.11.1","version":"0.1.0"}

# OpenAPI / Swagger
open http://localhost:8000/docs
```

## Configuration

Environment variables (all optional, prefixed `TANIK_`):

| var | default | meaning |
|---|---|---|
| `TANIK_LOG_LEVEL` | `INFO` | stdlib log level |
| `TANIK_CORS_ALLOW_ORIGINS` | `http://localhost:3000` | comma-separated allowlist; no wildcards |
| `TANIK_DB_URL` | `sqlite:///./tanik.db` | SQLAlchemy URL; SQLite for v1 |
| `TANIK_IRIS_MATCH_THRESHOLD` | `0.37` | Hamming distance below which iris verify returns `matched: true` |
| `TANIK_MAX_UPLOAD_BYTES` | `10485760` | reject uploads larger than this with 413 |

## Tests

```bash
.venv/bin/pytest apps/inference/tests
```
