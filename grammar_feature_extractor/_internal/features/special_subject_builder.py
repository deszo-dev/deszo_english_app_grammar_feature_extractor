from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    PredicateFeature,
    SpecialSubjectConstructionFeature,
    SpecialSubjectType,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

_WEATHER_LEMMAS = frozenset(
    {"rain", "snow", "hail", "thunder", "drizzle", "pour", "sleet"}
)


def build_special_subject_constructions(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[SpecialSubjectConstructionFeature, ...]:
    items: list[SpecialSubjectConstructionFeature] = []
    for predicate in predicates:
        feature = _classify(ctx, predicate)
        if feature is not None:
            items.append(feature)
    return tuple(items)


def _classify(
    ctx: SentenceContext,
    predicate: PredicateFeature,
) -> SpecialSubjectConstructionFeature | None:
    subject_ref = predicate.subject
    if subject_ref is None:
        return None
    subject_word = ctx.word_by_ref[subject_ref]
    surface = subject_word.text.casefold()
    deprel = subject_word.deprel

    if surface == "there" and deprel == "expl":
        notional = _find_notional_subject(ctx, predicate)
        return SpecialSubjectConstructionFeature(
            type="existential_there",
            subject_ref=subject_ref,
            predicate_ref=predicate.main,
            notional_subject=notional,
            agreement_controller=notional,
            evidence_refs=tuple(
                sorted({subject_ref, predicate.main, *(r for r in (notional,) if r)})
            ),
            confidence="high",
        )

    if surface == "it" and deprel == "expl":
        return SpecialSubjectConstructionFeature(
            type="dummy_it_extraposition",
            subject_ref=subject_ref,
            predicate_ref=predicate.main,
            notional_subject=None,
            agreement_controller=subject_ref,
            evidence_refs=(subject_ref, predicate.main),
            confidence="medium",
        )

    if surface == "it" and (
        predicate.main_lemma in _WEATHER_LEMMAS
        or _is_weather_complement(ctx, predicate)
    ):
        return SpecialSubjectConstructionFeature(
            type="dummy_it_weather",
            subject_ref=subject_ref,
            predicate_ref=predicate.main,
            notional_subject=None,
            agreement_controller=subject_ref,
            evidence_refs=(subject_ref, predicate.main),
            confidence="medium",
        )

    if (
        surface == "it"
        and predicate.copula is not None
        and _has_relative_clause_dependent(ctx, predicate)
    ):
        return SpecialSubjectConstructionFeature(
            type="cleft_it",
            subject_ref=subject_ref,
            predicate_ref=predicate.main,
            notional_subject=None,
            agreement_controller=subject_ref,
            evidence_refs=(subject_ref, predicate.main),
            confidence="low",
        )

    return None


def _find_notional_subject(
    ctx: SentenceContext, predicate: PredicateFeature
) -> int | None:
    main_ref = predicate.main
    children = ctx.children_by_head.get(main_ref, ())
    for child in children:
        word = ctx.word_by_ref[child]
        if word.deprel in {"nsubj", "obj", "obl", "attr"} and word.upos in {
            "NOUN",
            "PROPN",
            "PRON",
            "NUM",
        }:
            return child
    return None


def _is_weather_complement(ctx: SentenceContext, predicate: PredicateFeature) -> bool:
    if predicate.copula is None:
        return False
    main_word = ctx.word_by_ref[predicate.main]
    main_lemma = (main_word.lemma or main_word.text).casefold()
    return main_lemma in {
        "cold",
        "hot",
        "warm",
        "rainy",
        "sunny",
        "windy",
        "cloudy",
        "snowy",
    }


def _has_relative_clause_dependent(
    ctx: SentenceContext, predicate: PredicateFeature
) -> bool:
    children = ctx.children_by_head.get(predicate.main, ())
    for child in children:
        word = ctx.word_by_ref[child]
        if word.deprel in {"acl:relcl", "acl"}:
            return True
        grand = ctx.children_by_head.get(child, ())
        for g in grand:
            if ctx.word_by_ref[g].deprel in {"acl:relcl", "acl"}:
                return True
    return False


__all__ = ["build_special_subject_constructions", "SpecialSubjectType"]
