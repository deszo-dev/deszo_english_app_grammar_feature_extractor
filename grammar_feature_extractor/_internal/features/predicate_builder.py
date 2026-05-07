from __future__ import annotations

from grammar_feature_extractor._internal.features.dependency_helpers import (
    children_with_deprel,
    sorted_refs,
)
from grammar_feature_extractor._internal.form_signature_registry import (
    BE_PRESENT_COPULAR,
    MODAL_BASE_VERB,
    PASSIVE_BE_PARTICIPLE,
    PAST_SIMPLE,
    PRESENT_PERFECT,
    PRESENT_PROGRESSIVE,
    PRESENT_SIMPLE_DO_NEGATIVE,
    PRESENT_SIMPLE_DO_QUESTION,
    PRESENT_SIMPLE_LEXICAL,
    UNKNOWN,
)
from grammar_feature_extractor._internal.modal_registry import (
    ABILITY_MODALS,
    ADVICE_MODALS,
    CONDITIONAL_MODALS,
    MODAL_LEMMAS,
    OBLIGATION_MODALS,
    PERMISSION_MODALS,
    POSSIBILITY_MODALS,
    PREDICTION_MODALS,
)
from grammar_feature_extractor._internal.models import (
    AgreementFeature,
    AgreementType,
    AspectValue,
    AuxiliaryFeature,
    AuxiliaryRole,
    ClauseFeature,
    Confidence,
    ModalFeature,
    ModalityValue,
    ModalType,
    NumberValue,
    Polarity,
    PredicateComplementFeature,
    PredicateFeature,
    PredicateType,
    TAVMFeature,
    TenseValue,
    VoiceValue,
    WordRef,
)
from grammar_feature_extractor._internal.proof_surface import make_provenance
from grammar_feature_extractor._internal.sentence_context import SentenceContext

STRICT_NEGATORS = frozenset(
    {"not", "n't", "never", "no", "none", "nothing", "nobody", "neither", "nowhere"}
)
NEGATIVE_LIKE_ADVERBS = frozenset({"scarcely", "hardly"})
NEGATIVE_COORDINATORS = frozenset({"nor"})


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
        negation_refs = _negation_refs(ctx, clause, main, auxiliaries, negation)
        finite = _finite(ctx, main, auxiliaries, copula)
        predicate_complements = tuple(
            item
            for item in complements
            if item.governor == main or item.governor == clause.head
        )
        polarity = _polarity(ctx, negation_refs)
        tense = _tense(ctx, main, auxiliaries, copula)
        modality = _modality(main, auxiliaries, polarity)
        aspect = _aspect(ctx, main, auxiliaries)
        voice = _voice(ctx, main, auxiliaries, clause, predicate_type)
        form_signature = _form_signature(
            ctx,
            main,
            predicate_type,
            auxiliaries,
            copula,
            negation,
            tense,
            aspect,
            voice,
        )
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
                id=f"pred-{clause.head}",
                main=main,
                main_lemma=_lemma_or_text(ctx, main),
                main_upos=ctx.word_by_ref[main].upos,
                predicate_type=predicate_type,
                finite=finite,
                auxiliaries=auxiliaries,
                copula=copula,
                negation=negation,
                tense=tense,
                aspect=aspect,
                voice=voice,
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
                    aspect=aspect,
                    voice=voice,
                    modality=(
                        _broad_modality(modality.modal_type)
                        if modality is not None
                        else "unknown"
                    ),
                    form_signature=form_signature,
                ),
                form_signature=form_signature,
                evidence_refs=evidence_refs,
                confidence="high" if predicate_type != "unknown" else "low",
                provenance=make_provenance(
                    "deterministic",
                    "dependency",
                    evidence_refs,
                    "high" if predicate_type != "unknown" else "low",
                ),
            )
        )
    return tuple(predicates)


