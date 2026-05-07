from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TypeAlias

from grammar_feature_extractor._internal.errors import SerializationError
from grammar_feature_extractor._internal.models import (
    AbsenceFeature,
    AdjectivePatternFeature,
    AgreementFeature,
    AnnotatedDocument,
    ArticleSlotFeature,
    AuxiliaryFeature,
    ClauseFeature,
    ClauseMarkerFeature,
    ConditionalFeature,
    ConstructionFeature,
    ContrastiveSupportFeature,
    Coordination,
    CountabilityFeature,
    DependencyEvidence,
    DeterminerFeature,
    EvidenceFeatures,
    FeatureDiagnostic,
    GrammarEligibilityFeature,
    GrammarFeatureDocument,
    GrammarFeaturePage,
    GrammarFeatureSet,
    LexicalClassFeature,
    LexicalFeatures,
    LexicalItemFeature,
    ModalFeature,
    MorphFeature,
    MorphologyFeatures,
    NegationFeature,
    NormalizedMorph,
    NPFeature,
    PageInfo,
    PassiveFeature,
    Phrase,
    PluralAnalysisFeature,
    PredicateComplementFeature,
    PredicateFeature,
    PronounFeature,
    ProofProvenance,
    ReferenceFeature,
    RelativeClauseFeature,
    ReportedSpeechFeature,
    Roles,
    SentenceFeature,
    SentenceGrammarFeatures,
    SlotValue,
    SpecialSubjectConstructionFeature,
    SyntaxFeatures,
    TAVMFeature,
    TokenEvidence,
    TypedQuantifierFeature,
    Valency,
    VerbPatternFeature,
    WordOrderFeature,
)
from grammar_feature_extractor._internal.validation import parse_annotated_document

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


def loads_document(payload: str) -> AnnotatedDocument:
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SerializationError("Invalid input JSON.") from exc
    return parse_annotated_document(raw)


def dumps_page(page: GrammarFeaturePage) -> str:
    return (
        json.dumps(page_to_dict(page), ensure_ascii=False, separators=(",", ":")) + "\n"
    )


def page_to_dict(page: GrammarFeaturePage) -> JsonObject:
    return {
        "schema_version": page.schema_version,
        "page": _page_info_to_dict(page.page),
        "features": [_sentence_to_dict(sentence) for sentence in page.features],
    }


def document_to_dict(document: GrammarFeatureDocument) -> JsonObject:
    return {
        "schema_version": document.schema_version,
        "source_sentence_count": document.source_sentence_count,
        "sentences": [_sentence_to_dict(sentence) for sentence in document.sentences],
    }


def _page_info_to_dict(page: PageInfo) -> JsonObject:
    result: JsonObject = {
        "page_number": page.page_number,
        "page_size": page.page_size,
        "total_sentences": page.total_sentences,
        "sentence_start": page.sentence_start,
        "sentence_end_exclusive": page.sentence_end_exclusive,
        "has_next_page": page.has_next_page,
    }
    if page.next_page is not None:
        result["next_page"] = page.next_page
    return result


def _sentence_to_dict(sentence: SentenceGrammarFeatures) -> JsonObject:
    return {
        "sentence_index": sentence.sentence_index,
        "text": sentence.text,
        "tokens": _tokens_to_dict(sentence.features.evidence),
        "syntax": _syntax_to_dict(sentence.features.syntax),
        "diagnostics": [
            _diagnostic_to_dict(item) for item in sentence.features.diagnostics
        ],
    }


def _feature_set_to_dict(features: GrammarFeatureSet) -> JsonObject:
    return {
        "evidence": _evidence_to_dict(features.evidence),
        "morphology": _morphology_to_dict(features.morphology),
        "syntax": _syntax_to_dict(features.syntax),
        "lexical": _lexical_to_dict(features.lexical),
        "constructions": [
            _construction_to_dict(item) for item in features.constructions
        ],
        "contrastive_support": [
            _contrastive_to_dict(item) for item in features.contrastive_support
        ],
        "absences": [_absence_to_dict(item) for item in features.absences],
        "diagnostics": [_diagnostic_to_dict(item) for item in features.diagnostics],
    }


def _tokens_to_dict(evidence: EvidenceFeatures) -> list[JsonValue]:
    return [_token_to_dict(item) for item in evidence.words]


