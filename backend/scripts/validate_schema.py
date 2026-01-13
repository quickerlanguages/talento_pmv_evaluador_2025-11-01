#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_schema_registry(schemas_root: Path):
    """
    Build a referencing.Registry mapping $id -> schema resource, by scanning
    schemas_root/**/*.schema.json and schemas_root/**/v*.json (for versioned schemas).

    This makes $ref robust against file moves as long as $id is stable.
    """
    try:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except Exception as e:
        die(
            "No puedo importar 'referencing' (dependency of jsonschema>=4). "
            f"¿requirements-dev.txt actualizado? ({e})",
            2,
        )

    resources = []

    candidates = list(schemas_root.rglob("*.schema.json")) + list(schemas_root.rglob("v*.json"))
    for p in sorted(set(candidates)):
        try:
            schema = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            die(f"Schema inválido (JSON) en {p}: {e}", 2)

        schema_id = schema.get("$id")
        if not schema_id:
            # Skip schemas without $id. They cannot be addressed by $ref via $id.
            continue

        # DRAFT202012 determines how anchors/ids are interpreted.
        resource = Resource.from_contents(schema, default_specification=DRAFT202012)
        resources.append((schema_id, resource))

    reg = Registry().with_resources(resources)
    return reg


def main() -> int:
    if len(sys.argv) != 3:
        die("Uso: scripts/validate_schema.py <schema.json> <data.json>", 2)

    schema_path = Path(sys.argv[1]).resolve()
    data_path = Path(sys.argv[2]).resolve()

    if not schema_path.exists():
        die(f"Schema no existe: {schema_path}", 2)
    if not data_path.exists():
        die(f"JSON no existe: {data_path}", 2)

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    data = json.loads(data_path.read_text(encoding="utf-8"))

    try:
        from jsonschema import Draft202012Validator
    except Exception as e:
        die(f"No puedo importar jsonschema. ¿Instalaste requirements-dev.txt? ({e})", 2)

    # Resolve backend root relative to this script: backend/scripts/validate_schema.py
    backend_root = Path(__file__).resolve().parents[1]
    schemas_root = backend_root / "schemas"

    registry = load_schema_registry(schemas_root)


    v = Draft202012Validator(
        schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
        registry=registry,
    )
    errors = sorted(v.iter_errors(data), key=lambda e: e.path)

    if errors:
        print(f"FAIL: {data_path} no cumple {schema_path}", file=sys.stderr)
        for e in errors[:50]:
            loc = ".".join([str(x) for x in e.path]) or "<root>"
            print(f"  - {loc}: {e.message}", file=sys.stderr)
        return 1

    print(f"OK: {data_path} cumple {schema_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())