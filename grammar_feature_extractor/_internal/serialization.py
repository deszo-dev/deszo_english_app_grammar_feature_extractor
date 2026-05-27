from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TypeAlias, cast

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
    ModifierFeature,
    MorphFeature,
    MorphologyFeatures,
    MultiwordCueFeature,
    NarrationSegmentFeature,
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
    QuantifierFeature,
    ReferenceFeature,
    RelativeClauseFeature,
    ReportedSpeechFeature,
    Roles,
    SentenceFeature,
    SentenceGrammarFeatures,
    SlotValue,
    SpecialSubjectConstructionFeature,
    StanzaDocumentInputLineage,
    SyntaxFeatures,
    TAVMFeature,
    TimeExpressionFeature,
    TokenEvidence,
    TypedQuantifierFeature,
    Valency,
    VerbPatternFeature,
    WordOrderFeature,
)
from grammar_feature_extractor._internal.runtime_metadata import (
    contract_runtime_metadata,
)
from grammar_feature_extractor._internal.validation import parse_annotated_document

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]
SerializationContext: TypeAlias = dict[str, object]


def loads_document(payload: str) -> AnnotatedDocument:
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SerializationError("Invalid input JSON.") from exc
    return parse_annotated_document(raw)


def dumps_page(page: GrammarFeaturePage) -> str:
    return json.dumps(page_to_dict(page), ensure_ascii=False, indent=2) + "\n"


def page_to_dict(page: GrammarFeaturePage) -> JsonObject:
    return {
        "schema_version": page.schema_version,
        "kind": "grammar_feature_page",
        "runtime_metadata": _coerce_json_object(contract_runtime_metadata()),
        "input_lineage": _input_lineage_to_dict(page.input_lineage),
        "output_completeness": _output_completeness_from_sentences(page.features),
        "diagnostic_summary": _page_diagnostic_summary(page.features),
        "char_offset_space": "document_global",
        "page": _page_info_to_dict(page.page),
        "features": [_sentence_to_dict(sentence) for sentence in page.features],
    }


def _page_diagnostic_summary(
    sentences: tuple[SentenceGrammarFeatures, ...],
) -> JsonObject:
    by_group: dict[str, dict[str, int]] = {}
    by_code: dict[str, int] = {}
    total = 0
    for sentence in sentences:
        for diagnostic in sentence.features.diagnostics:
            normalized = _normalized_diagnostic(diagnostic)
            if normalized is None:
                continue
            total += 1
            code = normalized.code
            by_code[code] = by_code.get(code, 0) + 1
            path = normalized.feature_path or "features"
            group = path.split("[")[0]
            bucket = by_group.setdefault(group, {})
            bucket[normalized.severity] = bucket.get(normalized.severity, 0) + 1
    return {
        "by_group": {
            group: dict(sorted(severities.items()))
            for group, severities in sorted(by_group.items())
        },
        "by_code": dict(sorted(by_code.items())),
        "total": total,
    }


