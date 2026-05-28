"""Construction emitters for progressive/perfect-progressive/passive clauses.

Maps a predicate's `form_signature` to a downstream-ready
`ConstructionFeature` with slot structure suitable for GrammarRule
generation.
"""

from __future__ import annotations

from grammar_feature_extractor._internal.construction_registry import (
    MODAL_PERFECT_PROGRESSIVE_CLAUSE,
    MODAL_PROGRESSIVE_CLAUSE,
    PAST_PERFECT_PASSIVE_CLAUSE,
    PAST_PERFECT_PROGRESSIVE_CLAUSE,
    PAST_PROGRESSIVE_CLAUSE,
    PRESENT_PERFECT_PASSIVE_CLAUSE,
    PRESENT_PERFECT_PROGRESSIVE_CLAUSE,
    PRESENT_PROGRESSIVE_CLAUSE,
    PROGRESSIVE_PASSIVE_CLAUSE,
)
from grammar_feature_extractor._internal.models import (
    ConstructionFeature,
    PredicateFeature,
    SlotValue,
)
from grammar_feature_extractor._internal.proof_surface import make_provenance


_SIGNATURE_BY_FORM: dict[str, tuple[str, str]] = {
    # form_signature -> (construction signature, family_hint)
    "present_progressive": (PRESENT_PROGRESSIVE_CLAUSE, "present_progressive"),
    "past_progressive": (PAST_PROGRESSIVE_CLAUSE, "past_progressive"),
    "modal_progressive": (MODAL_PROGRESSIVE_CLAUSE, "modal_progressive"),
    "future_progressive": (MODAL_PROGRESSIVE_CLAUSE, "future_progressive"),
    "present_perfect_progressive": (
        PRESENT_PERFECT_PROGRESSIVE_CLAUSE,
        "present_perfect_progressive",
    ),
    "past_perfect_progressive": (
        PAST_PERFECT_PROGRESSIVE_CLAUSE,
        "past_perfect_progressive",
    ),
    "modal_perfect_progressive": (
        MODAL_PERFECT_PROGRESSIVE_CLAUSE,
        "modal_perfect_progressive",
    ),
    "present_perfect_passive": (
        PRESENT_PERFECT_PASSIVE_CLAUSE,
        "present_perfect_passive",
    ),
    "past_perfect_passive": (
        PAST_PERFECT_PASSIVE_CLAUSE,
        "past_perfect_passive",
    ),
    "present_progressive_passive": (
        PROGRESSIVE_PASSIVE_CLAUSE,
        "progressive_passive",
    ),
    "past_progressive_passive": (
        PROGRESSIVE_PASSIVE_CLAUSE,
        "progressive_passive",
    ),
    "perfect_progressive_passive": (
        PROGRESSIVE_PASSIVE_CLAUSE,
        "perfect_progressive_passive",
    ),
}


def _slot_value(ref: int | None) -> SlotValue | None:
    return ref if ref is not None else None


def build_progressive_constructions(
    predicates: tuple[PredicateFeature, ...],
) -> tuple[ConstructionFeature, ...]:
    items: list[ConstructionFeature] = []
    for index, predicate in enumerate(predicates):
        mapping = _SIGNATURE_BY_FORM.get(predicate.form_signature or "")
        if mapping is None:
            continue
        construction_signature, family_hint = mapping
        if "passive" in construction_signature:
            construction_type = "passive"
        else:
            construction_type = "tense_aspect"
        slots: dict[str, SlotValue] = {
            "predicate": predicate.main,
            "main_verb": predicate.main,
        }
        if predicate.subject is not None:
            slots["subject"] = predicate.subject
        chain = predicate.aux_chain
        if chain is not None:
            if chain.finite_anchor_ref is not None:
                slots["finite_aux"] = chain.finite_anchor_ref
            if chain.modal_ref is not None:
                slots["modal"] = chain.modal_ref
            if chain.perfect_aux_ref is not None:
                slots["perfect_aux"] = chain.perfect_aux_ref
            if chain.progressive_aux_ref is not None:
                slots["progressive_aux"] = chain.progressive_aux_ref
            if chain.passive_aux_ref is not None:
                slots["passive_aux"] = chain.passive_aux_ref
            slots["main_verb_form"] = chain.main_verb_form
        if predicate.negation is not None:
            slots["negation"] = predicate.negation
        evidence_refs = tuple(predicate.evidence_refs)
        items.append(
            ConstructionFeature(
                key=f"{construction_signature}.{index}",
                family_hint=family_hint,
                type=construction_type,
                signature=construction_signature,
                slots=slots,
                evidence_refs=evidence_refs,
                confidence=predicate.confidence or "high",
                provenance=make_provenance(
                    "deterministic",
                    "dependency",
                    evidence_refs,
                    predicate.confidence or "high",
                ),
            )
        )
    return tuple(items)


__all__ = ["build_progressive_constructions"]
