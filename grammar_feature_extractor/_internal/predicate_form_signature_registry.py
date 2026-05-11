from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PredicateFormSignatureSpec:
    signature: str
    stable_since: str
    description: str
    deprecated_since: str | None


def _registry_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "schema"
        / "grammar_feature_extractor.v5"
        / "predicate_form_signature_registry.v5.json"
    )


@lru_cache(maxsize=1)
def _load_registry() -> tuple[PredicateFormSignatureSpec, ...]:
    payload = json.loads(_registry_path().read_text(encoding="utf-8"))
    items = tuple(
        PredicateFormSignatureSpec(
            signature=str(entry["signature"]),
            stable_since=str(entry["stable_since"]),
            description=str(entry["description"]),
            deprecated_since=entry.get("deprecated_since"),
        )
        for entry in payload["form_signatures"]
    )
    return items


def all_form_signatures() -> tuple[PredicateFormSignatureSpec, ...]:
    return _load_registry()


def form_signature_specs() -> Mapping[str, PredicateFormSignatureSpec]:
    return {spec.signature: spec for spec in _load_registry()}


def is_registered(signature: str) -> bool:
    return signature in form_signature_specs()


REGISTERED_FORM_SIGNATURES: tuple[str, ...] = tuple(
    spec.signature for spec in _load_registry()
)
REGISTERED_FORM_SIGNATURE_SET: frozenset[str] = frozenset(REGISTERED_FORM_SIGNATURES)