def document_to_dict(document: GrammarFeatureDocument) -> JsonObject:
    return {
        "schema_version": document.schema_version,
        "kind": "grammar_feature_document",
        "runtime_metadata": _coerce_json_object(contract_runtime_metadata()),
        "input_lineage": _input_lineage_to_dict(document.input_lineage),
        "output_completeness": _output_completeness_from_sentences(document.sentences),
        "char_offset_space": "document_global",
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
    context = _make_serialization_context(sentence)
    result: JsonObject = {
        "sentence_index": sentence.sentence_index,
        "text": sentence.text,
        "features": _feature_set_to_dict(sentence.features, context),
    }
    if sentence.global_sentence_id is not None:
        result["global_sentence_id"] = sentence.global_sentence_id
    if sentence.global_sentence_index is not None:
        result["global_sentence_index"] = sentence.global_sentence_index
    if sentence.local_sentence_index is not None:
        result["local_sentence_index"] = sentence.local_sentence_index
    if sentence.source_unit_id is not None:
        result["source_unit_id"] = sentence.source_unit_id
    if sentence.source_unit_order is not None:
        result["source_unit_order"] = sentence.source_unit_order
    if sentence.source_unit_type is not None:
        result["source_unit_type"] = sentence.source_unit_type
    if sentence.source_unit_role is not None:
        result["source_unit_role"] = sentence.source_unit_role
    if sentence.source_text_hash is not None:
        result["source_text_hash"] = sentence.source_text_hash
    return result


def _input_lineage_to_dict(lineage: StanzaDocumentInputLineage) -> JsonObject:
    result: JsonObject = {
        "source_module": lineage.source_module,
        "source_schema_version": lineage.source_schema_version,
        "document_id": lineage.document_id,
        "source_status": lineage.source_status,
        "selected_unit_count": lineage.selected_unit_count,
        "global_sentence_count": lineage.global_sentence_count,
        "global_word_count": lineage.global_word_count,
    }
    if lineage.language is not None:
        result["language"] = lineage.language
    return result


def _feature_set_to_dict(
    features: GrammarFeatureSet,
    context: SerializationContext,
) -> JsonObject:
    return {
        "evidence": _evidence_to_dict(features.evidence),
        "morphology": _morphology_to_dict(features.morphology, context),
        "syntax": _syntax_to_dict(
            features.syntax,
            features.lexical.sentence,
            features.evidence,
            context,
        ),
        "lexical": _lexical_to_dict(features.lexical, features.evidence, context),
        "constructions": [
            _construction_to_dict(item, context, index)
            for index, item in enumerate(features.constructions, start=1)
        ],
        "contrastive_support": [
            _contrastive_to_dict(item, context, index)
            for index, item in enumerate(features.contrastive_support, start=1)
        ],
        "absences": [
            _absence_to_dict(item, context, index)
            for index, item in enumerate(features.absences, start=1)
        ],
        "diagnostics": [
            diagnostic
            for item in features.diagnostics
            for diagnostic in [_diagnostic_to_dict(item)]
            if diagnostic is not None
        ],
        "processing_support": _processing_support_to_dict(features.processing_support),
    }


def _processing_support_to_dict(support: object) -> JsonObject:
    from grammar_feature_extractor._internal.models import (  # local to avoid cycle
        FeatureCoverage,
        FeatureGroupQuality,
        LocalContext,
        ProcessingSupport,
    )

    if support is None:
        support = ProcessingSupport()
    quality = support.quality if isinstance(support.quality, FeatureGroupQuality) else FeatureGroupQuality()
    coverage = support.coverage if isinstance(support.coverage, FeatureCoverage) else FeatureCoverage()
    local_context = (
        support.local_context
        if isinstance(support.local_context, LocalContext)
        else LocalContext()
    )

    return {
        "quality": _quality_to_dict(quality),
        "coverage": _coverage_to_dict(coverage),
        "candidate_features": [
            _candidate_feature_to_dict(c) for c in support.candidate_features
        ],
        "normalization_trace": [
            _normalization_trace_to_dict(t) for t in support.normalization_trace
        ],
        "construction_family_summary": {
            family: _construction_family_summary_to_dict(summary)
            for family, summary in support.construction_family_summary.items()
        },
        "feature_conflicts": [
            _feature_conflict_to_dict(c) for c in support.feature_conflicts
        ],
        "negative_evidence": [
            _negative_evidence_to_dict(n) for n in support.negative_evidence
        ],
        "pattern_windows": [
            _pattern_window_to_dict(w) for w in support.pattern_windows
        ],
        "local_context": _local_context_to_dict(local_context),
    }


def _quality_to_dict(q: object) -> JsonObject:
    result: JsonObject = {"overall": q.overall}
    for attr in (
        "evidence",
        "morphology",
        "dependencies",
        "predicates",
        "clauses",
        "np_profiles",
        "constructions",
        "lexical",
        "recommended_processing_mode",
    ):
        value = getattr(q, attr, None)
        if value is not None:
            result[attr] = value
    if q.reason_codes:
        result["reason_codes"] = list(q.reason_codes)
    return result


def _coverage_to_dict(coverage: object) -> JsonObject:
    result: JsonObject = {}
    for attr in (
        "predicate_detection",
        "clause_detection",
        "np_detection",
        "construction_detection",
        "lexical_detection",
        "absence_detection",
    ):
        entry = getattr(coverage, attr, None)
        if entry is not None:
            result[attr] = _coverage_entry_to_dict(entry)
    return result


def _coverage_entry_to_dict(entry: object) -> JsonObject:
    result: JsonObject = {
        "status": entry.status,
        "emitted": entry.emitted,
        "reason_codes": list(entry.reason_codes),
    }
    if entry.expected is not None:
        result["expected"] = entry.expected
    if entry.families_attempted:
        result["families_attempted"] = list(entry.families_attempted)
    if entry.families_omitted:
        result["families_omitted"] = list(entry.families_omitted)
    return result


def _candidate_feature_to_dict(c: object) -> JsonObject:
    result: JsonObject = {
        "candidate_id": c.candidate_id,
        "group": c.group,
        "decision": c.decision,
        "reason": c.reason,
        "evidence_refs": list(c.evidence_refs),
        "confidence": c.confidence,
    }
    if c.candidate_type is not None:
        result["candidate_type"] = c.candidate_type
    if c.signature is not None:
        result["signature"] = c.signature
    return result


def _normalization_trace_to_dict(trace: object) -> JsonObject:
    result: JsonObject = {
        "trace_id": trace.trace_id,
        "target_group": trace.target_group,
        "steps": [_normalization_step_to_dict(s) for s in trace.steps],
    }
    if trace.target_feature_id is not None:
        result["target_feature_id"] = trace.target_feature_id
    if trace.nearest_known_signatures:
        result["nearest_known_signatures"] = list(trace.nearest_known_signatures)
    return result


def _normalization_step_to_dict(step: object) -> JsonObject:
    result: JsonObject = {"step": step.step, "result": step.result}
    if step.refs:
        result["refs"] = list(step.refs)
    if step.reason is not None:
        result["reason"] = step.reason
    return result


def _construction_family_summary_to_dict(summary: object) -> JsonObject:
    result: JsonObject = {
        "count": summary.count,
        "signatures": list(summary.signatures),
        "status": summary.status,
    }
    if summary.reason_codes:
        result["reason_codes"] = list(summary.reason_codes)
    return result


def _feature_conflict_to_dict(c: object) -> JsonObject:
    result: JsonObject = {
        "conflict_id": c.conflict_id,
        "type": c.type,
        "feature_paths": list(c.feature_paths),
        "evidence_refs": list(c.evidence_refs),
        "resolution": c.resolution,
    }
    if c.winner is not None:
        result["winner"] = c.winner
    if c.confidence_after_resolution is not None:
        result["confidence_after_resolution"] = c.confidence_after_resolution
    return result


def _negative_evidence_to_dict(item: object) -> JsonObject:
    result: JsonObject = {
        "target": item.target,
        "scope": item.scope,
        "anchor_ref": item.anchor_ref,
        "checked_window": list(item.checked_window),
        "result": item.result,
        "confidence": item.confidence,
    }
    if item.interpretation is not None:
        result["interpretation"] = item.interpretation
    return result


def _pattern_window_to_dict(window: object) -> JsonObject:
    return {
        "window_id": window.window_id,
        "anchor_ref": window.anchor_ref,
        "window_type": window.window_type,
        "refs": list(window.refs),
        "surface": window.surface,
        "lemmas": list(window.lemmas),
        "upos": list(window.upos),
        "deprels": list(window.deprels),
    }


def _local_context_to_dict(ctx: object) -> JsonObject:
    result: JsonObject = {
        "paragraph_position": ctx.paragraph_position,
        "same_unit_previous_sentence_available": ctx.same_unit_previous_sentence_available,
        "same_unit_next_sentence_available": ctx.same_unit_next_sentence_available,
        "quote_continuation_state": ctx.quote_continuation_state,
    }
    if ctx.previous_sentence_index is not None:
        result["previous_sentence_index"] = ctx.previous_sentence_index
    if ctx.next_sentence_index is not None:
        result["next_sentence_index"] = ctx.next_sentence_index
    return result


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
    if item.source_word_id is not None:
        result["source_word_id"] = item.source_word_id
    if item.source_token_id is not None:
        result["source_token_id"] = item.source_token_id
    if item.source_unit_id is not None:
        result["source_unit_id"] = item.source_unit_id
    return result


def _dependency_evidence_to_dict(item: DependencyEvidence) -> JsonObject:
    return {
        "governor": item.governor,
        "dependent": item.dependent,
        "deprel": item.deprel,
    }


def _morphology_to_dict(
    morphology: MorphologyFeatures,
    context: SerializationContext,
) -> JsonObject:
    return {
        "word_morphology": [
            _morph_feature_to_dict(item, context, index)
            for index, item in enumerate(morphology.word_morphology, start=1)
        ],
        "normalized": [
            _normalized_morph_to_dict(item, context, index)
            for index, item in enumerate(morphology.normalized, start=1)
        ],
    }


def _morph_feature_to_dict(
    item: MorphFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "morphology", index),
        "ref": item.ref,
        "pos": item.pos,
        "lemma": item.lemma,
        "features": _schema_morph_features(item.features),
        "provenance": _synthetic_provenance(item.ref, "morphology"),
    }
    if item.xpos is not None:
        result["xpos"] = item.xpos
    return result


