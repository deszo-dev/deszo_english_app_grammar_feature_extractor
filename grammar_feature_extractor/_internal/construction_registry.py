from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TypeAlias

ConstructionSignature: TypeAlias = str


@dataclass(frozen=True, slots=True)
class ConstructionSlotSpec:
    name: str
    required: bool
    value_type: str
    allowed_values: tuple[object, ...] | None = None


@dataclass(frozen=True, slots=True)
class ConstructionSignatureSpec:
    signature: str
    type: str
    family_hint: str | None
    allowed_provenance_tiers: tuple[str, ...]
    confidence_rules: tuple[str, ...]
    examples: tuple[str, ...]
    stable_since: str
    deprecated_since: str | None
    slots: tuple[ConstructionSlotSpec, ...]


def _registry_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "schema"
        / "grammar_feature_extractor.v5"
        / "construction_signature_registry.v5.json"
    )


@lru_cache(maxsize=1)
def _load_registry() -> tuple[ConstructionSignatureSpec, ...]:
    payload = json.loads(_registry_path().read_text(encoding="utf-8"))
    items: list[ConstructionSignatureSpec] = []
    for entry in payload["signatures"]:
        slots = tuple(
            ConstructionSlotSpec(
                name=slot["name"],
                required=bool(slot["required"]),
                value_type=str(slot["value_type"]),
                allowed_values=(
                    tuple(slot["allowed_values"])
                    if isinstance(slot.get("allowed_values"), list)
                    else None
                ),
            )
            for slot in entry.get("slots", [])
        )
        items.append(
            ConstructionSignatureSpec(
                signature=str(entry["signature"]),
                type=str(entry["type"]),
                family_hint=entry.get("family_hint"),
                allowed_provenance_tiers=tuple(entry.get("allowed_provenance_tiers", ())),
                confidence_rules=tuple(entry.get("confidence_rules", ())),
                examples=tuple(entry.get("examples", ())),
                stable_since=str(entry["stable_since"]),
                deprecated_since=entry.get("deprecated_since"),
                slots=slots,
            )
        )
    return tuple(items)


def all_signatures() -> tuple[ConstructionSignatureSpec, ...]:
    return _load_registry()


def signature_specs() -> Mapping[str, ConstructionSignatureSpec]:
    return {spec.signature: spec for spec in _load_registry()}


def slots_for(signature: str) -> tuple[ConstructionSlotSpec, ...] | None:
    spec = signature_specs().get(signature)
    return spec.slots if spec is not None else None


REGISTERED_CONSTRUCTION_SIGNATURES: tuple[str, ...] = tuple(
    spec.signature for spec in _load_registry()
)
REGISTERED_CONSTRUCTION_SIGNATURE_SET: frozenset[str] = frozenset(
    REGISTERED_CONSTRUCTION_SIGNATURES
)

SUBJECT_BE_PRESENT_COMPLEMENT = "subject_be_present_complement"
SUBJECT_BE_PRESENT_NOT_COMPLEMENT = "subject_be_present_not_complement"
BE_SUBJECT_COMPLEMENT_QUESTION = "be_subject_complement_question"
THERE_BE_NP = "there_be_np"
THERE_BE_NOT_ANY_NP = "there_be_not_any_np"
PRESENT_SIMPLE_LEXICAL_AFFIRMATIVE = "present_simple_lexical_affirmative"
PRESENT_SIMPLE_DO_NEGATIVE = "present_simple_do_negative"
PRESENT_SIMPLE_DO_QUESTION = "present_simple_do_question"
PRESENT_PROGRESSIVE_AFFIRMATIVE = "present_progressive_affirmative"
PRESENT_PERFECT_HAVE_PARTICIPLE = "present_perfect_have_participle"
PRESENT_PERFECT_EVER_QUESTION = "present_perfect_ever_question"
PAST_SIMPLE_REGULAR = "past_simple_regular"
MODAL_MUST_BASE = "modal_must_base"
SEMI_MODAL_BE_ABLE_TO = "semi_modal_be_able_to"
PASSIVE_BE_PARTICIPLE = "passive_be_participle"
TO_INFINITIVE_AFTER_ADJECTIVE = "to_infinitive_after_adjective"
GERUND_AFTER_PREPOSITION = "gerund_after_preposition"
COMPARATIVE_MORE_THAN = "comparative_more_than"
COMPARISON_AS_AS = "comparison_as_as"
DEMONSTRATIVE_THIS_SINGULAR_NP = "demonstrative_this_singular_np"
ARTICLE_INDEFINITE_A_NP = "article_indefinite_a_np"
ARTICLE_INDEFINITE_AN_NP = "article_indefinite_an_np"
ARTICLE_DEFINITE_THE_NP = "article_definite_the_np"
ZERO_ARTICLE_PLURAL_GENERIC_CANDIDATE = "zero_article_plural_generic_candidate"