def _predicate_main(
    ctx: SentenceContext,
    clause: ClauseFeature,
) -> tuple[WordRef, PredicateType]:
    head = ctx.word_by_ref[clause.head]
    if _has_expletive_there(ctx, clause):
        return clause.head, "existential_there"
    if children_with_deprel(ctx, clause.head, "cop"):
        return clause.head, _copular_type(head.upos)
    if head.upos in {"VERB", "AUX"}:
        if _is_passive_clause(ctx, clause):
            return clause.head, "passive_verbal"
        return clause.head, "verbal"
    for ref in clause.local_tokens:
        if ctx.word_by_ref[ref].upos in {"VERB", "AUX"}:
            if _is_passive_clause(ctx, clause):
                return ref, "passive_verbal"
            return ref, "verbal"
    return clause.head, "unknown"


def _has_expletive_there(ctx: SentenceContext, clause: ClauseFeature) -> bool:
    for ref in clause.local_tokens:
        word = ctx.word_by_ref[ref]
        if word.text.casefold() == "there" and word.deprel in {"expl", "nsubj"}:
            return True
    return False


def _is_passive_clause(ctx: SentenceContext, clause: ClauseFeature) -> bool:
    if clause.roles.subject is not None:
        if ctx.word_by_ref[clause.roles.subject].deprel == "nsubj:pass":
            return True
    for ref in clause.local_tokens:
        if ctx.word_by_ref[ref].deprel == "aux:pass":
            return True
    return False


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


def _negation_refs(
    ctx: SentenceContext,
    clause: ClauseFeature,
    main: WordRef,
    auxiliaries: tuple[AuxiliaryFeature, ...],
    direct_negation: WordRef | None,
) -> tuple[WordRef, ...]:
    refs: list[WordRef] = []
    if direct_negation is not None:
        refs.append(direct_negation)
    predicate_refs = {main, *(auxiliary.ref for auxiliary in auxiliaries)}
    for ref in clause.local_tokens:
        lower = ctx.word_by_ref[ref].text.casefold()
        lemma = (ctx.word_by_ref[ref].lemma or ctx.word_by_ref[ref].text).casefold()
        features = ctx.morph_by_ref[ref].features
        if (
            lower in STRICT_NEGATORS
            or lower in NEGATIVE_LIKE_ADVERBS
            or lower in NEGATIVE_COORDINATORS
            or lemma in STRICT_NEGATORS
            or features.get("Polarity") == "Neg"
            or features.get("PronType") == "Neg"
        ):
            head = ctx.word_by_ref[ref].head
            if (
                ref in predicate_refs
                or head in predicate_refs
                or head
                in {
                    clause.roles.object,
                    clause.roles.subject,
                }
                or ref
                in {
                    clause.roles.object,
                    clause.roles.subject,
                }
            ):
                refs.append(ref)
    return sorted_refs(refs)


def _polarity(ctx: SentenceContext, negation_refs: tuple[WordRef, ...]) -> Polarity:
    if not negation_refs:
        return "positive"
    lowers = {ctx.word_by_ref[ref].text.casefold() for ref in negation_refs}
    if lowers and lowers <= NEGATIVE_LIKE_ADVERBS:
        return "mixed"
    if lowers & NEGATIVE_LIKE_ADVERBS:
        return "mixed"
    return "negative"


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
    modal_lemma = next(
        auxiliary.lemma for auxiliary in auxiliaries if auxiliary.role == "modal"
    )
    medium_confidence_modals = {"can", "could", "must", "should", "will"}
    confidence: Confidence = (
        "medium" if modal_lemma in medium_confidence_modals else "high"
    )
    return ModalFeature(
        marker_refs=modal_refs,
        modal_type=_modal_type(modal_lemma),
        complement_verb=main,
        polarity=polarity,
        confidence=confidence,
    )


def _modal_type(lemma: str) -> ModalType:
    if lemma in ABILITY_MODALS:
        return "can_ability" if lemma == "can" else "could_ability"
    if lemma in PERMISSION_MODALS:
        return "may_permission"
    if lemma in POSSIBILITY_MODALS:
        return "might_possibility"
    if lemma in OBLIGATION_MODALS:
        return "must_obligation"
    if lemma in ADVICE_MODALS:
        return "should_advice"
    if lemma in PREDICTION_MODALS:
        return "will_prediction" if lemma == "will" else "shall_prediction"
    if lemma in CONDITIONAL_MODALS:
        return "would_conditional"
    return "unknown"


