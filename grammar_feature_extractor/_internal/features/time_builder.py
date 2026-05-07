from __future__ import annotations

from dataclasses import replace

from grammar_feature_extractor._internal.features.dependency_helpers import sorted_refs
from grammar_feature_extractor._internal.models import (
    FutureMarkingFeature,
    MultiwordCueFeature,
    PredicateFeature,
    TimeExpressionFeature,
    TimeKind,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

SINGLE_TIME_KINDS: dict[str, TimeKind] = {
    "tomorrow": "future_specific",
    "now": "present_now",
    "today": "present_or_current_day",
    "yesterday": "past_specific",
    "often": "habitual_frequency",
    "usually": "habitual_frequency",
    "always": "habitual_frequency",
    "sometimes": "habitual_frequency",
    "never": "habitual_frequency",
}
PERIODS = {"night", "week", "month", "year"}


def build_time_expressions(ctx: SentenceContext) -> tuple[TimeExpressionFeature, ...]:
    items: list[TimeExpressionFeature] = []
    used: set[int] = set()
    next_id = 1
    lowers = tuple(ctx.word_by_ref[ref].text.casefold() for ref in ctx.refs)
    for index, lower in enumerate(lowers):
        ref = ctx.refs[index]
        if ref in used:
            continue
        if lower in {"last", "next"} and index + 1 < len(lowers):
            following = lowers[index + 1]
            if following in PERIODS:
                refs = (ref, ctx.refs[index + 1])
                kind: TimeKind = (
                    "past_specific" if lower == "last" else "future_specific"
                )
                items.append(_time(next_id, ctx, refs, kind))
                used.update(refs)
                next_id += 1
                continue
        if lower == "ago":
            items.append(_time(next_id, ctx, (ref,), "past_offset"))
            used.add(ref)
            next_id += 1
            continue
        lexical_kind = SINGLE_TIME_KINDS.get(lower)
        if lexical_kind is not None:
            items.append(_time(next_id, ctx, (ref,), lexical_kind))
            used.add(ref)
            next_id += 1
    return tuple(items)


def attach_future_marking(
    predicates: tuple[PredicateFeature, ...],
    cues: tuple[MultiwordCueFeature, ...],
    time_expressions: tuple[TimeExpressionFeature, ...],
) -> tuple[PredicateFeature, ...]:
    future_time_ids = tuple(
        item.id for item in time_expressions if item.time_kind == "future_specific"
    )
    future_time_refs = tuple(
        ref
        for item in time_expressions
        if item.time_kind == "future_specific"
        for ref in item.token_refs
    )
    going_to_owner_ids = {
        cue.scope_owner_id
        for cue in cues
        if cue.cue_key == "going_to" and cue.scope_owner_id is not None
    }
    result: list[PredicateFeature] = []
    for predicate in predicates:
        will_shall_refs = tuple(
            aux.ref for aux in predicate.auxiliaries if aux.lemma in {"will", "shall"}
        )
        be_going_to = predicate.id in going_to_owner_ids
        if not be_going_to and not will_shall_refs and not future_time_ids:
            result.append(predicate)
            continue
        evidence_refs = sorted_refs(
            [predicate.main, *will_shall_refs, *future_time_refs]
        )
        if be_going_to:
            evidence_refs = sorted_refs(
                [
                    *evidence_refs,
                    *(
                        ref
                        for cue in cues
                        if cue.scope_owner_id == predicate.id
                        and cue.cue_key == "going_to"
                        for ref in cue.surface_refs
                    ),
                ]
            )
        result.append(
            replace(
                predicate,
                future_marking=FutureMarkingFeature(
                    be_going_to=be_going_to,
                    will_shall=bool(will_shall_refs),
                    future_time_expression_ids=future_time_ids,
                    future_orientation=(
                        "explicit_future"
                        if be_going_to or will_shall_refs or future_time_ids
                        else "unknown"
                    ),
                    source=(
                        "heuristic"
                        if be_going_to and future_time_ids
                        else "morphology"
                    ),
                    confidence="high" if be_going_to or will_shall_refs else "medium",
                    evidence_refs=evidence_refs,
                ),
            )
        )
    return tuple(result)


def _time(
    index: int,
    ctx: SentenceContext,
    refs: tuple[int, ...],
    kind: str,
) -> TimeExpressionFeature:
    return TimeExpressionFeature(
        id=f"time-{index}",
        token_refs=refs,
        surface=" ".join(ctx.word_by_ref[ref].text for ref in refs),
        time_kind=kind,  # type: ignore[arg-type]
        source="curated_lexical_time_list",
        confidence="high",
        evidence_refs=refs,
    )


__all__ = ["attach_future_marking", "build_time_expressions"]
