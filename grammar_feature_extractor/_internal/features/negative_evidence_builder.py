from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    NegativeEvidence,
    NPFeature,
    PredicateFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def _window_for_ref(ctx: SentenceContext, ref: int, radius: int = 3) -> tuple[int, int]:
    ordered = sorted(ctx.refs)
    if not ordered:
        return (ref, ref)
    lo = max(ordered[0], ref - radius)
    hi = min(ordered[-1], ref + radius)
    return (lo, hi)


def _has_lemma_in_window(
    ctx: SentenceContext, window: tuple[int, int], lemma: str
) -> bool:
    lo, hi = window
    for ref in ctx.refs:
        if lo <= ref <= hi:
            word = ctx.word_by_ref[ref]
            if (word.lemma or word.text).casefold() == lemma:
                return True
    return False


def build_predicate_negative_evidence(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[NegativeEvidence, ...]:
    items: list[NegativeEvidence] = []
    for predicate in predicates:
        window = _window_for_ref(ctx, predicate.main, radius=3)
        for target, lemma in (
            ("auxiliary_do", "do"),
            ("auxiliary_have", "have"),
            ("negation_marker", "not"),
        ):
            if _has_lemma_in_window(ctx, window, lemma):
                continue
            items.append(
                NegativeEvidence(
                    target=target,
                    scope="predicate",
                    anchor_ref=predicate.main,
                    checked_window=window,
                    result="not_present",
                    confidence="high",
                    interpretation=None,
                )
            )
    return tuple(items)


def build_np_negative_evidence(
    ctx: SentenceContext,
    np_profiles: tuple[NPFeature, ...],
) -> tuple[NegativeEvidence, ...]:
    items: list[NegativeEvidence] = []
    for profile in np_profiles:
        if not getattr(profile, "head", None):
            continue
        head_ref = profile.head
        window = _window_for_ref(ctx, head_ref, radius=2)
        article_present = False
        for ref in ctx.refs:
            if window[0] <= ref < head_ref:
                word = ctx.word_by_ref[ref]
                if word.upos == "DET" or (word.lemma or word.text).casefold() in {
                    "a",
                    "an",
                    "the",
                }:
                    article_present = True
                    break
        if not article_present:
            items.append(
                NegativeEvidence(
                    target="article_before_np",
                    scope="np",
                    anchor_ref=head_ref,
                    checked_window=window,
                    result="not_present",
                    confidence="medium",
                    interpretation=None,
                )
            )
    return tuple(items)


__all__ = [
    "build_predicate_negative_evidence",
    "build_np_negative_evidence",
]
