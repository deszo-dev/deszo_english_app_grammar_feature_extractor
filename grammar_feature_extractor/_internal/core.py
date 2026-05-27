from __future__ import annotations

from grammar_feature_extractor._internal.features.absence_builder import build_absences
from grammar_feature_extractor._internal.features.clause_builder import build_clauses
from grammar_feature_extractor._internal.features.complement_builder import (
    build_complements,
)
from grammar_feature_extractor._internal.features.conditional_builder import (
    build_conditionals,
)
from grammar_feature_extractor._internal.features.construction_builder import (
    build_constructions,
)
from grammar_feature_extractor._internal.features.contrastive_support_builder import (
    build_contrastive_support,
)
from grammar_feature_extractor._internal.features.coordination_builder import (
    build_coordination,
)
from grammar_feature_extractor._internal.features.diagnostics_builder import (
    add_baseline_diagnostics,
)
from grammar_feature_extractor._internal.features.discourse_builder import (
    build_discourse_segments,
)
from grammar_feature_extractor._internal.features.adjective_pattern_builder import (
    build_adjective_patterns,
)
from grammar_feature_extractor._internal.features.lexical_builder import (
    build_lexical_items,
    build_negation,
    build_sentence_feature,
    build_word_order,
)
from grammar_feature_extractor._internal.features.lexical_class_builder import (
    build_lexical_classes,
)
from grammar_feature_extractor._internal.features.quantifier_builder import (
    build_quantifiers,
)
from grammar_feature_extractor._internal.features.verb_pattern_builder import (
    build_verb_patterns,
)
from grammar_feature_extractor._internal.features.multiword_cue_builder import (
    build_multiword_cues,
)
from grammar_feature_extractor._internal.features.candidate_builder import (
    build_np_candidates,
    build_predicate_candidates,
)
from grammar_feature_extractor._internal.features.conflict_builder import (
    build_predicate_conflicts,
)
from grammar_feature_extractor._internal.features.negative_evidence_builder import (
    build_np_negative_evidence,
    build_predicate_negative_evidence,
)
from grammar_feature_extractor._internal.features.normalization_trace_builder import (
    build_predicate_normalization_traces,
)
from dataclasses import replace as _dc_replace

FRAGMENT_SOURCE_UNIT_ROLES = frozenset(
    {
        "heading",
        "chapter_heading",
        "section_heading",
        "title",
        "date",
        "address",
        "diary_label",
        "salutation",
        "signature",
        "label",
        "metadata",
    }
)
FRAGMENT_SOURCE_UNIT_TYPES = frozenset(
    {
        "heading",
        "title",
        "date_block",
        "address_block",
        "metadata_block",
        "label",
    }
)


def _is_non_predicative_unit(
    source_unit_type: str | None, source_unit_role: str | None
) -> bool:
    if source_unit_type and source_unit_type in FRAGMENT_SOURCE_UNIT_TYPES:
        return True
    if source_unit_role and source_unit_role in FRAGMENT_SOURCE_UNIT_ROLES:
        return True
    return False


def _convert_to_not_applicable(
    predicates: tuple,
) -> tuple:
    converted: list = []
    for predicate in predicates:
        if predicate.form_signature in ("unknown", None):
            new_tavm = _dc_replace(predicate.tavm, form_signature="not_applicable")
            converted.append(
                _dc_replace(
                    predicate,
                    form_signature="not_applicable",
                    tavm=new_tavm,
                )
            )
        else:
            converted.append(predicate)
    return tuple(converted)
from grammar_feature_extractor._internal.features.pattern_window_builder import (
    build_np_windows,
    build_predicate_windows,
)
from grammar_feature_extractor._internal.features.np_builder import build_np_profiles
from grammar_feature_extractor._internal.features.passive_builder import (
    build_participial_clauses,
    build_passive_features,
)
from grammar_feature_extractor._internal.features.phrase_builder import build_phrases
from grammar_feature_extractor._internal.features.predicate_builder import (
    build_predicates,
)
from grammar_feature_extractor._internal.features.pronoun_builder import build_pronouns
from grammar_feature_extractor._internal.features.relative_clause_builder import (
    build_relative_clauses,
)
from grammar_feature_extractor._internal.features.reported_speech_builder import (
    build_reported_speech_features,
)
from grammar_feature_extractor._internal.features.special_subject_builder import (
    build_special_subject_constructions,
)
from grammar_feature_extractor._internal.features.subordination_builder import (
    build_subordination,
)
from grammar_feature_extractor._internal.features.support_builder import (
    build_feature_diagnostics,
    build_feature_support,
    build_processing_support,
)
from grammar_feature_extractor._internal.features.time_builder import (
    attach_future_marking,
    build_time_expressions,
)
from grammar_feature_extractor._internal.models import (
    SCHEMA_VERSION,
    AnnotatedDocument,
    AnnotatedSentence,
    EvidenceFeatures,
    ExtractorConfig,
    FeatureDiagnostic,
    GrammarFeatureDocument,
    GrammarFeaturePage,
    GrammarFeatureSet,
    LexicalFeatures,
    MorphologyFeatures,
    PageInfo,
    PagingConfig,
    SentenceGrammarFeatures,
    SyntaxFeatures,
)
from grammar_feature_extractor._internal.sentence_context import (
    SentenceContext,
    build_sentence_context,
)
from grammar_feature_extractor._internal.validation import validate_paging_config


