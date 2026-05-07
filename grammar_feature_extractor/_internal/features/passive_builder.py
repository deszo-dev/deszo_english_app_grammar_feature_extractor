from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    PassiveFeature,
    PassiveType,
    PredicateFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def build_passive_features(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[PassiveFeature, ...]:
    items: list[PassiveFeature] = []
    for predicate in predicates:
        feature = _classify(ctx, predicate)
        if feature is not None:
            items.append(feature)
    return tuple(items)


def _classify(
    ctx: SentenceContext,
    predicate: PredicateFeature,
) -> PassiveFeature | None:
    if predicate.voice != "passive":
        if not _has_passive_signal(ctx, predicate):
            return None

    aux_refs = tuple(
        aux.ref
        for aux in predicate.auxiliaries
        if aux.role in {"passive_aux", "perfect_aux", "modal", "tense_aux"}
    )
    participle_ref = predicate.main
    passive_type = _passive_type(ctx, predicate, aux_refs)
    agent_refs = _agent_by_phrase(ctx, predicate)
    patient_subject = predicate.subject

    return PassiveFeature(
        predicate=predicate.main,
        passive_type=passive_type,
        aux_refs=aux_refs,
        participle_ref=participle_ref,
        agent_by_phrase=agent_refs,
        patient_subject=patient_subject,
        confidence="high" if aux_refs else "medium",
    )


def _has_passive_signal(
    ctx: SentenceContext,
    predicate: PredicateFeature,
) -> bool:
    if predicate.subject is not None:
        subj_word = ctx.word_by_ref[predicate.subject]
        if subj_word.deprel == "nsubj:pass":
            return True
    return any(
        aux.role == "passive_aux" for aux in predicate.auxiliaries
    )


def _passive_type(
    ctx: SentenceContext,
    predicate: PredicateFeature,
    aux_refs: tuple[int, ...],
) -> PassiveType:
    aux_lemmas = [
        (ctx.word_by_ref[aux.ref].lemma or ctx.word_by_ref[aux.ref].text).casefold()
        for aux in predicate.auxiliaries
    ]
    if any(lemma == "get" for lemma in aux_lemmas):
        return "get_passive"
    if any(role.role == "modal" for role in predicate.auxiliaries):
        return "modal_passive"
    if any(role.role == "perfect_aux" for role in predicate.auxiliaries):
        return "perfect_passive"
    if aux_refs:
        return "be_passive"
    if (
        predicate.subject is not None
        and ctx.word_by_ref[predicate.subject].deprel == "nsubj:pass"
    ):
        return "reduced_passive_participle"
    return "unknown"


def _agent_by_phrase(
    ctx: SentenceContext,
    predicate: PredicateFeature,
) -> tuple[int, ...]:
    children = ctx.children_by_head.get(predicate.main, ())
    for child in children:
        word = ctx.word_by_ref[child]
        if word.deprel != "obl:agent" and not (
            word.deprel == "obl"
            and any(
                ctx.word_by_ref[grand].text.casefold() == "by"
                and ctx.word_by_ref[grand].deprel == "case"
                for grand in ctx.children_by_head.get(child, ())
            )
        ):
            continue
        case_refs = tuple(
            grand
            for grand in ctx.children_by_head.get(child, ())
            if ctx.word_by_ref[grand].deprel == "case"
        )
        return tuple(sorted({child, *case_refs}))
    return ()


__all__ = ["build_passive_features"]
