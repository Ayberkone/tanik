---
name: new-api-endpoint
description: Add a new endpoint to the TANIK FastAPI service. Defines the contract first, then Pydantic models, route, async-safe pipeline call, storage, and tests in that order.
---

# /new-api-endpoint — Add a TANIK endpoint

Order matters. Skipping a step usually means it gets skipped forever.

## 1. Update `docs/api-contract.md` first

The contract is the source of truth. Add the new endpoint to the contract before writing code:

- Path, method, request shape (multipart fields + types + validation rules), response shape, status codes, error codes.
- If the endpoint adds a new `error_code`, add it to the error model table.
- Get the contract right; the implementation translates it.

## 2. Add Pydantic schemas (`tanik_inference/schemas.py`)

```python
class NewResponse(BaseModel):
    request_id: str
    subject_id: str
    modality: Modality
    # ... fields per the contract
```

Pydantic **v1** (constrained by open-iris). Use `Field(..., ge=, le=)` for numeric bounds.

## 3. Add the new error code (`tanik_inference/errors.py`)

If the endpoint introduces a failure mode that doesn't fit existing codes, extend the `ErrorCode` enum and the HTTP-status map in `register_exception_handlers`.

## 4. Implement the route (`tanik_inference/routes/<resource>.py`)

```python
@router.post("/new", response_model=NewResponse, status_code=201)
async def new_handler(
    request: Request,
    image: UploadFile = File(...),
    field: str = Form(...),
) -> NewResponse:
    data = await image.read()
    validate_image_bytes(data)                    # magic-byte gate

    template, err = await iris_engine.encode(     # async-safe; blocks event loop otherwise
        data, eye_side=..., image_id=f"new:{request.state.request_id}",
    )
    if template is None:
        raise APIError(500, ErrorCode.PIPELINE_FAILURE, f"...{err}", details={"stage": "encode"})

    # ... business logic via the storage layer

    return NewResponse(request_id=request.state.request_id, ...)
```

Mandatory in every handler:

- `validate_image_bytes(data)` for any uploaded image — never trust `Content-Type`
- `await iris_engine.encode/match` — never call the pipeline synchronously
- `request.state.request_id` echoed in the response and any error
- Errors raised as `APIError(...)` so the handlers in `errors.py` produce the contracted body

## 5. Wire the router in `tanik_inference/main.py`

```python
app.include_router(<resource>.router, prefix="/api/v1")
```

(Existing iris router does this — just add the new one alongside.)

## 6. Write tests (`apps/inference/tests/test_<resource>.py`)

Unhappy paths first (cheap, prove the validators), then happy path, then edge cases.

```python
def test_rejects_garbage_upload(client):
    r = client.post("/api/v1/<resource>/new",
                    files={"image": ("x.png", b"not an image", "image/png")},
                    data={"field": "..."})
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_IMAGE"

def test_happy_path_with_real_fixture(client, mmu_image):
    r = client.post(...)
    assert r.status_code == 201
    body = r.json()
    assert body["request_id"]
    assert body["subject_id"]
    # response shape exactly matches the contract
```

For the test client, use `fastapi.testclient.TestClient(app)` and a temp SQLite DB (`TANIK_DB_URL=sqlite:///:memory:` in env before importing).

## 7. End-to-end verify with curl

The unit test does not prove the wire format. Boot uvicorn and curl with a real MMU image — capture the request_id and response in the commit message.

```bash
.venv/bin/uvicorn tanik_inference.main:app --port 8001 &
curl -s -X POST http://localhost:8001/api/v1/<resource>/new \
  -F "image=@notebooks/data/mmu/<file>.bmp;type=image/bmp" \
  -F "field=value" | python3 -m json.tool
kill %1
```

## 8. Pre-completion audit

- Grep every consumer of any changed shared type: `grep -rn "<symbol>" apps/inference/ docs/ apps/client/`
- Re-read the contract — no drift
- All affected tests green
- `request_id` in every response (success and error)

## Anti-patterns

- ❌ Writing the route before updating the contract — guarantees drift
- ❌ Calling `iris.IRISPipeline()(...)` directly inside a handler — blocks the event loop
- ❌ Trusting `Content-Type` header on uploads — magic-byte validation only
- ❌ Hardcoding thresholds in the handler — must come from `Settings`
- ❌ Persisting raw images anywhere — only templates go to SQLite
