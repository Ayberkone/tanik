---
name: fix-bug-backend
description: Debug and fix a TANIK FastAPI backend bug. Reproduce with a failing test, trace the data flow, fix at the right layer, audit consumers.
---

# /fix-bug-backend — TANIK inference debugging

## 1. Reproduce with a failing test

Before touching any code, write a pytest test that reproduces the bug. Use the existing `tests/test_*` style:

```python
def test_does_not_<the_buggy_behavior>(client_with_db):
    # Setup: the exact conditions that trigger the bug
    response = client_with_db.post(
        "/api/v1/iris/<endpoint>",
        files={"image": ("a.bmp", BMP_BYTES, "image/bmp")},
        data={"<form fields>"},
    )
    assert response.status_code == <expected>  # this should FAIL on current code
```

If the bug is in a non-HTTP module, write a unit test in `tests/test_<module>.py`.

## 2. Trace the data flow

Walk the request through the layers in order:

1. **Middleware** (`tanik_inference.main.request_context`) — request_id assigned, logging fires?
2. **Validator** (`validators.validate_image_bytes`) — does magic-byte check accept/reject correctly?
3. **Pydantic model** (`schemas.py`) — Form/File parsing succeeds? validation errors mapped via `ErrorBody`?
4. **Route handler** (`routes/iris.py`) — request_id propagated to response?
5. **Iris engine** (`iris_engine.encode` / `match`) — wrapped in `run_in_threadpool`? pipeline `error` field surfaced?
6. **Storage** (`storage.create_subject` / `get_template`) — round-trip via `IrisTemplate.serialize/deserialize` preserves the template?
7. **Response** — matches the shape in `docs/api-contract.md`?

Read the actual code at each layer; do not assume.

## 3. Identify the root cause

- Validation gap → fix the validator (`validators.py`) or the Pydantic model (`schemas.py`)
- Pipeline error not surfaced → check `iris_engine._encode_sync` returns the `out["error"]` correctly
- Storage round-trip drift → verify with the round-trip test in `tests/test_storage.py`
- Threshold mishandled → check `settings.iris_match_threshold` is read in the handler, not hardcoded
- Event loop blocked → check the slow call is wrapped in `run_in_threadpool` (or `asyncio.to_thread`)
- Privacy leak (image written somewhere) → grep `cv2.imwrite\|open(.*'wb')` in the request path; biometric images are request-scoped only

## 4. Implement the fix at the right layer

Don't patch a service-layer bug in the route handler. Don't patch a validator bug in the service. Read the call chain, find the actual source.

## 5. Verify

```bash
.venv/bin/pytest apps/inference/tests/test_<file>.py::<test_name> -v
```

The reproducer test you wrote in step 1 should now pass.

## 6. Audit downstream consumers

If the fix changed a function signature, response shape, or error code:

```bash
grep -rn "<changed_name>" apps/inference/ tests/ apps/client/ docs/
```

For each hit, verify still works. Update `docs/api-contract.md` in the same commit if the wire format changed.

## 7. Run the full backend test suite

```bash
.venv/bin/pytest apps/inference/tests
```

All green before commit. Use `/smart-commit` when ready.

## TANIK-specific gotchas

- **Pydantic v1**, not v2 — `BaseSettings` from `pydantic`, not `pydantic_settings`. `.dict()` not `.model_dump()`. `validator` not `field_validator`.
- The iris pipeline downloads its ONNX model on first init via `huggingface_hub` cache. If a test fails with a model-not-found error, the cache is stale — re-run after a clean.
- `run_in_threadpool` is from `fastapi.concurrency`, not `asyncio`. Both work; pick one and stay consistent.
- `request.state.request_id` is set by the middleware in `main.py`. If a handler logs without it, fix the handler not the middleware.
