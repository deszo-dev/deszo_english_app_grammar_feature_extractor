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
    "non_finite_clause_candidate",
    "partial_upstream_input",
    "registry_signature_missing",
    "malformed_morphology_feats",
    "disabled_feature_group",
    "vbg_with_be_aux_marked_unknown",
    "vbg_with_be_aux_marked_past_simple",
    "have_been_vbn_marked_perfect_progressive",
    "modal_be_vbg_collapsed_to_modal_base",
    "copula_vbg_false_positive",
    "progressive_chain_unregistered",
    "aspect_voice_chain_conflict",
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
    "non_finite_clause_candidate": DiagnosticSpec(
        code="non_finite_clause_candidate",
        severity="info",
        result_impact="feature_omitted",
        refs_required=True,
        feature_path_required=True,
    ),
    "partial_upstream_input": DiagnosticSpec(
        code="partial_upstream_input",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=False,
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
    "vbg_with_be_aux_marked_unknown": DiagnosticSpec(
        code="vbg_with_be_aux_marked_unknown",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "vbg_with_be_aux_marked_past_simple": DiagnosticSpec(
        code="vbg_with_be_aux_marked_past_simple",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "have_been_vbn_marked_perfect_progressive": DiagnosticSpec(
        code="have_been_vbn_marked_perfect_progressive",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "modal_be_vbg_collapsed_to_modal_base": DiagnosticSpec(
        code="modal_be_vbg_collapsed_to_modal_base",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "copula_vbg_false_positive": DiagnosticSpec(
        code="copula_vbg_false_positive",
        severity="info",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "progressive_chain_unregistered": DiagnosticSpec(
        code="progressive_chain_unregistered",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
    "aspect_voice_chain_conflict": DiagnosticSpec(
        code="aspect_voice_chain_conflict",
        severity="warning",
        result_impact="confidence_lowered",
        refs_required=True,
        feature_path_required=True,
    ),
}

DIAGNOSTIC_CODES: tuple[DiagnosticCode, ...] = tuple(DIAGNOSTIC_REGISTRY)  # type: ignore[arg-type]

DIAGNOSTIC_CODE_SET = frozenset(DIAGNOSTIC_CODES)
