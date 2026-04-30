from __future__ import annotations

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
]

DIAGNOSTIC_CODES: tuple[DiagnosticCode, ...] = (
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
)

DIAGNOSTIC_CODE_SET = frozenset(DIAGNOSTIC_CODES)
