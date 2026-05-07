from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    DiscourseFeatures,
    FeatureDiagnosticItem,
    FeatureDiagnostics,
    FeatureSupportItem,
    RelativeClauseFeature,
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


__all__ = ["build_feature_diagnostics", "build_feature_support"]
