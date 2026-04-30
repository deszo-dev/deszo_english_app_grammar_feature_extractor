from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    ClauseMarkerFeature,
    Confidence,
    MarkerType,
)
from grammar_feature_extractor._internal.proof_surface import make_provenance
from grammar_feature_extractor._internal.sentence_context import SentenceContext

PREPOSITIONAL_GERUND_MARKERS = frozenset({"in", "of", "by", "with", "without"})


def build_subordination(ctx: SentenceContext) -> tuple[ClauseMarkerFeature, ...]:
    markers: list[ClauseMarkerFeature] = []
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        if word.deprel != "mark" or word.head not in ctx.word_by_ref:
            continue
        head = ctx.word_by_ref[word.head]
        if _clause_type(head.deprel) is None:
            continue
        marker_type, confidence = _marker_type(ctx, ref)
        markers.append(
            ClauseMarkerFeature(
                marker_ref=ref,
                marker=word.text,
                clause_head=word.head,
                marker_type=marker_type,
                confidence=confidence,
                sources=("dependency",),
                provenance=make_provenance(
                    "deterministic", "dependency", (ref, word.head), confidence
                ),
            )
        )
    return tuple(markers)


def marker_by_clause_head(
    markers: tuple[ClauseMarkerFeature, ...],
) -> dict[int, ClauseMarkerFeature]:
    return {marker.clause_head: marker for marker in markers}


def _marker_type(
    ctx: SentenceContext,
    marker_ref: int,
) -> tuple[MarkerType, Confidence]:
    marker = ctx.word_by_ref[marker_ref]
    head = ctx.word_by_ref[marker.head]
    head_morph = ctx.morph_by_ref[marker.head].features
    lower = marker.text.casefold()
    if lower == "to":
        if head_morph.get("VerbForm") == "Inf" or head.upos == "VERB":
            return "infinitive_to", "high"
        return "ambiguous", "low"
    if lower == "than":
        return "comparative_than", "high"
    if lower == "if":
        return "conditional_if", "high"
    if lower == "unless":
        return "conditional_unless", "high"
    if lower == "that":
        return "reported_that", "medium"
    if lower in PREPOSITIONAL_GERUND_MARKERS and head_morph.get("VerbForm") == "Ger":
        return "prepositional_gerund", "medium"
    if lower in {"because", "when", "while", "although", "as", "whether"}:
        return "finite_subordinator", "high"
    return "ambiguous", "low"


def _clause_type(deprel: str) -> str | None:
    if deprel == "root":
        return "root"
    if deprel == "acl:relcl":
        return "relcl"
    if deprel in {"ccomp", "xcomp", "advcl", "acl"}:
        return deprel
    return None
