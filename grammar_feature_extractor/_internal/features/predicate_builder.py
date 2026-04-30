from __future__ import annotations

from grammar_feature_extractor._internal.features.dependency_helpers import (
    children_with_deprel,
    sorted_refs,
)
from grammar_feature_extractor._internal.models import (
    AgreementFeature,
    AgreementType,
    AuxiliaryFeature,
    AuxiliaryRole,
    ClauseFeature,
    Confidence,
    ModalFeature,
    NumberValue,
    Polarity,
    PredicateComplementFeature,
    PredicateFeature,
    PredicateType,
    TAVMFeature,
    TenseValue,
    WordRef,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

MODAL_LEMMAS = frozenset(
    {"can", "could", "may", "might", "must", "shall", "should", "will", "would"}
)


def build_predicates(
    ctx: SentenceContext,
    clauses: tuple[ClauseFeature, ...],
    complements: tuple[PredicateComplementFeature, ...],
) -> tuple[PredicateFeature, ...]:
    predicates: list[PredicateFeature] = []
    for clause in clauses:
        main, predicate_type = _predicate_main(ctx, clause)
        auxiliaries = _auxiliaries(ctx, main)
        copula = _first_ref_with_deprel(ctx, main, "cop")
        negation = _negation(ctx, main, auxiliaries)
        finite = _finite(ctx, main, auxiliaries, copula)
        predicate_complements = tuple(
            item
            for item in complements
            if item.governor == main or item.governor == clause.head
        )
        polarity: Polarity = "negative" if negation is not None else "positive"
        tense = _tense(ctx, main, auxiliaries, copula)
        modality = _modality(main, auxiliaries, polarity)
        agreement = _agreement(ctx, clause, main, auxiliaries, copula)
        evidence_refs = _predicate_evidence_refs(
            main,
            auxiliaries,
            copula,
            negation,
            clause,
            predicate_complements,
        )
        predicates.append(
            PredicateFeature(
                id=f"predicate-{clause.head}",
                main=main,
                main_lemma=_lemma_or_text(ctx, main),
                predicate_type=predicate_type,
                finite=finite,
                auxiliaries=auxiliaries,
                copula=copula,
                negation=negation,
                tense=tense,
                aspect="unknown",
                voice="unknown",
                modality=modality,
                polarity=polarity,
                clause_head=clause.head,
                subject=clause.roles.subject,
                object=clause.roles.object,
                indirect_object=clause.roles.indirect_object,
                complements=predicate_complements,
                agreement=agreement,
                tavm=TAVMFeature(
                    tense=tense,
                    aspect="unknown",
                    voice="unknown",
                    modality=modality.modal_type if modality is not None else "unknown",
                    form_signature="unknown",
                ),
                form_signature="unknown",
                evidence_refs=evidence_refs,
                confidence="high" if predicate_type != "unknown" else "low",
            )
        )
    return tuple(predicates)


def _predicate_main(
    ctx: SentenceContext,
    clause: ClauseFeature,
) -> tuple[WordRef, PredicateType]:
    head = ctx.word_by_ref[clause.head]
    if children_with_deprel(ctx, clause.head, "cop"):
        return clause.head, _copular_type(head.upos)
    if head.upos in {"VERB", "AUX"}:
        return clause.head, "verbal"
    for ref in clause.local_tokens:
        if ctx.word_by_ref[ref].upos in {"VERB", "AUX"}:
            return ref, "verbal"
    return clause.head, "unknown"


def _copular_type(upos: str) -> PredicateType:
    if upos == "ADJ":
        return "copular_adjectival"
    if upos in {"NOUN", "PROPN", "PRON"}:
        return "copular_nominal"
    if upos == "ADP":
        return "copular_prepositional"
    return "unknown"


def _auxiliaries(
    ctx: SentenceContext,
    main: WordRef,
) -> tuple[AuxiliaryFeature, ...]:
    refs = children_with_deprel(ctx, main, "aux", "aux:pass", "cop")
    return tuple(
        AuxiliaryFeature(
            ref=ref,
            lemma=_lemma_or_text(ctx, ref),
            surface=ctx.word_by_ref[ref].text,
            role=_auxiliary_role(ctx, ref),
        )
        for ref in refs
    )


def _auxiliary_role(ctx: SentenceContext, ref: WordRef) -> AuxiliaryRole:
    word = ctx.word_by_ref[ref]
    lemma = _lemma_or_text(ctx, ref)
    if word.deprel == "cop":
        return "copula"
    if word.deprel == "aux:pass":
        return "passive_aux"
    if lemma in MODAL_LEMMAS:
        return "modal"
    if lemma == "do":
        return "do_support"
    if lemma == "have":
        return "perfect_aux"
    if lemma == "be":
        return "tense_aux"
    return "unknown"


def _negation(
    ctx: SentenceContext,
    main: WordRef,
    auxiliaries: tuple[AuxiliaryFeature, ...],
) -> WordRef | None:
    negation = _first_ref_with_deprel(ctx, main, "neg")
    if negation is not None:
        return negation
    for auxiliary in auxiliaries:
        negation = _first_ref_with_deprel(ctx, auxiliary.ref, "neg")
        if negation is not None:
            return negation
    return None


def _finite(
    ctx: SentenceContext,
    main: WordRef,
    auxiliaries: tuple[AuxiliaryFeature, ...],
    copula: WordRef | None,
) -> bool:
    if ctx.normalized_morph_by_ref[main].is_finite_verb:
        return True
    if copula is not None and ctx.normalized_morph_by_ref[copula].is_finite_verb:
        return True
    return any(
        ctx.normalized_morph_by_ref[auxiliary.ref].is_finite_verb
        for auxiliary in auxiliaries
    )


def _tense(
    ctx: SentenceContext,
    main: WordRef,
    auxiliaries: tuple[AuxiliaryFeature, ...],
    copula: WordRef | None,
) -> TenseValue:
    controller = _finite_controller(ctx, main, auxiliaries, copula)
    if controller is None:
        return "unknown"
    tense = ctx.morph_by_ref[controller].features.get("Tense")
    if tense == "Past":
        return "past"
    if tense == "Pres":
        return "present"
    return "unknown"


def _modality(
    main: WordRef,
    auxiliaries: tuple[AuxiliaryFeature, ...],
    polarity: Polarity,
) -> ModalFeature | None:
    modal_refs = tuple(
        auxiliary.ref for auxiliary in auxiliaries if auxiliary.role == "modal"
    )
    if not modal_refs:
        return None
    return ModalFeature(
        marker_refs=modal_refs,
        modal_type="unknown",
        complement_verb=main,
        polarity=polarity,
        confidence="medium",
    )


def _agreement(
    ctx: SentenceContext,
    clause: ClauseFeature,
    main: WordRef,
    auxiliaries: tuple[AuxiliaryFeature, ...],
    copula: WordRef | None,
) -> AgreementFeature:
    subject = clause.roles.subject
    controller = _finite_controller(ctx, main, auxiliaries, copula)
    subject_person = _person(ctx, subject)
    predicate_person = _person(ctx, controller)
    subject_number = _number(ctx, subject)
    predicate_number = _number(ctx, controller)
    match = _agreement_match(
        subject_person,
        predicate_person,
        subject_number,
        predicate_number,
    )
    evidence_refs = sorted_refs(
        [ref for ref in (subject, controller) if ref is not None]
    )
    return AgreementFeature(
        subject=subject,
        predicate=main,
        controller=controller,
        subject_person=subject_person,
        subject_number=subject_number,
        predicate_person=predicate_person,
        predicate_number=predicate_number,
        match=match,
        agreement_type=_agreement_type(copula),
        evidence_refs=evidence_refs,
        confidence=_agreement_confidence(
            subject_person,
            predicate_person,
            subject_number,
            predicate_number,
        ),
    )


def _finite_controller(
    ctx: SentenceContext,
    main: WordRef,
    auxiliaries: tuple[AuxiliaryFeature, ...],
    copula: WordRef | None,
) -> WordRef | None:
    if copula is not None:
        return copula
    for auxiliary in auxiliaries:
        if ctx.normalized_morph_by_ref[auxiliary.ref].is_finite_verb:
            return auxiliary.ref
    return main


def _agreement_match(
    subject_person: int | None,
    predicate_person: int | None,
    subject_number: NumberValue | None,
    predicate_number: NumberValue | None,
) -> bool | None:
    match = None
    if subject_person is not None and predicate_person is not None:
        match = subject_person == predicate_person
    if subject_number is not None and predicate_number is not None:
        number_match = subject_number == predicate_number
        match = number_match if match is None else match and number_match
    return match


def _agreement_confidence(
    subject_person: int | None,
    predicate_person: int | None,
    subject_number: NumberValue | None,
    predicate_number: NumberValue | None,
) -> Confidence:
    subject_known = subject_person is not None or subject_number is not None
    predicate_known = predicate_person is not None or predicate_number is not None
    if subject_known and predicate_known:
        return "high"
    if subject_known or predicate_known:
        return "medium"
    return "low"


def _agreement_type(copula: WordRef | None) -> AgreementType:
    return "subject_copula" if copula is not None else "subject_verb"


def _person(ctx: SentenceContext, ref: WordRef | None) -> int | None:
    if ref is None:
        return None
    value = ctx.morph_by_ref[ref].features.get("Person")
    if value in {"1", "2", "3"}:
        return int(value)
    return None


def _number(ctx: SentenceContext, ref: WordRef | None) -> NumberValue | None:
    if ref is None:
        return None
    value = ctx.morph_by_ref[ref].features.get("Number")
    if value == "Sing":
        return "sing"
    if value == "Plur":
        return "plur"
    return None


def _predicate_evidence_refs(
    main: WordRef,
    auxiliaries: tuple[AuxiliaryFeature, ...],
    copula: WordRef | None,
    negation: WordRef | None,
    clause: ClauseFeature,
    complements: tuple[PredicateComplementFeature, ...],
) -> tuple[WordRef, ...]:
    refs: list[WordRef] = [main, *(auxiliary.ref for auxiliary in auxiliaries)]
    if copula is not None:
        refs.append(copula)
    if negation is not None:
        refs.append(negation)
    for optional_ref in (
        clause.roles.subject,
        clause.roles.object,
        clause.roles.indirect_object,
    ):
        if optional_ref is not None:
            refs.append(optional_ref)
    for complement in complements:
        refs.extend(complement.evidence_refs)
    return sorted_refs(refs)


def _first_ref_with_deprel(
    ctx: SentenceContext,
    head: WordRef,
    deprel: str,
) -> WordRef | None:
    refs = children_with_deprel(ctx, head, deprel)
    return refs[0] if refs else None


def _lemma_or_text(ctx: SentenceContext, ref: WordRef) -> str:
    word = ctx.word_by_ref[ref]
    return (word.lemma or word.text).casefold()