def _normalized_morph_to_dict(
    item: NormalizedMorph,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    return {
        "id": _feature_id(context, "normalized_morphology", index),
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
        "provenance": _synthetic_provenance(item.ref, "morphology"),
    }


def _syntax_to_dict(
    syntax: SyntaxFeatures,
    sentence: SentenceFeature | None,
    evidence: EvidenceFeatures,
    context: SerializationContext,
) -> JsonObject:
    return {
        "phrases": [
            _phrase_to_dict(item, context, index)
            for index, item in enumerate(syntax.phrases, start=1)
        ],
        "clauses": [
            _clause_to_dict(item, context, index)
            for index, item in enumerate(syntax.clauses, start=1)
        ],
        "predicates": [
            _predicate_to_dict(item, syntax.np_profiles, sentence, context, index)
            for index, item in enumerate(syntax.predicates, start=1)
        ],
        "complements": [
            _complement_to_dict(item, context, index)
            for index, item in enumerate(syntax.complements, start=1)
        ],
        "coordination": [
            _coordination_to_dict(item, evidence, context, index)
            for index, item in enumerate(syntax.coordination, start=1)
        ],
        "subordination": [
            _clause_marker_to_dict(item, context, index)
            for index, item in enumerate(syntax.subordination, start=1)
        ],
        "np_profiles": [
            _np_to_dict(item, context, index)
            for index, item in enumerate(syntax.np_profiles, start=1)
        ],
        "pronouns": [
            _pronoun_to_dict(item, context, index)
            for index, item in enumerate(syntax.pronouns, start=1)
        ],
        "special_subject_constructions": [
            _special_subject_to_dict(item, context, index)
            for index, item in enumerate(
                syntax.special_subject_constructions,
                start=1,
            )
        ],
        "relative_clauses": [
            _relative_clause_to_dict(item, context, index)
            for index, item in enumerate(syntax.relative_clauses, start=1)
        ],
        "conditionals": [
            _conditional_to_dict(item, context, index)
            for index, item in enumerate(syntax.conditionals, start=1)
        ],
        "reported_speech": [
            _reported_speech_to_dict(item, context, index)
            for index, item in enumerate(syntax.reported_speech, start=1)
        ],
        "passive": [
            _passive_to_dict(item, context, index)
            for index, item in enumerate(syntax.passive, start=1)
        ],
    }


def _pronoun_to_dict(
    item: PronounFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "pronoun", index),
        "ref": item.ref,
        "lemma": item.lemma,
        "pronoun_type": item.pronoun_type,
        "provenance": _synthetic_provenance(item.ref, "lemma"),
    }
    if item.person is not None:
        result["person"] = item.person
    if item.number is not None:
        result["number"] = item.number
    if item.case is not None:
        result["case"] = item.case
    return result


def _special_subject_to_dict(
    item: SpecialSubjectConstructionFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "special_subject", index),
        "type": item.type,
        "subject_ref": item.subject_ref,
        "predicate_ref": item.predicate_ref,
        "evidence_refs": list(item.evidence_refs),
        "confidence": item.confidence,
        "provenance": _synthetic_provenance_from_refs(
            item.evidence_refs,
            "dependency",
            item.confidence,
        ),
    }
    if item.notional_subject is not None:
        result["notional_subject"] = item.notional_subject
    if item.agreement_controller is not None:
        result["agreement_controller"] = item.agreement_controller
    return result


def _relative_clause_to_dict(
    item: RelativeClauseFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "relative_clause", index),
        "clause_id": _mapped_id(context, "clause_ids", item.clause_id, item.clause_id),
        "head_noun": item.head_noun,
        "relative_type": item.relative_type,
        "confidence": item.confidence,
        "provenance": _synthetic_provenance_from_refs(
            item.evidence_refs,
            item.source,
            item.confidence,
        ),
    }
    if item.relative_marker is not None:
        result["relative_marker"] = item.relative_marker
    if item.marker_text is not None:
        result["marker_text"] = item.marker_text
    if item.restrictive is not None:
        result["restrictive"] = item.restrictive
    return result


def _conditional_to_dict(
    item: ConditionalFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "conditional", index),
        "if_clause": _mapped_clause_ref(context, item.if_clause),
        "main_clause": _mapped_clause_ref(context, item.main_clause),
        "conditional_type": item.conditional_type,
        "main_tavm": _tavm_to_dict(item.main_tavm),
        "subordinate_tavm": _tavm_to_dict(item.subordinate_tavm),
        "confidence": item.confidence,
        "provenance": _synthetic_provenance_from_refs(
            (item.if_marker_ref,) if item.if_marker_ref is not None else (),
            "dependency",
            item.confidence,
        ),
    }
    if item.if_marker_ref is not None:
        result["if_marker_ref"] = item.if_marker_ref
    return result


