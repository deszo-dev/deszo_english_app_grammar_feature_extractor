from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    AbsenceFeature,
    CandidateFeature,
    ConstructionFamilySummary,
    ConstructionFeature,
    CoverageEntry,
    DiscourseFeatures,
    FeatureCoverage,
    FeatureDiagnostic,
    FeatureDiagnosticItem,
    FeatureDiagnostics,
    FeatureGroupQuality,
    FeatureSupportItem,
    LexicalFeatures,
    LocalContext,
    NegativeEvidence,
    NormalizationTrace,
    PatternWindow,
    ProcessingSupport,
    RelativeClauseFeature,
    SyntaxFeatures,
)


def build_feature_diagnostics(
    relative_clauses: tuple[RelativeClauseFeature, ...],
    discourse: DiscourseFeatures,
) -> FeatureDiagnostics:
    low_confidence = [
        FeatureDiagnosticItem(
            layer=None,
            feature_path=f"syntax.relative_clauses[{index}].object_gap",
            reason="ambiguous_dependency_parse",
            confidence="low",
        )
        for index, clause in enumerate(relative_clauses)
        if clause.object_gap is None or clause.confidence == "low"
    ]
    missing = []
    if discourse.quote_segmentation_status == "unknown":
        missing.append(
            FeatureDiagnosticItem(
                layer="discourse.direct_speech_segments",
                feature_path=None,
                reason="no_sentence_local_quote_pair",
                severity="info",
            )
        )
    return FeatureDiagnostics(
        missing_expected_layers=tuple(missing),
        low_confidence_features=tuple(low_confidence),
        unsupported_features=(),
        feature_layer_warnings=(),
    )


def build_feature_support() -> dict[str, FeatureSupportItem]:
    return {
        "syntax.np_profiles": FeatureSupportItem(
            status="supported", source="parser_plus_rules", confidence="high"
        ),
        "syntax.predicates": FeatureSupportItem(
            status="supported", source="parser_plus_rules", confidence="high"
        ),
        "syntax.relative_clauses": FeatureSupportItem(
            status="heuristic",
            source="dependency_plus_surface_heuristic",
            confidence="medium",
        ),
        "lexical.multiword_cues": FeatureSupportItem(
            status="supported", source="exact_lemma_span", confidence="high"
        ),
        "time_expressions": FeatureSupportItem(
            status="partial", source="curated_lexical_time_list", confidence="medium"
        ),
        "discourse.direct_speech_segments": FeatureSupportItem(
            status="heuristic", source="quote_surface_heuristic", confidence="medium"
        ),
        "phonology.word_sound_classes": FeatureSupportItem(
            status="partial",
            source="exception_list_plus_spelling_heuristic",
            confidence="medium",
        ),
        "document_structure": FeatureSupportItem(
            status="not_supported_in_v4_scope", source=None, confidence="none"
        ),
    }


_CONSTRUCTION_FAMILY_BY_PREFIX: tuple[tuple[str, str], ...] = (
    ("tense_aspect_", "tense_aspect"),
    ("aspect_", "tense_aspect"),
    ("tense_", "tense_aspect"),
    ("passive_", "passive"),
    ("perfect_", "tense_aspect"),
    ("progressive_", "tense_aspect"),
    ("modal_", "modality"),
    ("conditional_", "conditional"),
    ("comparative_", "comparison"),
    ("superlative_", "comparison"),
    ("comparison_", "comparison"),
    ("article_", "article_np"),
    ("np_", "article_np"),
    ("zero_article_", "article_np"),
    ("reported_", "reported_speech"),
    ("direct_", "reported_speech"),
    ("relative_", "relative_clause"),
    ("interrogative_", "question"),
    ("question_", "question"),
    ("imperative_", "imperative"),
    ("existential_", "existential"),
    ("cleft_", "cleft"),
    ("coordination_", "coordination"),
    ("subordination_", "subordination"),
    ("negation_", "negation"),
    ("phrasal_verb_", "phrasal_verb"),
)


def _classify_construction_family(construction: ConstructionFeature) -> str | None:
    if construction.family_hint is not None and construction.family_hint != "predicate":
        return construction.family_hint
    if construction.type != "complement_pattern":
        return construction.type
    signature = construction.signature
    for prefix, family in _CONSTRUCTION_FAMILY_BY_PREFIX:
        if signature.startswith(prefix):
            return family
    return None


def _coverage_status(emitted: int, expected: int | None) -> tuple[str, tuple[str, ...]]:
    if expected is None and emitted == 0:
        return "not_applicable", ()
    if expected is None and emitted > 0:
        return "complete", ()
    assert expected is not None
    if expected == 0 and emitted == 0:
        return "not_applicable", ()
    if emitted >= expected and emitted > 0:
        return "complete", ()
    if emitted == 0:
        return "failed", ("no_features_emitted",)
    return "partial", ("expected_exceeds_emitted",)


def build_construction_family_summary(
    constructions: tuple[ConstructionFeature, ...],
) -> dict[str, ConstructionFamilySummary]:
    family_to_signatures: dict[str, list[str]] = {}
    for construction in constructions:
        family = _classify_construction_family(construction)
        if family is None:
            continue
        family_to_signatures.setdefault(family, []).append(construction.signature)
    return {
        family: ConstructionFamilySummary(
            count=len(family_to_signatures[family]),
            signatures=tuple(sorted(set(family_to_signatures[family]))),
            status="complete" if family_to_signatures[family] else "not_applicable",
            reason_codes=(),
        )
        for family in sorted(family_to_signatures)
    }


def _coverage_entry(emitted: int, expected: int | None = None) -> CoverageEntry:
    status, reason_codes = _coverage_status(emitted, expected)
    return CoverageEntry(
        status=status,
        expected=expected,
        emitted=emitted,
        families_attempted=(),
        families_omitted=(),
        reason_codes=reason_codes,
    )


