"""JSON Schema validation helper for API responses."""
import json

from jsonschema import Draft7Validator

from framework.config import SCHEMA_DIR


def validate(instance, schema_name: str) -> None:
    schema = json.loads((SCHEMA_DIR / f"{schema_name}.json").read_text(encoding="utf-8"))
    errors = sorted(Draft7Validator(schema).iter_errors(instance), key=lambda e: list(e.path))
    assert not errors, "Schema validation failed: " + "; ".join(
        f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors
    )
