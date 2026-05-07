from __future__ import annotations

from grammar_feature_extractor._internal.features.dependency_helpers import sorted_refs
from grammar_feature_extractor._internal.models import (
    DirectSpeechSegmentFeature,
    DiscourseFeatures,
    NarrationSegmentFeature,
    NPFeature,
    PredicateFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

SPEECH_VERBS = {"say", "tell", "ask", "reply", "cry", "answer"}


def build_discourse_segments(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
    np_profiles: tuple[NPFeature, ...],
) -> DiscourseFeatures:
    quote_bounds = _quote_bounds(ctx)
    if quote_bounds is None:
        return DiscourseFeatures(quote_segmentation_status="unknown")
    start, end = quote_bounds
    quote_refs = tuple(ref for ref in ctx.refs if start <= ref <= end)
    narration_refs = tuple(ref for ref in ctx.refs if ref < start or ref > end)
    if not quote_refs:
        return DiscourseFeatures(quote_segmentation_status="unknown")
    speaker_predicate = _speaker_predicate(ctx, narration_refs, predicates)
    speaker_np_id = _speaker_np_id(speaker_predicate, np_profiles)
    evidence_refs = sorted_refs([*quote_refs, *narration_refs])
    direct = DirectSpeechSegmentFeature(
        segment_id="quote-1",
        token_refs=quote_refs,
        speaker_tag_predicate_id=(
            speaker_predicate.id if speaker_predicate is not None else None
        ),
        speaker_np_id=speaker_np_id,
        quote_type="direct_speech",
        source="quote_surface_heuristic",
        confidence="high" if speaker_predicate is not None else "medium",
        evidence_refs=evidence_refs,
    )
    narration = (
        NarrationSegmentFeature(
            segment_id="narr-1",
            token_refs=narration_refs,
            source="quote_surface_heuristic",
            confidence="high",
            evidence_refs=narration_refs,
        )
        if narration_refs
        else None
    )
    return DiscourseFeatures(
        quote_segmentation_status="complete" if narration is not None else "partial",
        direct_speech_segments=(direct,),
        narration_segments=(narration,) if narration is not None else (),
    )


def _quote_bounds(ctx: SentenceContext) -> tuple[int, int] | None:
    quote_refs = [
        ref
        for ref in ctx.refs
        if ctx.word_by_ref[ref].text.startswith(('"', "“", "'"))
        or ctx.word_by_ref[ref].text.endswith(('"', "”", "'"))
    ]
    if len(quote_refs) < 2:
        return None
    return min(quote_refs), max(quote_refs)


def _speaker_predicate(
    ctx: SentenceContext,
    narration_refs: tuple[int, ...],
    predicates: tuple[PredicateFeature, ...],
) -> PredicateFeature | None:
    narration_set = set(narration_refs)
    for predicate in predicates:
        lemma = predicate.main_lemma.casefold()
        if lemma in SPEECH_VERBS and predicate.main in narration_set:
            return predicate
    for predicate in predicates:
        if predicate.main in narration_set:
            return predicate
    return None


def _speaker_np_id(
    predicate: PredicateFeature | None,
    np_profiles: tuple[NPFeature, ...],
) -> str | None:
    if predicate is None or predicate.subject is None:
        return None
    for np in np_profiles:
        if np.head == predicate.subject:
            return np.id
    return None


__all__ = ["build_discourse_segments"]