def _broad_modality(modal_type: ModalType) -> ModalityValue:
    if modal_type.endswith("_ability"):
        return "ability"
    if modal_type.endswith("_permission"):
        return "permission"
    if modal_type.endswith("_possibility"):
        return "possibility"
    if modal_type.endswith("_obligation"):
        return "obligation"
    if modal_type.endswith("_deduction"):
        return "deduction"
    if modal_type.endswith("_advice"):
        return "advice"
    if modal_type.endswith("_prediction"):
        return "prediction"
    if modal_type.endswith("_conditional"):
        return "conditional"
    if modal_type.endswith("_necessity"):
        return "necessity"
    if modal_type.endswith("_expectation"):
        return "expectation"
    if modal_type.endswith("_past_habit"):
        return "past_habit"
    return "unknown"


def _aspect(
    ctx: SentenceContext,
    main: WordRef,
    auxiliaries: tuple[AuxiliaryFeature, ...],
) -> AspectValue:
    has_have = any(auxiliary.lemma == "have" for auxiliary in auxiliaries)
    has_be = any(auxiliary.lemma == "be" for auxiliary in auxiliaries)
    main_morph = ctx.morph_by_ref[main].features
    if has_have and main_morph.get("VerbForm") == "Part":
        if has_be:
            return "perfect_progressive"
        return "perfect"
    if has_be and main_morph.get("VerbForm") in {"Ger", "Part"}:
        return "progressive"
    if main_morph.get("VerbForm") in {"Fin", "Inf"}:
        return "simple"
    return "unknown"


def _voice(
    ctx: SentenceContext,
    main: WordRef,
    auxiliaries: tuple[AuxiliaryFeature, ...],
    clause: ClauseFeature,
    predicate_type: PredicateType,
) -> VoiceValue:
    if predicate_type.startswith("copular") or predicate_type == "existential_there":
        return "copular_not_applicable"
    if any(auxiliary.role == "passive_aux" for auxiliary in auxiliaries):
        return "passive"
    if (
        clause.roles.subject is not None
        and ctx.word_by_ref[clause.roles.subject].deprel == "nsubj:pass"
    ):
        return "passive"
    return "active" if ctx.word_by_ref[main].upos in {"VERB", "AUX"} else "unknown"


def _form_signature(
    ctx: SentenceContext,
    main: WordRef,
    predicate_type: PredicateType,
    auxiliaries: tuple[AuxiliaryFeature, ...],
    copula: WordRef | None,
    negation: WordRef | None,
    tense: TenseValue,
    aspect: AspectValue,
    voice: VoiceValue,
) -> str:
    if copula is not None and tense == "present":
        return BE_PRESENT_COPULAR
    if voice == "passive":
        return PASSIVE_BE_PARTICIPLE
    if any(auxiliary.role == "modal" for auxiliary in auxiliaries):
        return MODAL_BASE_VERB
    if aspect == "perfect":
        return PRESENT_PERFECT
    if aspect == "progressive":
        return PRESENT_PROGRESSIVE
    if (
        any(auxiliary.role == "do_support" for auxiliary in auxiliaries)
        and negation is not None
    ):
        return PRESENT_SIMPLE_DO_NEGATIVE
    if any(auxiliary.role == "do_support" for auxiliary in auxiliaries):
        return PRESENT_SIMPLE_DO_QUESTION
    if predicate_type == "verbal" and tense == "past":
        return PAST_SIMPLE
    if (
        predicate_type == "verbal"
        and tense == "present"
        and ctx.normalized_morph_by_ref[main].is_finite_verb
    ):
        return PRESENT_SIMPLE_LEXICAL
    return UNKNOWN


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