def _token_to_dict(item: TokenEvidence) -> JsonObject:
    result: JsonObject = {
        "token_ref": item.ref,
        "surface": item.text,
        "lemma": item.lemma,
        "upos": item.upos,
        "head_ref": item.head,
        "deprel": item.deprel,
        "start_char": item.start_char,
        "end_char": item.end_char,
    }
    if item.xpos is not None:
        result["xpos"] = item.xpos
    if item.feats:
        result["features"] = dict(item.feats)
    return result


def _evidence_to_dict(evidence: EvidenceFeatures) -> JsonObject:
    return {
        "words": [_token_evidence_to_dict(item) for item in evidence.words],
        "dependencies": [
            _dependency_evidence_to_dict(item) for item in evidence.dependencies
        ],
    }


def _token_evidence_to_dict(item: TokenEvidence) -> JsonObject:
    result: JsonObject = {
        "ref": item.ref,
        "text": item.text,
        "lower": item.lower,
        "lemma": item.lemma,
        "upos": item.upos,
        "feats": dict(item.feats),
        "head": item.head,
        "deprel": item.deprel,
        "children": list(item.children),
        "start_char": item.start_char,
        "end_char": item.end_char,
        "position": item.position,
    }
    if item.xpos is not None:
        result["xpos"] = item.xpos
    return result


def _dependency_evidence_to_dict(item: DependencyEvidence) -> JsonObject:
    return {
        "governor": item.governor,
        "dependent": item.dependent,
        "deprel": item.deprel,
    }


def _morphology_to_dict(morphology: MorphologyFeatures) -> JsonObject:
    return {
        "word_morphology": [
            _morph_feature_to_dict(item) for item in morphology.word_morphology
        ],
        "normalized": [
            _normalized_morph_to_dict(item) for item in morphology.normalized
        ],
    }


def _morph_feature_to_dict(item: MorphFeature) -> JsonObject:
    result: JsonObject = {
        "ref": item.ref,
        "pos": item.pos,
        "lemma": item.lemma,
        "features": dict(item.features),
    }
    if item.xpos is not None:
        result["xpos"] = item.xpos
    return result


def _normalized_morph_to_dict(item: NormalizedMorph) -> JsonObject:
    return {
        "ref": item.ref,
        "is_finite_verb": item.is_finite_verb,
        "is_base_verb": item.is_base_verb,
        "is_to_infinitive": item.is_to_infinitive,
        "is_bare_infinitive": item.is_bare_infinitive,
        "is_gerund": item.is_gerund,
        "is_past_participle": item.is_past_participle,
        "is_present_participle": item.is_present_participle,
        "is_plural_noun": item.is_plural_noun,
        "is_singular_noun": item.is_singular_noun,
        "is_comparative": item.is_comparative,
        "is_superlative": item.is_superlative,
    }


def _syntax_to_dict(syntax: SyntaxFeatures) -> JsonObject:
    return {
        "clauses": [_clause_to_dict(item) for item in syntax.clauses],
        "predicates": [_predicate_to_dict(item) for item in syntax.predicates],
        "np_profiles": [_np_to_dict(item) for item in syntax.np_profiles],
        "pps": [],
        "relative_clauses": [],
        "participial_clauses": [],
    }


def _pronoun_to_dict(item: PronounFeature) -> JsonObject:
    result: JsonObject = {
        "ref": item.ref,
        "lemma": item.lemma,
        "pronoun_type": item.pronoun_type,
    }
    if item.person is not None:
        result["person"] = item.person
    if item.number is not None:
        result["number"] = item.number
    if item.case is not None:
        result["case"] = item.case
    return result


def _special_subject_to_dict(item: SpecialSubjectConstructionFeature) -> JsonObject:
    result: JsonObject = {
        "type": item.type,
        "subject_ref": item.subject_ref,
        "predicate_ref": item.predicate_ref,
        "evidence_refs": list(item.evidence_refs),
        "confidence": item.confidence,
    }
    if item.notional_subject is not None:
        result["notional_subject"] = item.notional_subject
    if item.agreement_controller is not None:
        result["agreement_controller"] = item.agreement_controller
    return result


