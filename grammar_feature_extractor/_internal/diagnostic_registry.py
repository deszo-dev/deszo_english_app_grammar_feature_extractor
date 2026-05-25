from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

DiagnosticCode: TypeAlias = Literal[
    "malformed_feats",
    "evidence_omitted_by_config",
    "dependency_cycle",
    "fragment_non_predicative_root",
    "unknown_predicate_type",
    "quoted_speech_fragment",
    "address_or_date_fragment",
    "heading_fragment",
    "negation_not_propagated",
    "ambiguous_negation_scope",
    "article_slot_not_applicable",
    "requires_phonology",
    "requires_countability_lexicon",
    "requires_discourse_context",
    "possible_parser_error",
    "invalid_optional_slot_ref",
    "predicate_type_unknown",
    "form_signature_unknown",
    "low_confidence_predicate_evidence",
    "non_predicative_fragment",
    "parser_degraded_predicate",
    "registry_signature_missing",
    "malformed_morphology_feats",
    "disabled_feature_group",
]

DiagnosticSeverity: TypeAlias = Literal["info", "warning", "error"]

DiagnosticResultImpact: TypeAlias = Literal[
    "none",
    "confidence_lowered",
    "feature_omitted",
    "feature_group_omitted",
]


@dataclass(frozen=True, slots=True)
class DiagnosticSpec:
    code: DiagnosticCode
    severity: DiagnosticSeverity
    result_impact: DiagnosticResultImpact
    refs_required: bool
    feature_path_required: bool


DIAGNOSTIC_REGISTRY: dict[str, DiagnosticSpec] = {
    "malformed_feats": DiagnosticSpec(
        code="malformed_feats",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "malformed_morphology_feats": DiagnosticSpec(
        code="malformed_morphology_feats",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "evidence_omitted_by_config": DiagnosticSpec(
        code="evidence_omitted_by_config",
        severity="info",
        result_impact="feature_group_omitted",
        refs_required=False,
        feature_path_required=True,
    ),
    "disabled_feature_group": DiagnosticSpec(
        code="disabled_feature_group",
        severity="info",
        result_impact="feature_group_omitted",
        refs_required=False,
        feature_path_required=True,
    ),
    "dependency_cycle": DiagnosticSpec(
        code="dependency_cycle",
        severity="error",
        result_impact="feature_group_omitted",
        refs_required=True,
        feature_path_required=False,
    ),
    "fragment_non_predicative_root": DiagnosticSpec(
        code="fragment_non_predicative_root",
        severity="info",
        result_impact="feature_omitted",
        refs_required=True,
        feature_path_required=True,
    ),
    "non_predicative_fragment": DiagnosticSpec(
        code="non_predicative_fragment",
        severity="info",
        result_impact="feature_omitted",
        refs_required=True,
        feature_path_required=True,
    ),
    "quoted_speech_fragment": DiagnosticSpec(
        code="quoted_speech_fragment",
        severity="info",
        result_impact="feature_omitted",
        refs_required=True,
        feature_path_required=True,
    ),
    "address_or_date_fragment": DiagnosticSpec(
        code="address_or_date_fragment",
        severity="info",
        result_impact="feature_omitted",
        refs_required=True,
        feature_path_required=True,
    ),
    "heading_fragment": DiagnosticSpec(
        code="heading_fragment",
        severity="info",
        result_impact="feature_omitted",
        refs_required=True,
        feature_path_required=True,
    ),
    "unknown_predicate_type": DiagnosticSpec(
        code="unknown_predicate_type",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "predicate_type_unknown": DiagnosticSpec(
        code="predicate_type_unknown",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "form_signature_unknown": DiagnosticSpec(
        code="form_signature_unknown",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "low_confidence_predicate_evidence": DiagnosticSpec(
        code="low_confidence_predicate_evidence",
        severity="info",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "parser_degraded_predicate": DiagnosticSpec(
        code="parser_degraded_predicate",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "registry_signature_missing": DiagnosticSpec(
        code="registry_signature_missing",
        severity="warning",
        result_impact="feature_omitted",
        refs_required=True,
        feature_path_required=True,
    ),
    "negation_not_propagated": DiagnosticSpec(
        code="negation_not_propagated",
        severity="info",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "ambiguous_negation_scope": DiagnosticSpec(
        code="ambiguous_negation_scope",
        severity="info",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "article_slot_not_applicable": DiagnosticSpec(
        code="article_slot_not_applicable",
        severity="info",
        result_impact="none",
        refs_required=True,
        feature_path_required=True,
    ),
    "requires_phonology": DiagnosticSpec(
        code="requires_phonology",
        severity="info",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "requires_countability_lexicon": DiagnosticSpec(
        code="requires_countability_lexicon",
        severity="info",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "requires_discourse_context": DiagnosticSpec(
        code="requires_discourse_context",
        severity="info",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "possible_parser_error": DiagnosticSpec(
        code="possible_parser_error",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "invalid_optional_slot_ref": DiagnosticSpec(
        code="invalid_optional_slot_ref",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
}

DIAGNOSTIC_CODES: tuple[DiagnosticCode, ...] = tuple(DIAGNOSTIC_REGISTRY)  # type: ignore[arg-type]

DIAGNOSTIC_CODE_SET = frozenset(DIAGNOSTIC_CODES)
