from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FeaturePathSpec:
    path: str
    value_type: str
    cardinality: str
    proof_relevant: bool
    allowed_operators: tuple[str, ...]
    enum_values: tuple[object, ...] | None
    stable_since: str
    deprecated_since: str | None


def _registry_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "schema"
        / "grammar_feature_extractor.v5"
        / "feature_path_registry.v5.json"
    )


@lru_cache(maxsize=1)
def _load_registry() -> tuple[FeaturePathSpec, ...]:
    payload = json.loads(_registry_path().read_text(encoding="utf-8"))
    items: list[FeaturePathSpec] = []
    for entry in payload["paths"]:
        enum_values = entry.get("enum_values")
        items.append(
            FeaturePathSpec(
                path=str(entry["path"]),
                value_type=str(entry["value_type"]),
                cardinality=str(entry["cardinality"]),
                proof_relevant=bool(entry["proof_relevant"]),
                allowed_operators=tuple(entry.get("allowed_operators", ())),
                enum_values=(
                    tuple(enum_values) if isinstance(enum_values, list) else None
                ),
                stable_since=str(entry["stable_since"]),
                deprecated_since=entry.get("deprecated_since"),
            )
        )
    return tuple(items)


def all_paths() -> Mapping[str, FeaturePathSpec]:
    return {spec.path: spec for spec in _load_registry()}


def is_registered(path: str) -> bool:
    return path in all_paths()


REGISTERED_FEATURE_PATHS: tuple[str, ...] = tuple(
    spec.path for spec in _load_registry()
)
REGISTERED_FEATURE_PATH_SET: frozenset[str] = frozenset(REGISTERED_FEATURE_PATHS)
