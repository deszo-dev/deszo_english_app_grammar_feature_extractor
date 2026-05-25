from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    AdjectivePattern,
    AdjectivePatternFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def _has_child_lemma(ctx: SentenceContext, head: int, lemma: str) -> int | None:
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        if word.head != head:
            continue
        if (word.lemma or word.text).casefold() == lemma:
            return ref
    return None


def _children(ctx: SentenceContext, head: int) -> list[int]:
    return [ref for ref in ctx.refs if ctx.word_by_ref[ref].head == head]


def _classify_adjective(
    ctx: SentenceContext, adj_ref: int
) -> tuple[AdjectivePattern, int | None]:
    children = _children(ctx, adj_ref)
    has_to_inf = False
    has_gerund = False
    has_that = False
    has_than = False
    has_as = False
    has_too = False
    has_enough = False
    degree_modifier: int | None = None

    for child_ref in children:
        child = ctx.word_by_ref[child_ref]
        lemma = (child.lemma or child.text).casefold()
        if lemma == "to" and child.upos == "PART":
            has_to_inf = True
        if child.upos == "VERB" and child.deprel in ("xcomp", "advcl"):
            has_to_inf = True
        if child.upos == "VERB" and (child.lemma or child.text).endswith("ing"):
            has_gerund = True
        if lemma == "that":
            has_that = True
        if lemma == "than":
            has_than = True
        if lemma == "as":
            has_as = True
        if lemma == "too":
            has_too = True
            degree_modifier = child_ref
        if lemma == "enough":
            has_enough = True
            degree_modifier = child_ref

    if has_too and has_to_inf:
        return "too_adjective_to_infinitive", degree_modifier
    if has_enough and has_to_inf:
        return "adjective_enough_to_infinitive", degree_modifier
    if has_to_inf:
        return "adjective_to_infinitive", degree_modifier
    if has_gerund:
        return "adjective_preposition_gerund", degree_modifier
    if has_that:
        return "adjective_that_clause", degree_modifier
    if has_than:
        return "comparative_adjective_than", degree_modifier
    if has_as:
        return "as_adjective_as", degree_modifier
    return "unknown", degree_modifier


def build_adjective_patterns(
    ctx: SentenceContext,
) -> tuple[AdjectivePatternFeature, ...]:
    items: list[AdjectivePatternFeature] = []
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        if word.upos != "ADJ":
            continue
        pattern, degree_modifier = _classify_adjective(ctx, ref)
        if pattern == "unknown":
            continue
        items.append(
            AdjectivePatternFeature(
                adjective=ref,
                lemma=(word.lemma or word.text).casefold(),
                pattern=pattern,
                complement=None,
                degree_modifier=degree_modifier,
                confidence="medium",
            )
        )
    return tuple(items)


__all__ = ["build_adjective_patterns"]