def extract_core(
    document: AnnotatedDocument,
    config: ExtractorConfig,
) -> GrammarFeatureDocument:
    total_sentences = len(document.sentences)
    sentences = tuple(
        SentenceGrammarFeatures(
            sentence_index=index,
            text=sentence.text,
            features=extract_sentence_features(
                index,
                sentence,
                config,
                total_sentences=total_sentences,
                source_unit_order=sentence.source_unit_order,
                source_unit_id=sentence.source_unit_id,
                previous_source_unit_id=(
                    document.sentences[index - 1].source_unit_id if index > 0 else None
                ),
                next_source_unit_id=(
                    document.sentences[index + 1].source_unit_id
                    if index + 1 < total_sentences
                    else None
                ),
                source_unit_type=sentence.source_unit_type,
                source_unit_role=sentence.source_unit_role,
            ),
            global_sentence_id=sentence.global_sentence_id,
            global_sentence_index=sentence.global_sentence_index,
            local_sentence_index=sentence.local_sentence_index,
            source_unit_id=sentence.source_unit_id,
            source_unit_order=sentence.source_unit_order,
            source_unit_type=sentence.source_unit_type,
            source_unit_role=sentence.source_unit_role,
            source_text_hash=sentence.source_text_hash,
        )
        for index, sentence in enumerate(document.sentences)
    )
    return GrammarFeatureDocument(
        schema_version=SCHEMA_VERSION,
        source_sentence_count=len(document.sentences),
        sentences=sentences,
        input_lineage=document.input_lineage,
    )


def paginate(
    document: GrammarFeatureDocument,
    paging: PagingConfig,
) -> GrammarFeaturePage:
    validate_paging_config(paging)
    total = document.source_sentence_count
    start = (paging.page_number - 1) * paging.page_size
    if start >= total:
        end = start
        features: tuple[SentenceGrammarFeatures, ...] = ()
    else:
        end = min(start + paging.page_size, total)
        features = document.sentences[start:end]
    has_next = end < total
    return GrammarFeaturePage(
        schema_version=SCHEMA_VERSION,
        page=PageInfo(
            page_number=paging.page_number,
            page_size=paging.page_size,
            total_sentences=total,
            sentence_start=start,
            sentence_end_exclusive=end,
            has_next_page=has_next,
            next_page=paging.page_number + 1 if has_next else None,
        ),
        features=features,
        input_lineage=document.input_lineage,
    )