def _reported_speech_to_dict(
    item: ReportedSpeechFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "reported_speech", index),
        "reporting_verb": item.reporting_verb,
        "reported_clause_head": item.reported_clause_head,
        "report_type": item.report_type,
        "backshift_candidate": item.backshift_candidate,
        "speaker_or_addressee_refs": list(item.speaker_or_addressee_refs),
        "confidence": item.confidence,
        "provenance": _synthetic_provenance_from_refs(
            (item.reporting_verb, item.reported_clause_head),
            "dependency",
            item.confidence,
        ),
    }
    if item.marker is not None:
        result["marker"] = item.marker
    return result


def _passive_to_dict(
    item: PassiveFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "passive", index),
        "predicate": item.predicate,
        "passive_type": item.passive_type,
        "aux_refs": list(item.aux_refs),
        "participle_ref": item.participle_ref,
        "confidence": item.confidence,
        "provenance": _synthetic_provenance_from_refs(
            (item.predicate, item.participle_ref),
            "dependency",
            item.confidence,
        ),
    }
    if item.agent_by_phrase:
        result["agent_by_phrase"] = list(item.agent_by_phrase)
    if item.patient_subject is not None:
        result["patient_subject"] = item.patient_subject
    return result


def _phrase_to_dict(
    item: Phrase,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    return {
        "id": _feature_id(context, "phrase", index),
        "type": item.type,
        "head": item.head,
        "tokens": list(item.tokens),
        "provenance": _provenance_to_dict(item.provenance),
    }


def _clause_to_dict(
    item: ClauseFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "clause", index),
        "head": item.head,
        "type": item.type,
        "finite": item.finite,
        "roles": _roles_to_dict(item.roles),
        "valency": _valency_to_dict(item.valency),
        "tokens": list(item.tokens),
        "local_tokens": list(item.local_tokens),
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.subject is not None:
        result["subject"] = item.subject
    if item.predicate is not None:
        result["predicate"] = item.predicate
    if item.marker is not None:
        result["marker"] = _clause_marker_to_dict(
            item.marker, context, index, group="clause_marker_inline"
        )
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


def _clause_marker_to_dict(
    item: ClauseMarkerFeature,
    context: SerializationContext,
    index: int,
    group: str = "clause_marker",
) -> JsonObject:
    return {
        "id": _feature_id(context, group, index),
        "marker_ref": item.marker_ref,
        "marker": item.marker,
        "clause_head": item.clause_head,
        "marker_type": item.marker_type,
        "confidence": item.confidence,
        "sources": list(item.sources),
        "provenance": _provenance_to_dict(item.provenance),
    }


def _complement_to_dict(
    item: PredicateComplementFeature,
    context: SerializationContext,
    index: int,
    group: str = "complement",
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, group, index),
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
    context: SerializationContext | None = None,
    index: int = 1,
) -> JsonObject:
    assert context is not None
    result: JsonObject = {
        "id": _feature_id(context, "predicate", index),
        "main": item.main,
        "main_lemma": item.main_lemma,
        "predicate_type": _schema_predicate_type(item.predicate_type),
        "finite": item.finite,
        "auxiliaries": [
            _auxiliary_to_dict(auxiliary) for auxiliary in item.auxiliaries
        ],
        "tense": item.tense,
        "aspect": item.aspect,
        "voice": _schema_voice(item.voice),
        "polarity": item.polarity,
        "clause_head": item.clause_head,
        "complements": [
            _complement_to_dict(
                complement,
                context,
                index * 1000 + complement_index,
                group="predicate_complement",
            )
            for complement_index, complement in enumerate(item.complements, start=1)
        ],
        "agreement": _agreement_to_dict(item.agreement),
        "tavm": _tavm_to_dict(item.tavm),
        "form_signature": item.form_signature,
        "evidence_refs": list(item.evidence_refs),
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.copula is not None:
        result["copula"] = item.copula
    if item.negation is not None:
        result["negation"] = item.negation
    if item.subject is not None:
        result["subject"] = item.subject
    if item.object is not None:
        result["object"] = item.object
    if item.indirect_object is not None:
        result["indirect_object"] = item.indirect_object
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
        "id": f"modal-{item.marker_refs[0]}" if item.marker_refs else "modal-0",
        "marker_refs": list(item.marker_refs),
        "modal_type": item.modal_type,
        "polarity": item.polarity,
        "confidence": item.confidence,
        "provenance": _synthetic_provenance_from_refs(
            item.marker_refs,
            "dependency",
            item.confidence,
        ),
    }
    if item.complement_verb is not None:
        result["complement_verb"] = item.complement_verb
    return result


def _agreement_to_dict(item: AgreementFeature) -> JsonObject:
    result: JsonObject = {
        "agreement_type": item.agreement_type,
        "evidence_refs": _dedupe_int_refs(item.evidence_refs),
        "confidence": item.confidence,
        "provenance": _synthetic_provenance_from_refs(
            item.evidence_refs,
            "dependency",
            item.confidence,
        ),
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
        "voice": _schema_voice(item.voice),
        "modality": _schema_modality(item.modality),
        "form_signature": item.form_signature,
    }


