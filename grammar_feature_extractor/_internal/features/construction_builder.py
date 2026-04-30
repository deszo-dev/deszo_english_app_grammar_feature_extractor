from __future__ import annotations

from grammar_feature_extractor._internal.construction_registry import (
    ARTICLE_DEFINITE_THE_NP,
    ARTICLE_INDEFINITE_A_NP,
    ARTICLE_INDEFINITE_AN_NP,
    BE_SUBJECT_COMPLEMENT_QUESTION,
    COMPARISON_AS_AS,
    MODAL_MUST_BASE,
    PAST_SIMPLE_REGULAR,
    PRESENT_PERFECT_HAVE_PARTICIPLE,
    PRESENT_PROGRESSIVE_AFFIRMATIVE,
    PRESENT_SIMPLE_DO_NEGATIVE,
    PRESENT_SIMPLE_DO_QUESTION,
    PRESENT_SIMPLE_LEXICAL_AFFIRMATIVE,
    SUBJECT_BE_PRESENT_COMPLEMENT,
    ZERO_ARTICLE_PLURAL_GENERIC_CANDIDATE,
)
from grammar_feature_extractor._internal.form_signature_registry import (
    BE_PRESENT_COPULAR,
    MODAL_BASE_VERB,
    PAST_SIMPLE,
    PRESENT_PERFECT,
    PRESENT_PROGRESSIVE,
    PRESENT_SIMPLE_LEXICAL,
)
from grammar_feature_extractor._internal.form_signature_registry import (
    PRESENT_SIMPLE_DO_NEGATIVE as FORM_PRESENT_SIMPLE_DO_NEGATIVE,
)
from grammar_feature_extractor._internal.form_signature_registry import (
    PRESENT_SIMPLE_DO_QUESTION as FORM_PRESENT_SIMPLE_DO_QUESTION,
)
from grammar_feature_extractor._internal.models import (
    ConstructionFeature,
    ConstructionType,
    NPFeature,
    PredicateFeature,
    WordOrderFeature,
)
from grammar_feature_extractor._internal.proof_surface import make_provenance


def build_constructions(
    predicates: tuple[PredicateFeature, ...],
    np_profiles: tuple[NPFeature, ...],
    word_order: tuple[WordOrderFeature, ...],
) -> tuple[ConstructionFeature, ...]:
    items: list[ConstructionFeature] = []
    for predicate in predicates:
        signature = _predicate_signature(predicate, word_order)
        if signature is not None:
            items.append(_predicate_construction(predicate, signature))
    for np in np_profiles:
        signature = _np_signature(np)
        if signature is not None:
            items.append(_np_construction(np, signature))
    if _has_as_as(word_order):
        first = word_order[0]
        items.append(
            ConstructionFeature(
                key=f"construction-{COMPARISON_AS_AS}-1",
                family_hint="comparison",
                type="comparison",
                signature=COMPARISON_AS_AS,
                slots={"refs": first.ordered_refs},
                evidence_refs=first.ordered_refs,
                confidence="medium",
                provenance=make_provenance(
                    "deterministic", "word_order", first.ordered_refs, "medium"
                ),
            )
        )
    return tuple(items)


def _predicate_signature(
    predicate: PredicateFeature,
    word_order: tuple[WordOrderFeature, ...],
) -> str | None:
    if predicate.form_signature == PRESENT_SIMPLE_LEXICAL:
        return PRESENT_SIMPLE_LEXICAL_AFFIRMATIVE
    if predicate.form_signature == FORM_PRESENT_SIMPLE_DO_NEGATIVE:
        return PRESENT_SIMPLE_DO_NEGATIVE
    if predicate.form_signature == FORM_PRESENT_SIMPLE_DO_QUESTION:
        return PRESENT_SIMPLE_DO_QUESTION
    if predicate.form_signature == PRESENT_PROGRESSIVE:
        return PRESENT_PROGRESSIVE_AFFIRMATIVE
    if predicate.form_signature == PRESENT_PERFECT:
        return PRESENT_PERFECT_HAVE_PARTICIPLE
    if predicate.form_signature == PAST_SIMPLE:
        return PAST_SIMPLE_REGULAR
    if predicate.form_signature == MODAL_BASE_VERB and any(
        auxiliary.lemma == "must" for auxiliary in predicate.auxiliaries
    ):
        return MODAL_MUST_BASE
    if predicate.form_signature == BE_PRESENT_COPULAR:
        if any(item.pattern == "aux_subject_verb" for item in word_order):
            return BE_SUBJECT_COMPLEMENT_QUESTION
        return SUBJECT_BE_PRESENT_COMPLEMENT
    return None


def _predicate_construction(
    predicate: PredicateFeature,
    signature: str,
) -> ConstructionFeature:
    return ConstructionFeature(
        key=f"construction-{signature}-{predicate.main}",
        family_hint="predicate",
        type=_construction_type(signature),
        signature=signature,
        slots={
            "predicate": predicate.main,
            "subject": predicate.subject or 0,
            "object": predicate.object or 0,
        },
        evidence_refs=predicate.evidence_refs,
        confidence=predicate.confidence,
        provenance=make_provenance(
            "deterministic", "dependency", predicate.evidence_refs, predicate.confidence
        ),
    )


def _np_signature(np: NPFeature) -> str | None:
    article = np.article_slot.article_form
    if article == "a":
        return ARTICLE_INDEFINITE_A_NP
    if article == "an":
        return ARTICLE_INDEFINITE_AN_NP
    if article == "the":
        return ARTICLE_DEFINITE_THE_NP
    if np.article_slot.requiredness == "zero_article" and np.number == "plural":
        return ZERO_ARTICLE_PLURAL_GENERIC_CANDIDATE
    return None


def _np_construction(np: NPFeature, signature: str) -> ConstructionFeature:
    return ConstructionFeature(
        key=f"construction-{signature}-{np.head}",
        family_hint="article_np",
        type="article_np",
        signature=signature,
        slots={"np": np.head, "article_form": np.article_slot.article_form or "none"},
        evidence_refs=np.evidence_refs,
        confidence=np.confidence,
        provenance=make_provenance(
            "deterministic", "dependency", np.evidence_refs, np.confidence
        ),
    )


def _construction_type(signature: str) -> ConstructionType:
    if signature.startswith("present") or signature.startswith("past"):
        return "tense_aspect"
    if signature.startswith("subject_be") or signature.startswith("be_subject"):
        return "copular"
    if signature.startswith("modal"):
        return "modal"
    return "complement_pattern"


def _has_as_as(_word_order: tuple[WordOrderFeature, ...]) -> bool:
    return False