def _relative_clause_to_dict(item: RelativeClauseFeature) -> JsonObject:
    result: JsonObject = {
        "clause_id": item.clause_id,
        "head_noun": item.head_noun,
        "relative_type": item.relative_type,
        "confidence": item.confidence,
    }
    if item.relative_marker is not None:
        result["relative_marker"] = item.relative_marker
    if item.marker_text is not None:
        result["marker_text"] = item.marker_text
    if item.restrictive is not None:
        result["restrictive"] = item.restrictive
    return result


def _conditional_to_dict(item: ConditionalFeature) -> JsonObject:
    result: JsonObject = {
        "if_clause": item.if_clause,
        "main_clause": item.main_clause,
        "conditional_type": item.conditional_type,
        "main_tavm": _tavm_to_dict(item.main_tavm),
        "subordinate_tavm": _tavm_to_dict(item.subordinate_tavm),
        "confidence": item.confidence,
    }
    if item.if_marker_ref is not None:
        result["if_marker_ref"] = item.if_marker_ref
    return result


def _reported_speech_to_dict(item: ReportedSpeechFeature) -> JsonObject:
    result: JsonObject = {
        "reporting_verb": item.reporting_verb,
        "reported_clause_head": item.reported_clause_head,
        "report_type": item.report_type,
        "backshift_candidate": item.backshift_candidate,
        "speaker_or_addressee_refs": list(item.speaker_or_addressee_refs),
        "confidence": item.confidence,
    }
    if item.marker is not None:
        result["marker"] = item.marker
    return result


def _passive_to_dict(item: PassiveFeature) -> JsonObject:
    result: JsonObject = {
        "predicate": item.predicate,
        "passive_type": item.passive_type,
        "aux_refs": list(item.aux_refs),
        "participle_ref": item.participle_ref,
        "agent_by_phrase": list(item.agent_by_phrase),
        "confidence": item.confidence,
    }
    if item.patient_subject is not None:
        result["patient_subject"] = item.patient_subject
    return result


def _phrase_to_dict(item: Phrase) -> JsonObject:
    return {
        "type": item.type,
        "head": item.head,
        "tokens": list(item.tokens),
        "provenance": _provenance_to_dict(item.provenance),
    }


def _clause_to_dict(item: ClauseFeature) -> JsonObject:
    result: JsonObject = {
        "id": item.id,
        "head_ref": item.head,
        "clause_type": item.type,
        "finite": item.finite,
        "token_refs": list(item.tokens),
        "local_token_refs": list(item.local_tokens),
        "evidence_refs": list(item.provenance.evidence_refs),
        "source": _flat_source(item.provenance),
        "confidence": item.confidence,
    }
    if item.subject is not None:
        result["subject_ref"] = item.subject
    if item.predicate is not None:
        result["predicate_ref"] = item.predicate
    if item.marker is not None:
        result["marker_ref"] = item.marker.marker_ref
    if item.semantic_relation is not None:
        result["semantic_relation"] = item.semantic_relation
    return result


def _roles_to_dict(item: Roles) -> JsonObject:
    result: JsonObject = {"oblique": list(item.oblique)}
    if item.subject is not None:
        result["subject"] = item.subject
    if item.object is not None:
        result["object"] = item.object
    if item.indirect_object is not None:
        result["indirect_object"] = item.indirect_object
    return result


def _valency_to_dict(item: Valency) -> JsonObject:
    return {
        "subject": item.subject,
        "object": item.object,
        "indirect_object": item.indirect_object,
    }


def _clause_marker_to_dict(item: ClauseMarkerFeature) -> JsonObject:
    return {
        "marker_ref": item.marker_ref,
        "marker": item.marker,
        "clause_head": item.clause_head,
        "marker_type": item.marker_type,
        "confidence": item.confidence,
        "sources": list(item.sources),
        "provenance": _provenance_to_dict(item.provenance),
    }


