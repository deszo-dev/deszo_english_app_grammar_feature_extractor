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
    DirectSpeechSegmentFeature,
    DiscourseFeatures,
    EvidenceFeatures,
    FeatureDiagnostic,
    FeatureDiagnosticItem,
    FeatureDiagnostics,
    FeatureSupportItem,
    FutureMarkingFeature,
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
    MultiwordCueFeature,
    NarrationSegmentFeature,
    NegationFeature,
    NormalizedMorph,
    NPFeature,
    PageInfo,
    ParticipialClauseFeature,
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
    TimeExpressionFeature,
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
        "construction_signature_registry_version": "construction_signature_registry.v1",
        "page": _page_info_to_dict(page.page),
        "features": [_sentence_to_dict(sentence) for sentence in page.features],
    }


def document_to_dict(document: GrammarFeatureDocument) -> JsonObject:
    return {
        "schema_version": document.schema_version,
        "construction_signature_registry_version": "construction_signature_registry.v1",
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
    features = sentence.features
    return {
        "sentence_index": sentence.sentence_index,
        "text": sentence.text,
        "sentence": _sentence_feature_to_dict(features.lexical.sentence),
        "tokens": _tokens_to_dict(features.evidence),
        "syntax": _syntax_to_dict(features.syntax, features.lexical.sentence),
        "lexical": _lexical_v4_to_dict(features.lexical),
        "time_expressions": [
            _time_expression_to_dict(item) for item in features.time_expressions
        ],
        "discourse": _discourse_to_dict(features.discourse),
        "diagnostics": [_diagnostic_to_dict(item) for item in features.diagnostics],
        "feature_diagnostics": _feature_diagnostics_to_dict(
            features.feature_diagnostics
        ),
        "feature_support": {
            key: _feature_support_to_dict(value)
            for key, value in features.feature_support.items()
        },
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


def _syntax_to_dict(
    syntax: SyntaxFeatures,
    sentence: SentenceFeature | None = None,
) -> JsonObject:
    return {
        "clauses": [_clause_to_dict(item) for item in syntax.clauses],
        "predicates": [
            _predicate_to_dict(item, syntax.np_profiles, sentence)
            for item in syntax.predicates
        ],
        "np_profiles": [_np_to_dict(item) for item in syntax.np_profiles],
        "pps": [],
        "relative_clauses": [
            _relative_clause_to_dict(item) for item in syntax.relative_clauses
        ],
        "participial_clauses": [
            _participial_clause_to_dict(item) for item in syntax.participial_clauses
        ],
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
        "id": item.id,
        "clause_id": item.clause_id,
        "antecedent_np_id": item.antecedent_np_id,
        "relative_marker_ref": item.relative_marker,
        "relative_marker_surface": item.marker_text,
        "relative_role": item.relative_role,
        "object_gap": item.object_gap,
        "is_omitted_relative_pronoun": item.is_omitted_relative_pronoun,
        "defining_status": item.defining_status,
        "comma_delimited": item.comma_delimited,
        "source": item.source,
        "evidence_refs": list(item.evidence_refs),
        "confidence": item.confidence,
    }
    return result


def _participial_clause_to_dict(item: ParticipialClauseFeature) -> JsonObject:
    return {
        "id": item.id,
        "head_ref": item.head_ref,
        "voice": item.voice,
        "clause_type": item.clause_type,
        "modified_np_id": item.modified_np_id,
        "has_by_agent": item.has_by_agent,
        "by_agent_np_id": item.by_agent_np_id,
        "source": item.source,
        "confidence": item.confidence,
        "evidence_refs": list(item.evidence_refs),
    }


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


def _predicate_to_dict(
    item: PredicateFeature,
    np_profiles: tuple[NPFeature, ...] = (),
    sentence: SentenceFeature | None = None,
) -> JsonObject:
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
    if item.future_marking is not None:
        result["future_marking"] = _future_marking_to_dict(item.future_marking)
    if item.predicate_type == "existential_there":
        expletive = _expletive_there_ref(item)
        postverbal_np_id = _postverbal_np_id(item, np_profiles)
        if expletive is not None:
            result["expletive_subject_ref"] = expletive
        if postverbal_np_id is not None:
            result["postverbal_np_id"] = postverbal_np_id
        if sentence is not None:
            result["has_subject_aux_inversion"] = sentence.has_subject_aux_inversion
            result["sentence_type"] = sentence.sentence_type
    return result


def _future_marking_to_dict(item: FutureMarkingFeature) -> JsonObject:
    return {
        "be_going_to": item.be_going_to,
        "will_shall": item.will_shall,
        "future_time_expression_ids": list(item.future_time_expression_ids),
        "future_orientation": item.future_orientation,
        "source": item.source,
        "confidence": item.confidence,
        "evidence_refs": list(item.evidence_refs),
    }


def _expletive_there_ref(item: PredicateFeature) -> int | None:
    return item.expletive_subject


def _postverbal_np_id(
    item: PredicateFeature,
    np_profiles: tuple[NPFeature, ...],
) -> str | None:
    candidates = [
        np
        for np in np_profiles
        if np.head > item.main
        and np.head != item.expletive_subject
        and np.phrase_type != "pronoun_np"
    ]
    if not candidates:
        return None
    return candidates[0].id


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


def _lexical_v4_to_dict(lexical: LexicalFeatures) -> JsonObject:
    return {
        "multiword_cues": [
            _multiword_cue_to_dict(item) for item in lexical.multiword_cues
        ]
    }


def _multiword_cue_to_dict(item: MultiwordCueFeature) -> JsonObject:
    return {
        "cue_key": item.cue_key,
        "surface_refs": list(item.surface_refs),
        "lemma_sequence": list(item.lemma_sequence),
        "surface_sequence": list(item.surface_sequence),
        "scope_type": item.scope_type,
        "scope_owner_id": item.scope_owner_id,
        "scope_status": item.scope_status,
        "contiguous": item.contiguous,
        "source": item.source,
        "confidence": item.confidence,
        "evidence_refs": list(item.evidence_refs),
    }


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
        "sentence_type": item.sentence_type,
        "terminal_punctuation": item.terminal_punctuation,
        "terminal_question_mark": item.terminal_question_mark,
        "question_type": item.question_type,
        "polarity": item.polarity,
        "has_subject_aux_inversion": item.has_subject_aux_inversion,
        "has_do_support": item.has_do_support,
        "has_wh_fronting": item.has_wh_fronting,
        "has_tag_question": item.has_tag_question,
        "sentence_type_confidence": item.sentence_type_confidence,
        "evidence_refs": list(item.evidence_refs),
    }


def _time_expression_to_dict(item: TimeExpressionFeature) -> JsonObject:
    return {
        "id": item.id,
        "token_refs": list(item.token_refs),
        "surface": item.surface,
        "time_kind": item.time_kind,
        "source": item.source,
        "confidence": item.confidence,
        "evidence_refs": list(item.evidence_refs),
    }


def _discourse_to_dict(item: DiscourseFeatures) -> JsonObject:
    return {
        "quote_segmentation_status": item.quote_segmentation_status,
        "direct_speech_segments": [
            _direct_speech_segment_to_dict(segment)
            for segment in item.direct_speech_segments
        ],
        "narration_segments": [
            _narration_segment_to_dict(segment) for segment in item.narration_segments
        ],
    }


def _direct_speech_segment_to_dict(item: DirectSpeechSegmentFeature) -> JsonObject:
    return {
        "segment_id": item.segment_id,
        "token_refs": list(item.token_refs),
        "speaker_tag_predicate_id": item.speaker_tag_predicate_id,
        "speaker_np_id": item.speaker_np_id,
        "quote_type": item.quote_type,
        "source": item.source,
        "confidence": item.confidence,
        "evidence_refs": list(item.evidence_refs),
    }


def _narration_segment_to_dict(item: NarrationSegmentFeature) -> JsonObject:
    return {
        "segment_id": item.segment_id,
        "token_refs": list(item.token_refs),
        "source": item.source,
        "confidence": item.confidence,
        "evidence_refs": list(item.evidence_refs),
    }


def _feature_diagnostics_to_dict(item: FeatureDiagnostics) -> JsonObject:
    return {
        "missing_expected_layers": [
            _feature_diagnostic_item_to_dict(entry)
            for entry in item.missing_expected_layers
        ],
        "low_confidence_features": [
            _feature_diagnostic_item_to_dict(entry)
            for entry in item.low_confidence_features
        ],
        "unsupported_features": [
            _feature_diagnostic_item_to_dict(entry)
            for entry in item.unsupported_features
        ],
        "feature_layer_warnings": [
            _feature_diagnostic_item_to_dict(entry)
            for entry in item.feature_layer_warnings
        ],
    }


def _feature_diagnostic_item_to_dict(item: FeatureDiagnosticItem) -> JsonObject:
    result: JsonObject = {"reason": item.reason}
    if item.layer is not None:
        result["layer"] = item.layer
    if item.feature_path is not None:
        result["feature_path"] = item.feature_path
    if item.severity is not None:
        result["severity"] = item.severity
    if item.confidence is not None:
        result["confidence"] = item.confidence
    return result


def _feature_support_to_dict(item: FeatureSupportItem) -> JsonObject:
    return {
        "status": item.status,
        "source": item.source,
        "confidence": item.confidence,
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
