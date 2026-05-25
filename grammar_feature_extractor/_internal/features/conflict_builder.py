from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    FeatureConflict,
    PassiveFeature,
    PredicateFeature,
)


def build_predicate_conflicts(
    predicates: tuple[PredicateFeature, ...],
    passive: tuple[PassiveFeature, ...],
    sentence_index: int,
) -> tuple[FeatureConflict, ...]:
    conflicts: list[FeatureConflict] = []
    passive_predicates = {
        item.predicate for item in passive if getattr(item, "predicate", None) is not None
    }
    for index, predicate in enumerate(predicates):
        if predicate.voice == "passive" and predicate.main not in passive_predicates:
            conflicts.append(
                FeatureConflict(
                    conflict_id=f"s{sentence_index}.conflict.passive.{index}",
                    type="surface_vs_dependency",
                    feature_paths=(
                        "features.syntax.predicates[*].voice",
                        "features.syntax.passive",
                    ),
                    evidence_refs=tuple(predicate.evidence_refs),
                    resolution="downgrade_confidence",
                    winner="dependency",
                    confidence_after_resolution="medium",
                )
            )
    return tuple(conflicts)


__all__ = ["build_predicate_conflicts"]
