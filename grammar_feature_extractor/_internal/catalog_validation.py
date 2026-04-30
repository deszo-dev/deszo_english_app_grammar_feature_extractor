from __future__ import annotations

from collections.abc import Mapping

from grammar_feature_extractor._internal.construction_registry import (
    REGISTERED_CONSTRUCTION_SIGNATURES,
)
from grammar_feature_extractor._internal.errors import ConfigurationError

REGISTERED_FEATURE_PATHS = frozenset(
    {
        "evidence.words",
        "morphology.normalized",
        "syntax.clauses",
        "syntax.predicates",
        "syntax.np_profiles",
        "lexical.sentence",
        "lexical.word_order",
        "lexical.negation",
        "constructions",
        "absences",
        "contrastive_support",
        "diagnostics",
    }
)


def validate_catalog_projection(catalog: Mapping[str, object]) -> None:
    for path in _string_array(catalog.get("feature_paths", []), "feature_paths"):
        if path not in REGISTERED_FEATURE_PATHS:
            raise ConfigurationError(f"Unknown feature path in catalog: {path}.")
    for signature in _string_array(
        catalog.get("construction_signatures", []),
        "construction_signatures",
    ):
        _validate_signature(signature)


def _validate_signature(signature: str) -> None:
    if signature not in REGISTERED_CONSTRUCTION_SIGNATURES:
        raise ConfigurationError(f"Unknown construction signature: {signature}.")


def _string_array(value: object, path: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{path} must be an array.")
    if not all(isinstance(item, str) for item in value):
        raise ConfigurationError(f"{path} must contain only strings.")
    return tuple(value)
