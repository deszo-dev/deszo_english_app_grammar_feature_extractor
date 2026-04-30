from __future__ import annotations

from grammar_feature_extractor._internal.features.clause_builder import build_clauses
from grammar_feature_extractor._internal.features.complement_builder import (
    build_complements,
)
from grammar_feature_extractor._internal.features.coordination_builder import (
    build_coordination,
)
from grammar_feature_extractor._internal.features.phrase_builder import build_phrases
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
    Polarity,
    SentenceFeature,
    SentenceGrammarFeatures,
    SentenceKind,
    SentenceType,
    SyntaxFeatures,
)
from grammar_feature_extractor._internal.sentence_context import (
    SentenceContext,
    build_sentence_context,
)
from grammar_feature_extractor._internal.validation import validate_paging_config

WH_WORDS = frozenset(
    {"what", "who", "whom", "whose", "which", "when", "where", "why", "how"}
)


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

    return GrammarFeatureSet(
        evidence=evidence,
        morphology=_morphology_from_context(context),
        syntax=SyntaxFeatures(
            phrases=build_phrases(context),
            clauses=clauses,
            complements=build_complements(context),
            coordination=build_coordination(context),
            subordination=subordination,
        ),
        lexical=LexicalFeatures(sentence=_sentence_feature(sentence)),
        constructions=() if config.include_construction_signatures else (),
        contrastive_support=() if config.include_contrastive_support else (),
        absences=(),
        diagnostics=tuple(diagnostics) if config.include_diagnostics else (),
    )


def _morphology_from_context(context: SentenceContext) -> MorphologyFeatures:
    word_morphology = tuple(context.morph_by_ref[ref] for ref in context.refs)
    normalized = tuple(context.normalized_morph_by_ref[ref] for ref in context.refs)
    return MorphologyFeatures(word_morphology=word_morphology, normalized=normalized)


def _sentence_feature(sentence: AnnotatedSentence) -> SentenceFeature:
    lower_words = tuple(word.text.casefold() for word in sentence.words)
    has_negation = any(
        word.deprel == "neg" or word.text.casefold() in {"not", "n't"}
        for word in sentence.words
    )
    subject_positions = tuple(
        index
        for index, word in enumerate(sentence.words)
        if word.deprel in {"nsubj", "nsubj:pass"}
    )
    aux_positions = tuple(
        index for index, word in enumerate(sentence.words) if word.upos == "AUX"
    )
    has_subject_aux_inversion = bool(
        subject_positions
        and aux_positions
        and min(aux_positions) < min(subject_positions)
    )
    return SentenceFeature(
        sentence_kind=_sentence_kind(sentence),
        clause_count=sum(
            1
            for word in sentence.words
            if word.deprel in {"root", "ccomp", "xcomp", "advcl", "acl", "acl:relcl"}
        ),
        sentence_type=_sentence_type(sentence, has_subject_aux_inversion),
        polarity=_polarity(has_negation),
        has_subject_aux_inversion=has_subject_aux_inversion,
        has_do_support=any(
            word.upos == "AUX" and (word.lemma or word.text).casefold() == "do"
            for word in sentence.words
        ),
        has_wh_fronting=bool(lower_words and lower_words[0] in WH_WORDS),
        has_tag_question=False,
        has_exclamation_marker=sentence.text.rstrip().endswith("!"),
    )


def _sentence_kind(sentence: AnnotatedSentence) -> SentenceKind:
    text = sentence.text.strip()
    if text.startswith(('"', "'")) and text.endswith(('"', "'")):
        return "quote"
    if any(word.upos in {"VERB", "AUX"} for word in sentence.words):
        return "normal"
    if text.endswith("!"):
        return "exclamation_fragment"
    if len(sentence.words) <= 8:
        return "fragment"
    return "unknown"


def _sentence_type(
    sentence: AnnotatedSentence,
    has_subject_aux_inversion: bool,
) -> SentenceType:
    text = sentence.text.rstrip()
    lower_words = tuple(word.text.casefold() for word in sentence.words)
    if text.endswith("?"):
        if lower_words and lower_words[0] in WH_WORDS:
            return "wh_question"
        if has_subject_aux_inversion:
            return "yes_no_question"
        return "unknown"
    if text.endswith("!"):
        return "exclamative"
    if not any(word.upos in {"VERB", "AUX"} for word in sentence.words):
        return "fragment"
    return "declarative"


def _polarity(has_negation: bool) -> Polarity:
    return "negative" if has_negation else "positive"
