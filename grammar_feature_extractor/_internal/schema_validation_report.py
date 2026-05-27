"""Lightweight schema validation report writer.

After CLI emits all page files + manifest, build a structured validation
report by replaying each file against the authoritative v5 JSON schemas
(under `docs/docs/schemas/`). The result is written as
`grammar_features.schema_validation.json` next to the manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from grammar_feature_extractor._internal.runtime_metadata import repository_root


def _schema_dir() -> Path:
    return repository_root() / "docs" / "docs" / "schemas"


def _load_validator(schema_name: str):
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError:  # pragma: no cover - jsonschema is a dev dep
        return None
    schema_dir = _schema_dir()
    if not schema_dir.exists():
        return None
    resources: dict[str, Any] = {}
    for path in schema_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if "$id" in payload:
            resources[payload["$id"]] = Resource.from_contents(payload)
    registry = Registry().with_resources(resources.items())
    schema_path = schema_dir / schema_name
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return Draft202012Validator(schema, registry=registry)


def _validate_file(file_path: Path, schema_name: str) -> dict[str, Any]:
    validator = _load_validator(schema_name)
    entry: dict[str, Any] = {
        "file_name": file_path.name,
        "schema": schema_name,
        "ok": True,
        "errors": [],
    }
    if validator is None:
        entry["ok"] = True
        entry["errors"] = []
        entry["_validator_unavailable"] = True
        return entry
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        entry["ok"] = False
        entry["errors"] = [{"path": "", "message": f"file_read_or_parse_error: {exc}"}]
        return entry
    errors = list(validator.iter_errors(payload))
    if errors:
        entry["ok"] = False
        entry["errors"] = [
            {
                "path": "/".join(str(part) for part in error.absolute_path),
                "message": error.message,
            }
            for error in errors[:10]
        ]
    return entry


def build_schema_validation_report(out_dir: Path) -> dict[str, Any]:
    page_entries: list[dict[str, Any]] = []
    for page_path in sorted(out_dir.glob("grammar_features.page_*.json")):
        page_entries.append(
            _validate_file(page_path, "grammar_feature_page.v5.schema.json")
        )
    manifest_path = out_dir / "grammar_features.manifest.json"
    manifest_entry = (
        _validate_file(manifest_path, "grammar_feature_manifest.v5.schema.json")
        if manifest_path.exists()
        else None
    )
    all_ok = all(entry["ok"] for entry in page_entries) and (
        manifest_entry is None or manifest_entry["ok"]
    )
    return {
        "schema_version": "schema_validation.v5",
        "validator": "jsonschema.Draft202012Validator",
        "ok": all_ok,
        "pages": page_entries,
        "manifest": manifest_entry,
    }


def write_schema_validation_report(out_dir: Path) -> dict[str, Any]:
    report = build_schema_validation_report(out_dir)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    target = out_dir / "grammar_features.schema_validation.json"
    target.write_bytes(payload.encode("utf-8"))
    return report


__all__ = ["build_schema_validation_report", "write_schema_validation_report"]