def extract_sentence_features(
    sentence_index: int,
    sentence: AnnotatedSentence,
    config: ExtractorConfig,
    total_sentences: int | None = None,
    source_unit_order: int | None = None,
    source_unit_id: str | None = None,
    previous_source_unit_id: str | None = None,
    next_source_unit_id: str | None = None,
    source_unit_type: str | None = None,
    source_unit_role: str | None = None,
) -> GrammarFeatureSet:
    diagnostics: list[FeatureDiagnostic] = []
    context = build_sentence_context(sentence_index, sentence, diagnostics)
    evidence = (
        EvidenceFeatures(
            words=tuple(context.evidence_by_ref[ref] for ref in context.refs),
            dependencies=context.deps,
        )
        if config.include_evidence
        else EvidenceFeatures(words=(), dependencies=())
    )
    if not config.include_evidence and config.include_diagnostics:
        diagnostics.append(
            FeatureDiagnostic(
                severity="info",
                code="evidence_omitted_by_config",
                message=(
                    "Evidence layer was omitted from serialized output by "
                    "configuration."
                ),
                refs=(),
                feature_path="evidence",
            )
        )
    subordination = build_subordination(context)
    clauses = build_clauses(context, subordination, diagnostics)
    complements = build_complements(context)
    predicates = build_predicates(context, clauses, complements)
    if _is_non_predicative_unit(source_unit_type, source_unit_role):
        predicates = _convert_to_not_applicable(predicates)
        if config.include_diagnostics:
            for predicate in predicates:
                diagnostics.append(
                    FeatureDiagnostic(
                        severity="info",
                        code="non_predicative_fragment",
                        message=(
                            "Sentence belongs to a non-predicative source unit; "
                            "form_signature marked not_applicable."
                        ),
                        refs=(predicate.main,),
                        feature_path="features.syntax.predicates[*].tavm.form_signature",
                    )
                )
    np_profiles = build_np_profiles(context)
    multiword_cues = build_multiword_cues(context, predicates)
    time_expressions = build_time_expressions(context)
    predicates = attach_future_marking(predicates, multiword_cues, time_expressions)
    word_order = build_word_order(context, predicates)
    negation = build_negation(context, predicates)
    lexical_items = build_lexical_items(context)
    pronouns = build_pronouns(context)
    special_subjects = build_special_subject_constructions(context, predicates)
    relative_clauses = build_relative_clauses(context, clauses, np_profiles)
    conditionals = build_conditionals(context, clauses, predicates)
    reported_speech = build_reported_speech_features(context, predicates, clauses)
    passive = build_passive_features(context, predicates)
    participial_clauses = build_participial_clauses(context, np_profiles)
    discourse = build_discourse_segments(context, predicates, np_profiles)
    constructions = (
        build_constructions(predicates, np_profiles, word_order)
        if config.include_construction_signatures
        else ()
    )
    contrastive_support = (
        build_contrastive_support(constructions)
        if config.include_contrastive_support
        else ()
    )
    absences = build_absences(predicates, np_profiles)
    if config.include_diagnostics:
        add_baseline_diagnostics(context, predicates, np_profiles, diagnostics)

    final_diagnostics = tuple(diagnostics) if config.include_diagnostics else ()
    syntax_features = SyntaxFeatures(
        phrases=build_phrases(context),
        clauses=clauses,
        predicates=predicates,
        complements=complements,
        coordination=build_coordination(context),
        subordination=subordination,
        np_profiles=np_profiles,
        pronouns=pronouns,
        special_subject_constructions=special_subjects,
        relative_clauses=relative_clauses,
        participial_clauses=participial_clauses,
        conditionals=conditionals,
        reported_speech=reported_speech,
        passive=passive,
    )
    lexical_features = LexicalFeatures(
        sentence=build_sentence_feature(context, clauses, predicates),
        word_order=word_order,
        negation=negation,
        time_markers=lexical_items["time_markers"],
        lexical_classes=build_lexical_classes(context),
        verb_patterns=build_verb_patterns(context, predicates),
        adjective_patterns=build_adjective_patterns(context),
        comparisons=lexical_items["comparisons"],
        quantifiers=build_quantifiers(context),
        phrasal_verbs=lexical_items["phrasal_verbs"],
        discourse_markers=lexical_items["discourse_markers"],
        contractions=lexical_items["contractions"],
        noun_inflections=lexical_items["noun_inflections"],
        multiword_cues=multiword_cues,
    )
    normalization_traces = build_predicate_normalization_traces(predicates)
    candidate_features = build_predicate_candidates(
        predicates, sentence_index
    ) + build_np_candidates(np_profiles, sentence_index)
    feature_conflicts = build_predicate_conflicts(predicates, passive, sentence_index)
    negative_evidence = (
        build_predicate_negative_evidence(context, predicates)
        + build_np_negative_evidence(context, np_profiles)
    )
    pattern_windows = (
        build_predicate_windows(context, predicates)
        + build_np_windows(context, np_profiles)
    )
    processing_support = build_processing_support(
        syntax=syntax_features,
        lexical=lexical_features,
        constructions=constructions,
        absences=absences,
        diagnostics=final_diagnostics,
        sentence_index=sentence_index,
        total_sentences=total_sentences if total_sentences is not None else sentence_index + 1,
        source_unit_order=source_unit_order,
        source_unit_id=source_unit_id,
        previous_source_unit_id=previous_source_unit_id,
        next_source_unit_id=next_source_unit_id,
        sentence_text=sentence.text,
        candidate_features=candidate_features,
        normalization_trace=normalization_traces,
        feature_conflicts=feature_conflicts,
        negative_evidence=negative_evidence,
        pattern_windows=pattern_windows,
    )

    return GrammarFeatureSet(
        evidence=evidence,
        morphology=_morphology_from_context(context),
        syntax=syntax_features,
        lexical=lexical_features,
        time_expressions=time_expressions,
        discourse=discourse,
        constructions=constructions,
        contrastive_support=contrastive_support,
        absences=absences,
        diagnostics=final_diagnostics,
        feature_diagnostics=build_feature_diagnostics(relative_clauses, discourse),
        feature_support=build_feature_support(),
        processing_support=processing_support,
    )


def _morphology_from_context(context: SentenceContext) -> MorphologyFeatures:
    word_morphology = tuple(context.morph_by_ref[ref] for ref in context.refs)
    normalized = tuple(context.normalized_morph_by_ref[ref] for ref in context.refs)
    return MorphologyFeatures(word_morphology=word_morphology, normalized=normalized)
