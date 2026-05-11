from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SemanticValidationSpec:
    code: str
    phase: str
    exception: str
    cli_error_code: str
    exit_code: int
    stable_since: str
    when_emitted: str
    affected_entity: str
    message_template: str
    required_details: tuple[str, ...]
    test_case: str | None
    deprecated_since: str | None


def _registry_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "schema"
        / "grammar_feature_extractor.v5"
        / "semantic_validation_registry.v5.json"
    )


@lru_cache(maxsize=1)
def _load_registry() -> tuple[SemanticValidationSpec, ...]:
    payload = json.loads(_registry_path().read_text(encoding="utf-8"))
    items = tuple(
        SemanticValidationSpec(
            code=str(entry["code"]),
            phase=str(entry["phase"]),
            exception=str(entry["exception"]),
            cli_error_code=str(entry["cli_error_code"]),
            exit_code=int(entry["exit_code"]),
            stable_since=str(entry["stable_since"]),
            when_emitted=str(entry["when_emitted"]),
            affected_entity=str(entry["affected_entity"]),
            message_template=str(entry["message_template"]),
            required_details=tuple(entry.get("required_details", ())),
            test_case=entry.get("test_case"),
            deprecated_since=entry.get("deprecated_since"),
        )
        for entry in payload["codes"]
    )
    return items


def all_codes() -> tuple[SemanticValidationSpec, ...]:
    return _load_registry()


def semantic_specs() -> Mapping[str, SemanticValidationSpec]:
    return {spec.code: spec for spec in _load_registry()}


def entry(code: str) -> SemanticValidationSpec | None:
    return semantic_specs().get(code)


REGISTERED_SEMANTIC_CODES: tuple[str, ...] = tuple(
    spec.code for spec in _load_registry()
)
REGISTERED_SEMANTIC_CODE_SET: frozenset[str] = frozenset(REGISTERED_SEMANTIC_CODES)
