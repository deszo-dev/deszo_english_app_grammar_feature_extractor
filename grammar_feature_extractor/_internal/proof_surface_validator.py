from __future__ import annotations

from collections.abc import Iterable

from grammar_feature_extractor._internal.models import (
    AnnotatedSentence,
    ClauseFeature,
    ConstructionFeature,
    GrammarFeatureSet,
    NPFeature,
    PredicateFeature,
    ProofProvenance,
    WordRef,
)

PREDICATE_TYPES = frozenset(
    {
        "verbal",
        "copular_adjectival",
        "copular_nominal",
        "copular_prepositional",
        "existential_there",
        "unknown",
    }
)


def validate_proof_surface(
    sentence: AnnotatedSentence,
    features: GrammarFeatureSet,
) -> None:
    max_ref = len(sentence.words)
    _validate_unique_ids(
        "syntax.predicates", (item.id for item in features.syntax.predicates)
    )
    _validate_unique_ids(
        "syntax.clauses", (item.id for item in features.syntax.clauses)
    )
    _validate_unique_ids(
        "syntax.np_profiles", (item.id for item in features.syntax.np_profiles)
    )
    _validate_unique_ids("constructions", (item.key for item in features.constructions))

    for clause in features.syntax.clauses:
        _validate_clause(max_ref, clause)
    for predicate in features.syntax.predicates:
        _validate_predicate(max_ref, predicate)
    for complement in features.syntax.complements:
        _validate_provenance(max_ref, complement.provenance)
    for marker in features.syntax.subordination:
        _validate_provenance(max_ref, marker.provenance)
    for np in features.syntax.np_profiles:
        _validate_np(max_ref, np)
    for construction in features.constructions:
        _validate_construction(max_ref, construction)
    for absence in features.absences:
        _check_ref(max_ref, absence.anchor_ref)
        _validate_provenance(max_ref, absence.provenance)
    for contrastive in features.contrastive_support:
        _validate_provenance(max_ref, contrastive.provenance)


def _validate_clause(max_ref: int, clause: ClauseFeature) -> None:
    _check_ref(max_ref, clause.head)
    _validate_provenance(max_ref, clause.provenance)


def _validate_predicate(max_ref: int, predicate: PredicateFeature) -> None:
    if predicate.predicate_type not in PREDICATE_TYPES:
        raise AssertionError(f"Unknown predicate_type: {predicate.predicate_type}.")
    _check_ref(max_ref, predicate.main)
    _validate_provenance(max_ref, predicate.provenance)
    for ref in predicate.evidence_refs:
        _check_ref(max_ref, ref)


def _validate_np(max_ref: int, np: NPFeature) -> None:
    _check_ref(max_ref, np.head)
    _validate_provenance(max_ref, np.provenance)
    _validate_provenance(max_ref, np.article_slot.provenance)
    if np.determiner is not None:
        _validate_provenance(max_ref, np.determiner.provenance)


def _validate_construction(max_ref: int, construction: ConstructionFeature) -> None:
    if not construction.evidence_refs:
        raise AssertionError(
            f"Construction {construction.key} has empty evidence_refs."
        )
    _validate_provenance(max_ref, construction.provenance)
    for ref in construction.evidence_refs:
        _check_ref(max_ref, ref)


def _validate_provenance(max_ref: int, provenance: ProofProvenance) -> None:
    if provenance.evidence_refs != tuple(
        sorted(dict.fromkeys(provenance.evidence_refs))
    ):
        raise AssertionError("ProofProvenance evidence_refs must be sorted and unique.")
    if not provenance.evidence_refs:
        raise AssertionError("ProofProvenance evidence_refs must be non-empty.")
    for ref in provenance.evidence_refs:
        _check_ref(max_ref, ref)


def _validate_unique_ids(group: str, ids: Iterable[str]) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            raise AssertionError(f"Duplicate feature id in {group}: {item_id}.")
        seen.add(item_id)


def _check_ref(max_ref: int, ref: WordRef) -> None:
    if ref < 1 or ref > max_ref:
        raise AssertionError(f"Invalid WordRef {ref}; expected 1..{max_ref}.")
