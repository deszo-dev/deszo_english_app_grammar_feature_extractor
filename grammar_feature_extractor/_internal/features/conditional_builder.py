from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    ClauseFeature,
    ConditionalFeature,
    ConditionalType,
    Confidence,
    PredicateFeature,
    TAVMFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

_FALLBACK_TAVM = TAVMFeature(
    tense="unknown",
    aspect="unknown",
    voice="unknown",
    modality="unknown",
    form_signature="unknown",
)


def build_conditionals(
    ctx: SentenceContext,
    clauses: tuple[ClauseFeature, ...],
    predicates: tuple[PredicateFeature, ...],
) -> tuple[ConditionalFeature, ...]:
    items: list[ConditionalFeature] = []
    predicate_by_clause_head = {p.clause_head: p for p in predicates}
    predicate_by_main = {p.main: p for p in predicates}
    for clause in clauses:
        if clause.marker is None:
            continue
        marker_text = clause.marker.marker.casefold()
        if marker_text not in {"if", "unless"}:
            continue
        sub_predicate = _resolve_predicate(
            clause, predicate_by_clause_head, predicate_by_main
        )
        main_predicate = _find_main_predicate(ctx, clause, predicate_by_main)
        sub_tavm = sub_predicate.tavm if sub_predicate else _FALLBACK_TAVM
        main_tavm = main_predicate.tavm if main_predicate else _FALLBACK_TAVM
        conditional_type = _classify_type(marker_text, main_tavm, sub_tavm)
        confidence: Confidence = "medium" if conditional_type != "unknown" else "low"
        items.append(
            ConditionalFeature(
                if_clause=clause.id,
                main_clause=(
                    f"clause:{main_predicate.clause_head}"
                    if main_predicate is not None
                    else clause.id
                ),
                conditional_type=conditional_type,
                if_marker_ref=clause.marker.marker_ref,
                main_tavm=main_tavm,
                subordinate_tavm=sub_tavm,
                confidence=confidence,
            )
        )
    return tuple(items)


def _resolve_predicate(
    clause: ClauseFeature,
    by_clause_head: dict[int, PredicateFeature],
    by_main: dict[int, PredicateFeature],
) -> PredicateFeature | None:
    if clause.head in by_clause_head:
        return by_clause_head[clause.head]
    return by_main.get(clause.head)


def _find_main_predicate(
    ctx: SentenceContext,
    sub_clause: ClauseFeature,
    by_main: dict[int, PredicateFeature],
) -> PredicateFeature | None:
    parent = ctx.word_by_ref[sub_clause.head].head
    if parent == 0:
        return None
    return by_main.get(parent)


def _classify_type(
    marker_text: str,
    main: TAVMFeature,
    sub: TAVMFeature,
) -> ConditionalType:
    if marker_text == "unless":
        return "unless_conditional"
    if sub.tense == "present" and main.tense == "present":
        return "zero_conditional_candidate"
    if sub.tense == "present" and main.tense in {"present", "future_like"}:
        return "first_conditional_candidate"
    if sub.tense == "past" and main.modality in {
        "ability",
        "possibility",
        "advice",
        "conditional",
        "permission",
    }:
        return "second_conditional_candidate"
    if sub.tense == "past" and sub.aspect == "perfect" and main.aspect == "perfect":
        return "third_conditional_candidate"
    if sub.tense != "unknown" and main.tense != "unknown":
        return "mixed_conditional_candidate"
    return "unknown"


__all__ = ["build_conditionals"]