def _coordination_to_dict(
    item: Coordination,
    evidence: EvidenceFeatures,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    coordinator_ref = _find_coordinator_ref(item, evidence)
    return {
        "id": _feature_id(context, "coordination", index),
        "conjunct_refs": _dedupe_int_refs(item.conjuncts),
        "head_ref": item.head,
        "coordination_type": _schema_coordination_type("clausal_or_phrasal"),
        "evidence_refs": _dedupe_int_refs(item.provenance.evidence_refs),
        "provenance": _provenance_to_dict(item.provenance),
        "confidence": item.provenance.confidence,
        **({"coordinator_ref": coordinator_ref} if coordinator_ref is not None else {}),
    }


def _provenance_to_dict(item: ProofProvenance) -> JsonObject:
    return {
        "tier": item.tier,
        "source": item.source,
        "evidence_refs": _dedupe_int_refs(item.evidence_refs),
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


def _lexical_to_dict(
    lexical: LexicalFeatures,
    evidence: EvidenceFeatures,
    context: SerializationContext,
) -> JsonObject:
    return {
        "sentence": _sentence_feature_to_dict(lexical.sentence),
        "word_order": [
            _word_order_to_dict(item, context, index)
            for index, item in enumerate(lexical.word_order, start=1)
        ],
        "negation": [
            _negation_to_dict(item, context, index, evidence)
            for index, item in enumerate(lexical.negation, start=1)
        ],
        "time_markers": [
            _time_marker_to_dict(item, context, index)
            for index, item in enumerate(lexical.time_markers, start=1)
        ],
        "lexical_classes": [
            _lexical_class_to_dict(item, context, index)
            for index, item in enumerate(lexical.lexical_classes, start=1)
        ],
        "verb_patterns": [
            _verb_pattern_to_dict(item, context, index)
            for index, item in enumerate(lexical.verb_patterns, start=1)
        ],
        "adjective_patterns": [
            _adjective_pattern_to_dict(item, context, index)
            for index, item in enumerate(lexical.adjective_patterns, start=1)
        ],
        "comparisons": [
            _comparison_to_dict(item, context, index)
            for index, item in enumerate(lexical.comparisons, start=1)
        ],
        "quantifiers": [
            _typed_quantifier_to_dict(item, context, index)
            for index, item in enumerate(lexical.quantifiers, start=1)
        ],
        "phrasal_verbs": [
            _phrasal_verb_to_dict(item, context, index)
            for index, item in enumerate(lexical.phrasal_verbs, start=1)
        ],
        "discourse_markers": [
            _discourse_marker_to_dict(item, context, index)
            for index, item in enumerate(lexical.discourse_markers, start=1)
        ],
        "contractions": [
            _contraction_to_dict(item, context, index)
            for index, item in enumerate(lexical.contractions, start=1)
        ],
        "noun_inflections": [
            _noun_inflection_to_dict(item, context, index, evidence)
            for index, item in enumerate(lexical.noun_inflections, start=1)
        ],
    }


def _lexical_class_to_dict(
    item: LexicalClassFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    return {
        "id": _feature_id(context, "lexical_class", index),
        "ref": item.ref,
        "lemma": item.lemma,
        "classes": list(item.classes),
        "source": item.source,
        "confidence": item.confidence,
        "provenance": _synthetic_provenance(item.ref, item.source, item.confidence),
    }


def _verb_pattern_to_dict(
    item: VerbPatternFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    return {
        "id": _feature_id(context, "verb_pattern", index),
        "predicate": item.predicate,
        "lemma": item.lemma,
        "pattern": item.pattern,
        "complements": [
            _complement_to_dict(
                complement,
                context,
                index * 1000 + complement_index,
                group="verb_pattern_complement",
            )
            for complement_index, complement in enumerate(item.complements, start=1)
        ],
        "confidence": item.confidence,
        "provenance": _synthetic_provenance(item.predicate, "lemma", item.confidence),
    }


def _adjective_pattern_to_dict(
    item: AdjectivePatternFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "adjective_pattern", index),
        "adjective": item.adjective,
        "lemma": item.lemma,
        "pattern": item.pattern,
        "confidence": item.confidence,
        "provenance": _synthetic_provenance(item.adjective, "lemma", item.confidence),
    }
    if item.complement is not None:
        result["complement"] = _complement_to_dict(item.complement, context, 1)
    if item.degree_modifier is not None:
        result["degree_modifier"] = item.degree_modifier
    return result


def _typed_quantifier_to_dict(
    item: TypedQuantifierFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "quantifier", index),
        "ref": item.ref,
        "text": item.text,
        "quantifier_type": item.quantifier_type,
        "provenance": _synthetic_provenance(item.ref, "surface"),
    }
    if item.compatible_number is not None:
        result["compatible_number"] = item.compatible_number
    if item.polarity_sensitivity is not None:
        result["polarity_sensitivity"] = item.polarity_sensitivity
    return result


def _countability_to_dict(item: CountabilityFeature) -> JsonObject | None:
    if item.status == "pronoun_not_applicable":
        return None
    return {
        "value": item.status,
        "source": _schema_countability_source(item.source),
        "confidence": item.confidence,
        "provenance": _synthetic_provenance_from_refs(
            tuple(item.evidence_refs), item.source, item.confidence
        ),
    }


def _reference_to_dict(item: ReferenceFeature) -> JsonObject:
    return {
        "reference_status": item.reference_status,
        "evidence": item.evidence,
        "confidence": item.confidence,
        "provenance": _synthetic_provenance_from_refs((), "surface", item.confidence),
    }


def _np_to_dict(
    item: NPFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "np", index),
        "head": item.head,
        "head_lemma": item.head_lemma,
        "phrase_type": item.phrase_type,
        "has_determiner": item.has_determiner,
        "article_slot": _article_slot_to_dict(item.article_slot),
        "modifiers": [_modifier_to_dict(modifier) for modifier in item.modifiers],
        "quantifiers": [
            _np_quantifier_to_dict(quantifier, context, quantifier_index)
            for quantifier_index, quantifier in enumerate(item.quantifiers, start=1)
        ],
        "syntactic_role": item.syntactic_role,
        "evidence_refs": list(item.evidence_refs),
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.determiner is not None:
        result["determiner"] = _determiner_to_dict(item.determiner, context, index)
    if item.number is not None:
        result["number"] = item.number
    if item.person is not None:
        result["person"] = item.person
    if item.possessive is not None:
        result["possessive"] = item.possessive
    if item.countability is not None:
        countability = _countability_to_dict(item.countability)
        if countability is not None:
            result["countability"] = countability
    if item.reference is not None:
        result["reference"] = _reference_to_dict(item.reference)
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


def _determiner_to_dict(
    item: DeterminerFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "determiner", index),
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
        "requiredness": item.requiredness,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.article_form is not None:
        result["article_form"] = item.article_form
    if item.following_sound_class is not None:
        result["following_sound_class"] = item.following_sound_class
    if item.following_spelling_class is not None:
        result["following_spelling_class"] = item.following_spelling_class
    if item.definiteness is not None:
        result["definiteness"] = item.definiteness
    return result


def _word_order_to_dict(
    item: WordOrderFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    return {
        "id": _feature_id(context, "word_order", index),
        "pattern": item.pattern,
        "ordered_refs": list(item.ordered_refs),
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }


def _negation_to_dict(
    item: NegationFeature,
    context: SerializationContext,
    index: int,
    evidence: EvidenceFeatures,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "negation", index),
        "ref": item.ref,
        "negator_kind": _schema_negator_kind(item.negator),
        "surface": _surface_text(evidence, item.ref),
        "scope": item.scope,
        "polarity_effect": "negative",
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.governor is not None:
        result["governor"] = item.governor
    return result


def _construction_to_dict(
    item: ConstructionFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "construction", index),
        "key": item.key,
        "type": item.type,
        "signature": _schema_construction_signature(item.signature),
        "slots": _slots_to_dict(item.slots),
        "evidence_refs": _dedupe_int_refs(item.evidence_refs),
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.family_hint is not None:
        result["family_hint"] = item.family_hint
    return result


def _slots_to_dict(slots: dict[str, SlotValue]) -> JsonObject:
    slot_name_map = {
        "article_form": "article",
    }
    result: JsonObject = {}
    for key, value in slots.items():
        mapped_key = slot_name_map.get(key, key)
        result[mapped_key] = list(value) if isinstance(value, tuple) else value
    return result


def _absence_to_dict(
    item: AbsenceFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    result: JsonObject = {
        "id": _feature_id(context, "absence", index),
        "scope": item.scope,
        "target": item.target,
        "anchor_ref": item.anchor_ref,
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }
    if item.expected_position is not None:
        result["expected_position"] = item.expected_position
    return result


def _contrastive_to_dict(
    item: ContrastiveSupportFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    return {
        "id": _feature_id(context, "contrastive_support", index),
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
        "sentence_kind": item.sentence_kind,
        "clause_count": item.clause_count,
        "polarity": item.polarity,
        "has_subject_aux_inversion": item.has_subject_aux_inversion,
        "has_do_support": item.has_do_support,
        "has_wh_fronting": item.has_wh_fronting,
        "has_tag_question": item.has_tag_question,
        "has_exclamation_marker": item.has_exclamation_marker,
        "provenance": _synthetic_provenance_from_refs(
            item.evidence_refs,
            "surface",
            item.sentence_type_confidence,
        ),
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


def _diagnostic_to_dict(item: FeatureDiagnostic) -> JsonObject | None:
    normalized = _normalized_diagnostic(item)
    if normalized is None:
        return None
    result: JsonObject = {
        "severity": normalized.severity,
        "code": normalized.code,
        "message": normalized.message,
        "refs": list(normalized.refs),
    }
    if normalized.feature_path is not None:
        result["feature_path"] = normalized.feature_path
    return result


def _normalized_diagnostic(item: FeatureDiagnostic) -> FeatureDiagnostic | None:
    feature_path_map = {
        "evidence": "features.evidence.words[*].ref",
        "syntax.predicates": "features.syntax.predicates[*].tavm.form_signature",
        "syntax.clauses": "features.syntax.clauses[*].type",
        "syntax.np_profiles.article_slot": (
            "features.syntax.np_profiles[*].article_slot.requiredness"
        ),
    }
    diagnostic_map: dict[str, tuple[str | None, str | None]] = {
        "malformed_feats": (
            "malformed_morphology_feats",
            "features.morphology.normalized[*].is_finite_verb",
        ),
        "evidence_omitted_by_config": (
            "disabled_feature_group",
            "features.evidence.words[*].ref",
        ),
        "unknown_predicate_type": (
            "predicate_type_unknown",
            "features.syntax.predicates[*].tavm.form_signature",
        ),
        "fragment_non_predicative_root": (
            "non_predicative_fragment",
            "features.lexical.sentence.sentence_type",
        ),
        "quoted_speech_fragment": (
            "quoted_speech_fragment",
            "features.lexical.sentence.sentence_type",
        ),
        "address_or_date_fragment": (
            "address_or_date_fragment",
            "features.lexical.sentence.sentence_type",
        ),
        "heading_fragment": (
            "heading_fragment",
            "features.lexical.sentence.sentence_type",
        ),
        "possible_parser_error": (
            "parser_degraded_predicate",
            "features.syntax.predicates[*].tavm.form_signature",
        ),
        "article_slot_not_applicable": (None, None),
    }
    mapped_code, mapped_path = diagnostic_map.get(
        item.code,
        (item.code, feature_path_map.get(item.feature_path or "")),
    )
    if mapped_code is None:
        return None
    return FeatureDiagnostic(
        severity=item.severity,
        code=mapped_code,
        message=item.message,
        refs=item.refs,
        feature_path=mapped_path or feature_path_map.get(item.feature_path or ""),
    )


def ensure_json_object(value: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
    return value


def _coerce_json_object(value: Mapping[str, object]) -> JsonObject:
    return cast(JsonObject, value)


def _make_serialization_context(
    sentence: SentenceGrammarFeatures,
) -> SerializationContext:
    features = sentence.features
    return {
        "sentence_number": sentence.sentence_index,
        "clause_ids": {
            item.id: _feature_id_value(sentence.sentence_index, "clause", index)
            for index, item in enumerate(features.syntax.clauses, start=1)
        },
        "clause_ids_by_head": {
            item.head: _feature_id_value(sentence.sentence_index, "clause", index)
            for index, item in enumerate(features.syntax.clauses, start=1)
        },
        "np_ids": {
            item.id: _feature_id_value(sentence.sentence_index, "np", index)
            for index, item in enumerate(features.syntax.np_profiles, start=1)
        },
    }


def _feature_id(
    context: SerializationContext,
    group: str,
    index: int,
) -> str:
    sentence_number = cast(int, context["sentence_number"])
    counters = cast(dict[str, int], context.setdefault("_id_counters", {}))
    next_index = counters.get(group, 0) + 1
    counters[group] = next_index
    return _feature_id_value(sentence_number, group, next_index)


def _feature_id_value(sentence_number: int, group: str, index: int) -> str:
    return f"s{sentence_number}.{group}.{index}"


def _mapped_id(
    context: SerializationContext,
    map_name: str,
    key: str | int,
    default: str,
) -> str:
    mapping = cast(dict[str | int, str], context.get(map_name, {}))
    return mapping.get(key, default)


def _mapped_clause_ref(
    context: SerializationContext,
    raw_value: str,
) -> str:
    mapped = _mapped_id(context, "clause_ids", raw_value, raw_value)
    if mapped != raw_value:
        return mapped
    if raw_value.startswith("clause:"):
        try:
            head_ref = int(raw_value.split(":", 1)[1])
        except ValueError:
            return raw_value
        return _mapped_id(context, "clause_ids_by_head", head_ref, raw_value)
    return raw_value


def _synthetic_provenance(
    ref: int,
    source: str,
    confidence: str = "high",
) -> JsonObject:
    return _synthetic_provenance_from_refs((ref,), source, confidence)


def _synthetic_provenance_from_refs(
    refs: tuple[int, ...] | list[int],
    source: str,
    confidence: str,
) -> JsonObject:
    normalized_source = (
        source
        if source
        in {
            "word_order",
            "upos",
            "xpos",
            "morphology",
            "dependency",
            "surface",
            "lemma",
            "closed_list",
            "lexicon",
            "phonology",
            "task_context",
            "discourse_heuristic",
        }
        else "surface"
    )
    return {
        "tier": "deterministic",
        "source": normalized_source,
        "evidence_refs": _dedupe_int_refs(refs),
        "confidence": confidence,
    }


def _schema_morph_features(features: dict[str, str]) -> JsonObject:
    allowed = {
        "VerbForm",
        "Tense",
        "Number",
        "Person",
        "Degree",
        "PronType",
        "Definite",
        "Mood",
        "Voice",
        "Aspect",
        "Case",
        "Poss",
    }
    return {key: value for key, value in features.items() if key in allowed}


def _schema_voice(value: str) -> str:
    if value == "copular_not_applicable":
        return "unknown"
    return value


def _schema_modality(value: str) -> str:
    if value == "conditional":
        return "unknown"
    return value


def _schema_predicate_type(value: str) -> str:
    if value == "passive_verbal":
        return "verbal"
    return value


def _schema_coordination_type(value: str) -> str:
    if value == "clausal_or_phrasal":
        return "unknown"
    return value


def _schema_negator_kind(value: str) -> str:
    negator_map = {
        "nor": "neither",
        "nobody": "none",
        "nowhere": "other",
        "hardly": "other",
    }
    normalized = negator_map.get(value, value)
    allowed = {
        "not",
        "nt",
        "never",
        "no",
        "none",
        "nothing",
        "neither",
        "other",
    }
    return normalized if normalized in allowed else "other"


def _schema_construction_signature(value: str) -> str:
    signature_map = {
        "modal_negative_base": "modal_must_base",
        "present_simple_do_negative_question": "present_simple_do_question",
        "past_simple_negative": "past_simple_lexical_affirmative",
        "perfect_negative": "present_perfect_have_participle",
        "copular_be_negative": "subject_be_present_not_complement",
        "passive_negative": "passive_be_participle",
    }
    return signature_map.get(value, value)


def _dedupe_int_refs(refs: tuple[int, ...] | list[int]) -> list[int]:
    ordered: list[int] = []
    seen: set[int] = set()
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            ordered.append(ref)
    return ordered


def _schema_countability_source(value: str) -> str:
    if value in {"parser", "determiner_pattern"}:
        return "heuristic"
    return value


def _surface_text(evidence: EvidenceFeatures, ref: int) -> str:
    for word in evidence.words:
        if word.ref == ref:
            return word.text
    return ""


def _noun_inflection_to_dict(
    item: LexicalItemFeature,
    context: SerializationContext,
    index: int,
    evidence: EvidenceFeatures,
) -> JsonObject:
    ref = item.refs[0] if item.refs else 1
    token = next((word for word in evidence.words if word.ref == ref), None)
    number = (
        "plural"
        if "plural" in item.kind
        else "singular"
        if "singular" in item.kind
        else "unknown"
    )
    result: JsonObject = {
        "id": _feature_id(context, "noun_inflection", index),
        "ref": ref,
        "lemma": token.lemma if token is not None else item.text.casefold(),
        "surface": token.text if token is not None else item.text,
        "number": number,
        "provenance": _provenance_to_dict(item.provenance),
    }
    return result


def _time_marker_to_dict(
    item: LexicalItemFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    return {
        "id": _feature_id(context, "time_marker", index),
        "refs": _dedupe_int_refs(item.refs),
        "marker_kind": _schema_time_marker_kind(item.kind),
        "surface": item.text,
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }


def _comparison_to_dict(
    item: LexicalItemFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    return {
        "id": _feature_id(context, "comparison", index),
        "type": _schema_comparison_type(item.kind),
        "marker_refs": _dedupe_int_refs(item.refs),
        "semantic_relation": "unknown",
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }


def _phrasal_verb_to_dict(
    item: LexicalItemFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    refs = list(item.refs)
    return {
        "id": _feature_id(context, "phrasal_verb", index),
        "verb": refs[0] if refs else 1,
        "particle_ref": refs[1] if len(refs) > 1 else (refs[0] if refs else 1),
        "particle": item.text,
        "separability": "unknown",
        "lemma_signature": item.kind,
        "confidence": item.confidence,
        "sources": [_flat_source(item.provenance)],
        "provenance": _provenance_to_dict(item.provenance),
    }


def _discourse_marker_to_dict(
    item: LexicalItemFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    return {
        "id": _feature_id(context, "discourse_marker", index),
        "refs": _dedupe_int_refs(item.refs),
        "marker_kind": _schema_discourse_marker_kind(item.kind),
        "surface": item.text,
        "confidence": item.confidence,
        "provenance": _provenance_to_dict(item.provenance),
    }


def _schema_time_marker_kind(value: str) -> str:
    if value == "time_marker":
        return "other"
    return value


def _schema_comparison_type(value: str) -> str:
    comparison_map = {
        "comparison": "unknown",
        "comparison_as_as": "equality_as_as",
    }
    return comparison_map.get(value, value)


def _schema_discourse_marker_kind(value: str) -> str:
    if value == "discourse_marker":
        return "other"
    return value


def _contraction_to_dict(
    item: LexicalItemFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    ref = item.refs[0] if item.refs else 1
    return {
        "id": _feature_id(context, "contraction", index),
        "surface_ref": ref,
        "surface": item.text,
        "expansion": "unknown",
        "contraction_type": "unknown",
        "provenance": _provenance_to_dict(item.provenance),
    }


def _modifier_to_dict(item: ModifierFeature) -> JsonObject:
    return {"ref": item.ref, "modifier_type": item.modifier_type}


def _np_quantifier_to_dict(
    item: QuantifierFeature,
    context: SerializationContext,
    index: int,
) -> JsonObject:
    return {
        "id": _feature_id(context, "np_quantifier", index),
        "ref": item.ref,
        "text": item.text,
        "quantifier_type": "unknown",
        "provenance": _synthetic_provenance(item.ref, "surface"),
    }


def _find_coordinator_ref(
    item: Coordination,
    evidence: EvidenceFeatures,
) -> int | None:
    conjunct_set = set(item.conjuncts)
    for word in evidence.words:
        if word.deprel == "cc" and word.head in conjunct_set:
            return word.ref
    return None


_MATCHER_UNSAFE_REASONS = frozenset(
    {
        "unknown_predicate_type",
        "predicate_type_unknown",
        "form_signature_unknown",
        "possible_parser_error",
        "parser_degraded_predicate",
        "low_confidence_predicate_evidence",
        "registry_signature_missing",
    }
)

_MATCHER_SAFE_REASONS = frozenset(
    {
        "non_finite_clause_candidate",
        "non_predicative_fragment",
        "fragment_non_predicative_root",
        "quoted_speech_fragment",
        "heading_fragment",
        "address_or_date_fragment",
    }
)


def _reason_subgroup(feature_path: str | None) -> tuple[str, str | None]:
    if not feature_path:
        return "unknown", None
    path = feature_path
    parts = path.split(".")
    group = parts[0] if parts else "unknown"
    subgroup: str | None = None
    if len(parts) >= 2:
        # strip array indexing like [*] in `features.syntax.predicates[*].tavm.form_signature`
        cleaned = ".".join(part.split("[")[0] for part in parts[1:])
        subgroup = cleaned or None
    return group or "unknown", subgroup


def _output_completeness_from_sentences(
    sentences: tuple[SentenceGrammarFeatures, ...],
) -> JsonObject:
    degraded_codes = _MATCHER_UNSAFE_REASONS | _MATCHER_SAFE_REASONS
    evidence_omitted = any(
        any(
            diagnostic.code == "evidence_omitted_by_config"
            for diagnostic in sentence.features.diagnostics
        )
        for sentence in sentences
    )
    if not evidence_omitted and sentences:
        evidence_omitted = all(
            sentence.features.evidence.words == ()
            and sentence.features.morphology.word_morphology != ()
            for sentence in sentences
        )

    # Build structured omissions
    omissions_by_key: dict[
        tuple[str, str | None, str], dict[str, object]
    ] = {}
    for sentence in sentences:
        for diagnostic in sentence.features.diagnostics:
            if diagnostic.code not in degraded_codes:
                continue
            group_value = "features"
            subgroup_value = None
            reason = diagnostic.code
            scope = "sentence"
            if diagnostic.feature_path:
                group_value, subgroup_value = _reason_subgroup(
                    diagnostic.feature_path
                )
                # feature_path is `features.X.Y` — peel "features." prefix
                if group_value == "features" and subgroup_value:
                    head, _, rest = subgroup_value.partition(".")
                    group_value = head
                    subgroup_value = rest or None
            matcher_safe = reason in _MATCHER_SAFE_REASONS
            key = (group_value, subgroup_value, reason)
            bucket = omissions_by_key.setdefault(
                key,
                {
                    "group": group_value,
                    "subgroup": subgroup_value,
                    "reason": reason,
                    "scope": scope,
                    "matcher_safe": matcher_safe,
                    "affected_sentence_count": 0,
                    "affected_sentence_indexes_sample": [],
                },
            )
            bucket["affected_sentence_count"] = (
                int(bucket["affected_sentence_count"]) + 1
            )
            samples = bucket["affected_sentence_indexes_sample"]
            assert isinstance(samples, list)
            if len(samples) < 10 and sentence.sentence_index not in samples:
                samples.append(sentence.sentence_index)

    omissions: list[JsonValue] = []
    if evidence_omitted:
        omissions.append(
            {
                "group": "evidence",
                "subgroup": None,
                "reason": "evidence_omitted_by_config",
                "scope": "page",
                "matcher_safe": False,
                "affected_sentence_count": len(sentences),
                "affected_sentence_indexes_sample": [
                    sentence.sentence_index
                    for sentence in sentences[:10]
                ],
            }
        )
    for key in sorted(omissions_by_key):
        omissions.append(omissions_by_key[key])

    has_unsafe = any(not bool(item["matcher_safe"]) for item in omissions)
    matcher_complete = not has_unsafe

    # Legacy `omitted_feature_groups` (deprecated)
    legacy_groups: list[JsonValue] = []
    if evidence_omitted:
        legacy_groups.append("evidence")
    for item in omissions:
        if item.get("group") in {"evidence"}:
            continue
        group_label = str(item.get("group", ""))
        if group_label and group_label not in legacy_groups:
            legacy_groups.append(group_label)

    return {
        "matcher_complete": matcher_complete,
        "omissions": omissions,
        "omitted_feature_groups": legacy_groups,
    }


def _degraded_omitted_groups(
    sentences: tuple[SentenceGrammarFeatures, ...],
    degraded_codes: set[str],
) -> list[JsonValue]:
    groups: list[JsonValue] = []
    for sentence in sentences:
        for diagnostic in sentence.features.diagnostics:
            if diagnostic.code not in degraded_codes:
                continue
            path = diagnostic.feature_path or ""
            if "syntax" in path and "syntax" not in groups:
                groups.append("syntax")
            if "construction" in path and "constructions" not in groups:
                groups.append("constructions")
            if "lexical" in path and "lexical" not in groups:
                groups.append("lexical")
    if not groups:
        groups.append("diagnostics")
    return groups
