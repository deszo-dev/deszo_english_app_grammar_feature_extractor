from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    CandidateFeature,
    PredicateFeature,
)


def build_predicate_candidates(
    predicates: tuple[PredicateFeature, ...],
    sentence_index: int,
) -> tuple[CandidateFeature, ...]:
    candidates: list[CandidateFeature] = []
    for index, predicate in enumerate(predicates):
        signature = predicate.form_signature or "unknown"
        if signature in {"unknown", "not_applicable"}:
            decision = "ambiguous" if signature == "unknown" else "omitted"
            non_finite = (
                predicate.finite is False and predicate.main_upos in {"VERB", "AUX"}
            )
            if signature == "not_applicable":
                reason = "predicate_not_applicable_to_fragment"
            elif non_finite:
                reason = "non_finite_clause_candidate"
            else:
                reason = "form_signature_not_registered_for_combination"
            candidates.append(
                CandidateFeature(
                    candidate_id=f"s{sentence_index}.predicate.{index}",
                    group="predicate",
                    decision=decision,
                    reason=reason,
                    evidence_refs=tuple(predicate.evidence_refs),
                    confidence=predicate.confidence or "low",
                    candidate_type=predicate.predicate_type,
                    signature=signature,
                )
            )
        elif predicate.confidence == "low":
            candidates.append(
                CandidateFeature(
                    candidate_id=f"s{sentence_index}.predicate.{index}",
                    group="predicate",
                    decision="emitted",
                    reason="low_confidence_predicate_evidence",
                    evidence_refs=tuple(predicate.evidence_refs),
                    confidence="low",
                    candidate_type=predicate.predicate_type,
                    signature=signature,
                )
            )
    return tuple(candidates)


__all__ = ["build_predicate_candidates"]
