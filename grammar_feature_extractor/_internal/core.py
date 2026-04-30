from __future__ import annotations

from grammar_feature_extractor._internal.features.absence_builder import build_absences
from grammar_feature_extractor._internal.features.clause_builder import build_clauses
from grammar_feature_extractor._internal.features.complement_builder import (
    build_complements,
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
from grammar_feature_extractor._internal.features.lexical_builder import (
    build_lexical_items,
    build_negation,
    build_sentence_feature,
    build_word_order,
)
from grammar_feature_extractor._internal.features.np_builder import build_np_profiles
from grammar_feature_extractor._internal.features.phrase_builder import build_phrases
from grammar_feature_extractor._internal.features.predicate_builder import (
    build_predicates,
)
from grammar_feature_extractor._internal.features.subordination_builder import (
    build_subordination,
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
    sentences = tuple(
        SentenceGrammarFeatures(
            sentence_index=index,
            text=sentence.text,
            features=extract_sentence_features(index, sentence, config),
        )
        for index, sentence in enumerate(document.sentences)
    )
    return GrammarFeatureDocument(
        schema_version=SCHEMA_VERSION,
        source_sentence_count=len(document.sentences),
        sentences=sentences,
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
    )


def extract_sentence_features(
    sentence_index: int,
    sentence: AnnotatedSentence,
    config: ExtractorConfig,
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
    np_profiles = build_np_profiles(context)
    word_order = build_word_order(context, predicates)
    negation = build_negation(context, predicates)
    lexical_items = build_lexical_items(context)
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

    return GrammarFeatureSet(
        evidence=evidence,
        morphology=_morphology_from_context(context),
        syntax=SyntaxFeatures(
            phrases=build_phrases(context),
            clauses=clauses,
            predicates=predicates,
            complements=complements,
            coordination=build_coordination(context),
            subordination=subordination,
            np_profiles=np_profiles,
        ),
        lexical=LexicalFeatures(
            sentence=build_sentence_feature(context, clauses, predicates),
            word_order=word_order,
            negation=negation,
            time_markers=lexical_items["time_markers"],
            comparisons=lexical_items["comparisons"],
            phrasal_verbs=lexical_items["phrasal_verbs"],
            discourse_markers=lexical_items["discourse_markers"],
            contractions=lexical_items["contractions"],
            noun_inflections=lexical_items["noun_inflections"],
        ),
        constructions=constructions,
        contrastive_support=contrastive_support,
        absences=absences,
        diagnostics=tuple(diagnostics) if config.include_diagnostics else (),
    )


def _morphology_from_context(context: SentenceContext) -> MorphologyFeatures:
    word_morphology = tuple(context.morph_by_ref[ref] for ref in context.refs)
    normalized = tuple(context.normalized_morph_by_ref[ref] for ref in context.refs)
    return MorphologyFeatures(word_morphology=word_morphology, normalized=normalized)
