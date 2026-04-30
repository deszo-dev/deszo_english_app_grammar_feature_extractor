from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    AbsenceFeature,
    NPFeature,
    PredicateFeature,
)
from grammar_feature_extractor._internal.proof_surface import make_provenance


def build_absences(
    predicates: tuple[PredicateFeature, ...],
    np_profiles: tuple[NPFeature, ...],
) -> tuple[AbsenceFeature, ...]:
    items: list[AbsenceFeature] = []
    for np in np_profiles:
        if np.article_slot.requiredness == "zero_article":
            items.append(
                AbsenceFeature(
                    scope="np",
                    target="article",
                    expected_position="before_head",
                    anchor_ref=np.head,
                    confidence="medium",
                    provenance=make_provenance(
                        "deterministic", "dependency", (np.head,), "medium"
                    ),
                )
            )
        elif np.article_slot.requiredness == "missing_required_determiner_candidate":
            items.append(
                AbsenceFeature(
                    scope="np",
                    target="determiner",
                    expected_position="before_head",
                    anchor_ref=np.head,
                    confidence="low",
                    provenance=make_provenance(
                        "heuristic", "dependency", (np.head,), "low"
                    ),
                )
            )
    for predicate in predicates:
        if (
            predicate.subject is None
            and predicate.predicate_type == "verbal"
            and predicate.finite
            and predicate.main == min(predicate.evidence_refs)
        ):
            items.append(
                AbsenceFeature(
                    scope="clause",
                    target="subject",
                    expected_position="before_clause",
                    anchor_ref=predicate.main,
                    confidence="low",
                    provenance=make_provenance(
                        "heuristic", "dependency", (predicate.main,), "low"
                    ),
                )
            )
        if (
            not predicate.auxiliaries
            and predicate.form_signature == "present_simple_lexical"
        ):
            items.append(
                AbsenceFeature(
                    scope="predicate",
                    target="auxiliary",
                    expected_position="after_aux",
                    anchor_ref=predicate.main,
                    confidence="medium",
                    provenance=make_provenance(
                        "deterministic", "dependency", (predicate.main,), "medium"
                    ),
                )
            )
    return tuple(items)
