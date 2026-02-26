# Contract Fixtures and Test Template

Directory layout:

- `tests/contracts/fixtures/valid/` valid event samples
- `tests/contracts/fixtures/invalid/` invalid event samples
- `tests/contracts/test_event_schema_contract.py` schema validation template

Defaults:

- Schema path: `contracts/event-schema.json`
- Override with env var: `EVENT_SCHEMA_PATH=/abs/path/to/event-schema.json`

Suggested setup:

1. Add `jsonschema` to test deps if missing.
2. Run:

```bash
pytest tests/contracts/test_event_schema_contract.py
```