def _complement_to_dict(item: PredicateComplementFeature) -> JsonObject:
    result: JsonObject = {
        "governor": item.governor,
        "head": item.head,
        "type": item.type,
        "deprel_source": item.deprel_source,
        "evidence_refs": list(item.evidence_refs),
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.preposition is not None:
        result["preposition"] = item.preposition
    if item.marker is not None:
        result["marker"] = item.marker
    return result


def _predicate_to_dict(item: PredicateFeature) -> JsonObject:
    result: JsonObject = {
        "id": item.id,
        "clause_id": f"clause-{item.clause_head}",
        "main_ref": item.main,
        "main_lemma": item.main_lemma,
        "main_upos": item.main_upos,
        "predicate_type": item.predicate_type,
        "finite": item.finite,
        "auxiliary_refs": [auxiliary.ref for auxiliary in item.auxiliaries],
        "tense": item.tense,
        "aspect": item.aspect,
        "voice": item.voice,
        "polarity": item.polarity,
        "object_refs": [ref for ref in (item.object,) if ref is not None],
        "complement_refs": [complement.head for complement in item.complements],
        "evidence_refs": list(item.evidence_refs),
        "source": _flat_source(item.provenance),
        "confidence": item.confidence,
    }
    if item.copula is not None:
        result["copula_ref"] = item.copula
    if item.negation is not None:
        result["negation_ref"] = item.negation
    if item.subject is not None:
        result["subject_ref"] = item.subject
    if item.indirect_object is not None:
        result["indirect_object_ref"] = item.indirect_object
    return result


def _auxiliary_to_dict(item: AuxiliaryFeature) -> JsonObject:
    return {
        "ref": item.ref,
        "lemma": item.lemma,
        "surface": item.surface,
        "role": item.role,
    }


def _modal_to_dict(item: ModalFeature) -> JsonObject:
    result: JsonObject = {
        "marker_refs": list(item.marker_refs),
        "modal_type": item.modal_type,
        "polarity": item.polarity,
        "confidence": item.confidence,
    }
    if item.complement_verb is not None:
        result["complement_verb"] = item.complement_verb
    return result


def _agreement_to_dict(item: AgreementFeature) -> JsonObject:
    result: JsonObject = {
        "agreement_type": item.agreement_type,
        "evidence_refs": list(item.evidence_refs),
        "confidence": item.confidence,
    }
    if item.subject is not None:
        result["subject"] = item.subject
    if item.predicate is not None:
        result["predicate"] = item.predicate
    if item.controller is not None:
        result["controller"] = item.controller
    if item.subject_person is not None:
        result["subject_person"] = item.subject_person
    if item.subject_number is not None:
        result["subject_number"] = item.subject_number
    if item.predicate_person is not None:
        result["predicate_person"] = item.predicate_person
    if item.predicate_number is not None:
        result["predicate_number"] = item.predicate_number
    if item.match is not None:
        result["match"] = item.match
    return result


def _tavm_to_dict(item: TAVMFeature) -> JsonObject:
    return {
        "tense": item.tense,
        "aspect": item.aspect,
        "voice": item.voice,
        "modality": item.modality,
        "form_signature": item.form_signature,
    }


def _coordination_to_dict(item: Coordination) -> JsonObject:
    return {
        "head": item.head,
        "conjuncts": list(item.conjuncts),
        "provenance": _provenance_to_dict(item.provenance),
    }


def _provenance_to_dict(item: ProofProvenance) -> JsonObject:
    return {
        "tier": item.tier,
        "source": item.source,
        "evidence_refs": list(item.evidence_refs),
        "confidence": item.confidence,
    }


def _flat_source(item: ProofProvenance) -> str:
    if item.source in {"dependency", "upos", "xpos", "word_order"}:
        return "parser"
    if item.source == "morphology":
        return "morphology"
    if item.source in {"lexicon", "closed_list"}:
        return "lexicon"
    if item.source == "phonology":
        return "phonology"
    if item.source in {"surface", "lemma", "discourse_heuristic", "task_context"}:
        return "heuristic"
    return "heuristic"


def _lexical_to_dict(lexical: LexicalFeatures) -> JsonObject:
    return {
        "sentence": _sentence_feature_to_dict(lexical.sentence),
        "word_order": [_word_order_to_dict(item) for item in lexical.word_order],
        "negation": [_negation_to_dict(item) for item in lexical.negation],
        "time_markers": [_lexical_item_to_dict(item) for item in lexical.time_markers],
        "lexical_classes": [
            _lexical_class_to_dict(item) for item in lexical.lexical_classes
        ],
        "verb_patterns": [
            _verb_pattern_to_dict(item) for item in lexical.verb_patterns
        ],
        "adjective_patterns": [
            _adjective_pattern_to_dict(item) for item in lexical.adjective_patterns
        ],
        "comparisons": [_lexical_item_to_dict(item) for item in lexical.comparisons],
        "quantifiers": [
            _typed_quantifier_to_dict(item) for item in lexical.quantifiers
        ],
        "phrasal_verbs": [
            _lexical_item_to_dict(item) for item in lexical.phrasal_verbs
        ],
        "discourse_markers": [
            _lexical_item_to_dict(item) for item in lexical.discourse_markers
        ],
        "contractions": [_lexical_item_to_dict(item) for item in lexical.contractions],
        "noun_inflections": [
            _lexical_item_to_dict(item) for item in lexical.noun_inflections
        ],
    }


def _lexical_class_to_dict(item: LexicalClassFeature) -> JsonObject:
    return {
        "ref": item.ref,
        "lemma": item.lemma,
        "classes": list(item.classes),
        "source": item.source,
        "confidence": item.confidence,
    }


def _verb_pattern_to_dict(item: VerbPatternFeature) -> JsonObject:
    return {
        "predicate": item.predicate,
        "lemma": item.lemma,
        "pattern": item.pattern,
        "complements": [_complement_to_dict(c) for c in item.complements],
        "confidence": item.confidence,
    }


def _adjective_pattern_to_dict(item: AdjectivePatternFeature) -> JsonObject:
    result: JsonObject = {
        "adjective": item.adjective,
        "lemma": item.lemma,
        "pattern": item.pattern,
        "confidence": item.confidence,
    }
    if item.complement is not None:
        result["complement"] = _complement_to_dict(item.complement)
    if item.degree_modifier is not None:
        result["degree_modifier"] = item.degree_modifier
    return result


def _typed_quantifier_to_dict(item: TypedQuantifierFeature) -> JsonObject:
    result: JsonObject = {
        "ref": item.ref,
        "text": item.text,
        "quantifier_type": item.quantifier_type,
    }
    if item.compatible_number is not None:
        result["compatible_number"] = item.compatible_number
    if item.polarity_sensitivity is not None:
        result["polarity_sensitivity"] = item.polarity_sensitivity
    return result


def _countability_to_dict(item: CountabilityFeature) -> JsonObject:
    return {
        "status": item.status,
        "source": item.source,
        "confidence": item.confidence,
    }


def _reference_to_dict(item: ReferenceFeature) -> JsonObject:
    return {
        "reference_status": item.reference_status,
        "evidence": item.evidence,
        "confidence": item.confidence,
    }


def _np_to_dict(item: NPFeature) -> JsonObject:
    result: JsonObject = {
        "id": item.id,
        "token_refs": list(item.token_refs),
        "head_ref": item.head,
        "head_lemma": item.head_lemma,
        "head_upos": item.head_upos,
        "determiner_refs": list(item.determiner_refs),
        "phrase_type": item.phrase_type,
        "grammar_eligibility": _grammar_eligibility_to_dict(
            item.grammar_eligibility
        ),
        "article_slot": _article_slot_to_dict(item.article_slot),
        "modifier_refs": [modifier.ref for modifier in item.modifiers],
        "quantifier_refs": [quantifier.ref for quantifier in item.quantifiers],
        "syntactic_role": item.syntactic_role,
        "evidence_refs": list(item.evidence_refs),
        "source": _flat_source(item.provenance),
        "confidence": item.confidence,
    }
    if item.number is not None:
        result["number"] = item.number
    if item.person is not None:
        result["person"] = item.person
    if item.possessive is not None:
        result["possessive_ref"] = item.possessive
    if item.plural_analysis is not None:
        result["plural_analysis"] = _plural_analysis_to_dict(item.plural_analysis)
    if item.countability is not None:
        result["countability"] = _countability_to_dict(item.countability)
    return result


def _grammar_eligibility_to_dict(item: GrammarEligibilityFeature) -> JsonObject:
    return {
        "article_choice_eligible": item.article_choice_eligible,
        "countability_choice_eligible": item.countability_choice_eligible,
        "plural_inflection_choice_eligible": item.plural_inflection_choice_eligible,
        "reason": item.reason,
    }


def _plural_analysis_to_dict(item: PluralAnalysisFeature) -> JsonObject:
    return {
        "number": item.number,
        "surface_plural_class": item.surface_plural_class,
        "lemma": item.lemma,
        "surface": item.surface,
        "confidence": item.confidence,
    }


def _determiner_to_dict(item: DeterminerFeature) -> JsonObject:
    result: JsonObject = {
        "ref": item.ref,
        "text": item.text,
        "lemma": item.lemma,
        "determiner_type": item.determiner_type,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.definite is not None:
        result["definite"] = item.definite
    if item.number is not None:
        result["number"] = item.number
    return result


def _article_slot_to_dict(item: ArticleSlotFeature) -> JsonObject:
    result: JsonObject = {
        "owner_np_id": item.owner_np_id,
        "article_presence": item.article_presence,
        "head_ref": item.head_ref,
        "following_word_ref": item.following_word_ref,
        "following_sound_class": item.following_sound_class or "unknown",
        "following_sound_source": item.following_sound_source,
        "following_sound_confidence": item.following_sound_confidence,
        "evidence_refs": list(item.evidence_refs),
        "source": item.source,
        "confidence": item.confidence,
    }
    if item.article_form is not None:
        result["article_form"] = item.article_form
    if item.determiner_ref is not None:
        result["determiner_ref"] = item.determiner_ref
    if item.definiteness is not None:
        result["definiteness"] = item.definiteness
    return result


def _word_order_to_dict(item: WordOrderFeature) -> JsonObject:
    return {
        "pattern": item.pattern,
        "ordered_refs": list(item.ordered_refs),
        "slots": dict(item.slots),
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }


def _negation_to_dict(item: NegationFeature) -> JsonObject:
    result: JsonObject = {
        "ref": item.ref,
        "negator": item.negator,
        "negation_type": item.negation_type,
        "scope": item.scope,
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.governor is not None:
        result["governor"] = item.governor
    return result


def _lexical_item_to_dict(item: LexicalItemFeature) -> JsonObject:
    return {
        "kind": item.kind,
        "refs": list(item.refs),
        "text": item.text,
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }


def _construction_to_dict(item: ConstructionFeature) -> JsonObject:
    result: JsonObject = {
        "key": item.key,
        "type": item.type,
        "signature": item.signature,
        "slots": _slots_to_dict(item.slots),
        "evidence_refs": list(item.evidence_refs),
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.family_hint is not None:
        result["family_hint"] = item.family_hint
    return result


def _slots_to_dict(slots: dict[str, SlotValue]) -> JsonObject:
    result: JsonObject = {}
    for key, value in slots.items():
        result[key] = list(value) if isinstance(value, tuple) else value
    return result


def _absence_to_dict(item: AbsenceFeature) -> JsonObject:
    result: JsonObject = {
        "scope": item.scope,
        "target": item.target,
        "anchor_ref": item.anchor_ref,
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.expected_position is not None:
        result["expected_position"] = item.expected_position
    return result


def _contrastive_to_dict(item: ContrastiveSupportFeature) -> JsonObject:
    return {
        "contrastive_hint": item.contrastive_hint,
        "observed_choice": item.observed_choice,
        "competing_choices": list(item.competing_choices),
        "local_cues": list(item.local_cues),
        "missing_context": list(item.missing_context),
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }


def _sentence_feature_to_dict(item: SentenceFeature) -> JsonObject:
    return {
        "sentence_kind": item.sentence_kind,
        "clause_count": item.clause_count,
        "sentence_type": item.sentence_type,
        "polarity": item.polarity,
        "has_subject_aux_inversion": item.has_subject_aux_inversion,
        "has_do_support": item.has_do_support,
        "has_wh_fronting": item.has_wh_fronting,
        "has_tag_question": item.has_tag_question,
        "has_exclamation_marker": item.has_exclamation_marker,
    }


def _diagnostic_to_dict(item: FeatureDiagnostic) -> JsonObject:
    result: JsonObject = {
        "severity": item.severity,
        "code": item.code,
        "message": item.message,
        "refs": list(item.refs),
    }
    if item.feature_path is not None:
        result["feature_path"] = item.feature_path
    return result


def ensure_json_object(value: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
    return value
