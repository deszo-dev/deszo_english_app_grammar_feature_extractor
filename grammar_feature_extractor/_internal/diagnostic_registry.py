from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TypeAlias

DiagnosticCode: TypeAlias = str


@dataclass(frozen=True, slots=True)
class DiagnosticSpec:
    code: str
    severity: str
    when_emitted: str
    affected_entity: str
    refs_required: bool
    feature_path_required: bool
    message_template: str
    result_impact: str
    cli_exit_code: int
    stable_since: str
    exception: str | None = None
    cli_error_code: str | None = None
    fatal_exit_code: int | None = None
    deprecated_since: str | None = None


def _registry_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "schema"
        / "grammar_feature_extractor.v5"
        / "diagnostic_registry.v5.json"
    )


@lru_cache(maxsize=1)
def _load_registry() -> tuple[DiagnosticSpec, ...]:
    payload = json.loads(_registry_path().read_text(encoding="utf-8"))
    items: list[DiagnosticSpec] = []
    for entry in payload["codes"]:
        items.append(
            DiagnosticSpec(
                code=str(entry["code"]),
                severity=str(entry["severity"]),
                when_emitted=str(entry["when_emitted"]),
                affected_entity=str(entry["affected_entity"]),
                refs_required=bool(entry["refs_required"]),
                feature_path_required=bool(entry["feature_path_required"]),
                message_template=str(entry["message_template"]),
                result_impact=str(entry["result_impact"]),
                cli_exit_code=int(entry["cli_exit_code"]),
                stable_since=str(entry["stable_since"]),
                exception=entry.get("exception"),
                cli_error_code=entry.get("cli_error_code"),
                fatal_exit_code=entry.get("fatal_exit_code"),
                deprecated_since=entry.get("deprecated_since"),
            )
        )
    return tuple(items)


def all_diagnostics() -> tuple[DiagnosticSpec, ...]:
    return _load_registry()


def diagnostic_specs() -> Mapping[str, DiagnosticSpec]:
    return {spec.code: spec for spec in _load_registry()}


def is_fatal(code: str) -> bool:
    spec = diagnostic_specs().get(code)
    return spec is not None and spec.result_impact == "extraction_failed"


DIAGNOSTIC_CODES: tuple[str, ...] = tuple(spec.code for spec in _load_registry())
DIAGNOSTIC_CODE_SET: frozenset[str] = frozenset(DIAGNOSTIC_CODES)
