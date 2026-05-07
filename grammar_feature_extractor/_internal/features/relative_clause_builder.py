from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    ClauseFeature,
    RelativeClauseFeature,
    RelativeMarkerText,
    RelativeType,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

_RELATIVE_MARKERS: dict[str, RelativeMarkerText] = {
    "who": "who",
    "whom": "whom",
    "whose": "whose",
    "which": "which",
    "that": "that",
    "where": "where",
}


def build_relative_clauses(
    ctx: SentenceContext,
    clauses: tuple[ClauseFeature, ...],
) -> tuple[RelativeClauseFeature, ...]:
    items: list[RelativeClauseFeature] = []
    for clause in clauses:
        if clause.type != "relcl":
            continue
        head_word = ctx.word_by_ref[clause.head]
        head_noun = head_word.head if head_word.head != 0 else clause.head
        marker_ref, marker_text = _find_marker(ctx, clause.head)
        relative_type = _relative_type(ctx, clause, marker_ref, marker_text)
        items.append(
            RelativeClauseFeature(
                clause_id=clause.id,
                head_noun=head_noun,
                relative_marker=marker_ref,
                marker_text=marker_text,
                relative_type=relative_type,
                restrictive=None,
                confidence="medium" if marker_ref is not None else "low",
            )
        )
    return tuple(items)


def _find_marker(
    ctx: SentenceContext,
    clause_head: int,
) -> tuple[int | None, RelativeMarkerText | None]:
    for child in ctx.children_by_head.get(clause_head, ()):
        word = ctx.word_by_ref[child]
        surface = word.text.casefold()
        if surface in _RELATIVE_MARKERS and word.deprel in {
            "nsubj",
            "nsubj:pass",
            "obj",
            "nmod:poss",
            "advmod",
            "obl",
            "mark",
        }:
            return child, _RELATIVE_MARKERS[surface]
    return None, None


def _relative_type(
    ctx: SentenceContext,
    clause: ClauseFeature,
    marker_ref: int | None,
    marker_text: RelativeMarkerText | None,
) -> RelativeType:
    if marker_text == "where":
        return "place_relative"
    if marker_text == "whose" or (
        marker_ref is not None
        and ctx.word_by_ref[marker_ref].deprel == "nmod:poss"
    ):
        return "possessive_relative"
    if marker_ref is not None:
        deprel = ctx.word_by_ref[marker_ref].deprel
        if deprel in {"nsubj", "nsubj:pass"}:
            return "subject_relative"
        if deprel in {"obj", "obl"}:
            return "object_relative"
    head_word = ctx.word_by_ref[clause.head]
    if head_word.upos == "VERB":
        feats = ctx.morph_by_ref[clause.head].features
        if feats.get("VerbForm") == "Part":
            return "reduced_participle_relative"
        if feats.get("VerbForm") == "Inf":
            return "reduced_to_infinitive_relative"
    return "unknown"


__all__ = ["build_relative_clauses"]
