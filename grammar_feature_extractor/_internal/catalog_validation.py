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
REGISTERED_ENUM_VALUES = {
    "Polarity": frozenset({"positive", "negative", "mixed", "unknown"}),
    "PredicateType": frozenset(
        {
            "verbal",
            "copular_adjectival",
            "copular_nominal",
            "copular_prepositional",
            "existential_there",
            "unknown",
        }
    ),
    "ModalType": frozenset(
        {
            "can_ability",
            "could_ability",
            "may_permission",
            "might_possibility",
            "must_obligation",
            "must_deduction",
            "should_advice",
            "will_prediction",
            "would_conditional",
            "shall_prediction",
            "have_to_obligation",
            "need_to_necessity",
            "be_able_to_ability",
            "be_supposed_to_expectation",
            "used_to_past_habit",
            "unknown",
        }
    ),
}


def validate_catalog_projection(catalog: Mapping[str, object]) -> None:
    for path in _string_array(catalog.get("feature_paths", []), "feature_paths"):
        if path not in REGISTERED_FEATURE_PATHS:
            raise ConfigurationError(f"Unknown feature path in catalog: {path}.")
    for signature in _string_array(
        catalog.get("construction_signatures", []),
        "construction_signatures",
    ):
        _validate_signature(signature)
    enum_values = catalog.get("enum_values", {})
    if enum_values:
        if not isinstance(enum_values, Mapping):
            raise ConfigurationError("enum_values must be an object.")
        for enum_name, values in enum_values.items():
            if not isinstance(enum_name, str):
                raise ConfigurationError("enum_values keys must be strings.")
            _validate_enum_values(enum_name, _string_array(values, enum_name))


def _validate_signature(signature: str) -> None:
    if signature not in REGISTERED_CONSTRUCTION_SIGNATURES:
        raise ConfigurationError(f"Unknown construction signature: {signature}.")


def _validate_enum_values(enum_name: str, values: tuple[str, ...]) -> None:
    if enum_name not in REGISTERED_ENUM_VALUES:
        raise ConfigurationError(f"Unknown registered enum: {enum_name}.")
    registered = REGISTERED_ENUM_VALUES[enum_name]
    for value in values:
        if value not in registered:
            raise ConfigurationError(f"Unknown {enum_name} value: {value}.")


def _string_array(value: object, path: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{path} must be an array.")
    if not all(isinstance(item, str) for item in value):
        raise ConfigurationError(f"{path} must contain only strings.")
    return tuple(value)
