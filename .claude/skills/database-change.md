---
name: database-change
description: Modify the TANIK SQLite schema (SQLAlchemy 2.x ORM). Update the model, decide on migration if data exists, update the storage layer, write a round-trip test.
---

# /database-change — TANIK schema change

The TANIK data model is small (one `subjects` table in v1). Most changes are additive: a new column, a new index. Real migrations are rare.

## 1. Update the SQLAlchemy model (`tanik_inference/db.py`)

```python
class Subject(Base):
    __tablename__ = "subjects"
    subject_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # ... existing fields
    new_field: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
```

Decisions to make:

- **Nullable?** In v1 with no production data, you can choose. Default to nullable to avoid migration ceremony for the SQLite case.
- **Index?** Add `index=True` if a query will filter or sort by this field.
- **Unique?** `unique=True` if it's a natural identifier.
- **Default?** Use Python defaults sparingly (`default=...`) — server-side defaults are simpler in SQLite.

## 2. Decide on a migration

For TANIK at current scale:

- **No production data, fresh dev DB:** delete the local `*.db` file, restart, `init_db()` recreates the schema. No migration needed.
- **Data exists you want to preserve:** write a small script in `apps/inference/scripts/migrate_<description>.py` that opens the engine, alters the schema, and backfills. Document rollback in the script docstring.

For Phase 1-3, the no-migration path is almost always the right call — the project has no users.

When TANIK does have production data (Phase 4+, deployed), introduce Alembic. Don't introduce it before then.

## 3. Update the storage layer (`tanik_inference/storage.py`)

If the new field is set on `create_subject` or read on `get_subject` / `get_template`, update those functions and their type signatures. Keep the existing `Subject` ORM expunged-after-fetch pattern.

## 4. Update the API contract (`docs/api-contract.md`)

If the new field is exposed in any response or accepted in any request, update the contract in the same commit. The contract is the source of truth; it must not lag.

## 5. Update Pydantic schemas (`tanik_inference/schemas.py`)

If the new field appears in `EnrollResponse` / `VerifyResponse` / a request model, update them. Pydantic **v1** API.

## 6. Write the round-trip test (`apps/inference/tests/test_storage.py`)

Most schema bugs are template (de)serialization drift or NULL handling. Make sure both work:

```python
def test_new_field_round_trip(template):
    row = create_subject(template, ..., new_field="value")
    fetched = get_subject(row.subject_id)
    assert fetched.new_field == "value"

def test_new_field_optional(template):
    row = create_subject(template, ..., new_field=None)
    fetched = get_subject(row.subject_id)
    assert fetched.new_field is None
```

If the change touches template serialization itself, also run a Hamming-distance round-trip:

```python
def test_template_round_trip_preserves_distance(template):
    row = create_subject(template, ..., new_field=None)
    back = get_template(row.subject_id)
    matcher = iris.HammingDistanceMatcher()
    assert matcher.run(template, back) < 0.05
```

## 7. End-to-end verify

If the new field shows up in any endpoint response, boot uvicorn and curl:

```bash
.venv/bin/uvicorn tanik_inference.main:app --port 8001 &
curl ... | python3 -m json.tool   # confirm the field is present and correctly populated
kill %1
```

## 8. Pre-completion audit

- Grep every consumer of `Subject` / `EnrollResponse` / `VerifyResponse` — each one updated
- Contract reflects the change
- Tests green: `.venv/bin/pytest apps/inference/tests`
- The `*.db` files are gitignored (already are) — no DB binary in the commit

## Anti-patterns

- ❌ Adding Alembic before there is production data to protect
- ❌ Changing template serialization format without a round-trip Hamming test
- ❌ Dropping a column with stored data — even in dev, write a backup-then-recreate script and document it
- ❌ Storing raw biometric images — templates only, always