def build_feature_coverage(
    syntax: SyntaxFeatures,
    lexical: LexicalFeatures,
    constructions: tuple[ConstructionFeature, ...],
    absences: tuple[AbsenceFeature, ...],
) -> FeatureCoverage:
    lexical_emitted = (
        len(lexical.contractions)
        + len(lexical.quantifiers)
        + len(lexical.verb_patterns)
        + len(lexical.adjective_patterns)
        + len(lexical.lexical_classes)
        + len(lexical.discourse_markers)
        + len(lexical.time_markers)
        + len(lexical.comparisons)
        + len(lexical.phrasal_verbs)
    )
    return FeatureCoverage(
        predicate_detection=_coverage_entry(len(syntax.predicates)),
        clause_detection=_coverage_entry(len(syntax.clauses)),
        np_detection=_coverage_entry(len(syntax.np_profiles)),
        construction_detection=_coverage_entry(len(constructions)),
        lexical_detection=_coverage_entry(lexical_emitted),
        absence_detection=_coverage_entry(len(absences)),
    )


def build_feature_group_quality(
    diagnostics: tuple[FeatureDiagnostic, ...],
) -> FeatureGroupQuality:
    has_error = any(d.severity == "error" for d in diagnostics)
    has_warning = any(d.severity == "warning" for d in diagnostics)
    codes = {d.code for d in diagnostics}
    overall = "high"
    mode = "normal"
    if codes & {"heading_fragment", "address_or_date_fragment", "non_predicative_fragment"}:
        overall = "medium"
        mode = "skip"
    elif codes & {"parser_degraded_predicate", "possible_parser_error"}:
        overall = "low"
        mode = "evidence_only"
    elif codes & {"predicate_type_unknown", "unknown_predicate_type", "quoted_speech_fragment"}:
        overall = "medium"
        mode = "cautious"
    elif has_error:
        overall = "low"
        mode = "cautious"
    elif has_warning:
        overall = "medium"
        mode = "cautious"
    reason_codes = tuple(sorted(codes))
    return FeatureGroupQuality(
        overall=overall,
        recommended_processing_mode=mode,
        reason_codes=reason_codes,
    )


_QUOTE_OPEN_CHARS = frozenset({'"', "“", "‘", "«"})
_QUOTE_CLOSE_CHARS = frozenset({'"', "”", "’", "»"})


def _quote_continuation_state(text: str) -> str:
    opens = sum(1 for ch in text if ch in _QUOTE_OPEN_CHARS)
    closes = sum(1 for ch in text if ch in _QUOTE_CLOSE_CHARS)
    if opens == 0 and closes == 0:
        return "outside"
    if opens > closes:
        return "inside_open_quote"
    if closes > 0 and opens == 0:
        return "closing_quote"
    return "outside"


def build_local_context(
    sentence_index: int,
    total_sentences: int,
    source_unit_order: int | None,
    source_unit_id: str | None = None,
    previous_source_unit_id: str | None = None,
    next_source_unit_id: str | None = None,
    sentence_text: str = "",
) -> LocalContext:
    previous_index = sentence_index - 1 if sentence_index > 0 else None
    next_index = sentence_index + 1 if sentence_index + 1 < total_sentences else None
    if total_sentences <= 1:
        paragraph_position = "single"
    elif sentence_index == 0:
        paragraph_position = "initial"
    elif sentence_index + 1 >= total_sentences:
        paragraph_position = "final"
    else:
        paragraph_position = "middle"
    return LocalContext(
        paragraph_position=paragraph_position,
        same_unit_previous_sentence_available=(
            previous_index is not None
            and source_unit_id is not None
            and previous_source_unit_id == source_unit_id
        ),
        same_unit_next_sentence_available=(
            next_index is not None
            and source_unit_id is not None
            and next_source_unit_id == source_unit_id
        ),
        quote_continuation_state=_quote_continuation_state(sentence_text),
        previous_sentence_index=previous_index,
        next_sentence_index=next_index,
    )


def build_processing_support(
    syntax: SyntaxFeatures,
    lexical: LexicalFeatures,
    constructions: tuple[ConstructionFeature, ...],
    absences: tuple[AbsenceFeature, ...],
    diagnostics: tuple[FeatureDiagnostic, ...],
    sentence_index: int,
    total_sentences: int,
    source_unit_order: int | None,
    source_unit_id: str | None = None,
    previous_source_unit_id: str | None = None,
    next_source_unit_id: str | None = None,
    sentence_text: str = "",
    candidate_features: tuple[CandidateFeature, ...] = (),
    normalization_trace: tuple[NormalizationTrace, ...] = (),
    feature_conflicts: tuple = (),
    negative_evidence: tuple[NegativeEvidence, ...] = (),
    pattern_windows: tuple[PatternWindow, ...] = (),
) -> ProcessingSupport:
    return ProcessingSupport(
        quality=build_feature_group_quality(diagnostics),
        coverage=build_feature_coverage(syntax, lexical, constructions, absences),
        candidate_features=candidate_features,
        normalization_trace=normalization_trace,
        construction_family_summary=build_construction_family_summary(constructions),
        feature_conflicts=feature_conflicts,
        negative_evidence=negative_evidence,
        pattern_windows=pattern_windows,
        local_context=build_local_context(
            sentence_index,
            total_sentences,
            source_unit_order,
            source_unit_id,
            previous_source_unit_id,
            next_source_unit_id,
            sentence_text,
        ),
    )


__all__ = [
    "build_construction_family_summary",
    "build_feature_coverage",
    "build_feature_diagnostics",
    "build_feature_group_quality",
    "build_feature_support",
    "build_local_context",
    "build_processing_support",
]
