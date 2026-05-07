from __future__ import annotations

from collections.abc import Iterable

from grammar_feature_extractor._internal.construction_registry import (
    REGISTERED_CONSTRUCTION_SIGNATURES,
)
from grammar_feature_extractor._internal.diagnostic_registry import DIAGNOSTIC_CODE_SET
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
REGISTERED_CONSTRUCTION_SIGNATURE_SET = frozenset(REGISTERED_CONSTRUCTION_SIGNATURES)


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
    for pronoun in features.syntax.pronouns:
        _check_ref(max_ref, pronoun.ref)
    for special in features.syntax.special_subject_constructions:
        _check_ref(max_ref, special.subject_ref)
        _check_ref(max_ref, special.predicate_ref)
        if special.notional_subject is not None:
            _check_ref(max_ref, special.notional_subject)
        if special.agreement_controller is not None:
            _check_ref(max_ref, special.agreement_controller)
        for ref in special.evidence_refs:
            _check_ref(max_ref, ref)
    for relcl in features.syntax.relative_clauses:
        _check_ref(max_ref, relcl.head_noun)
        if relcl.relative_marker is not None:
            _check_ref(max_ref, relcl.relative_marker)
    for cond in features.syntax.conditionals:
        if cond.if_marker_ref is not None:
            _check_ref(max_ref, cond.if_marker_ref)
    for report in features.syntax.reported_speech:
        _check_ref(max_ref, report.reporting_verb)
        _check_ref(max_ref, report.reported_clause_head)
        if report.marker is not None:
            _check_ref(max_ref, report.marker)
        for ref in report.speaker_or_addressee_refs:
            _check_ref(max_ref, ref)
    for passive in features.syntax.passive:
        _check_ref(max_ref, passive.predicate)
        _check_ref(max_ref, passive.participle_ref)
        for ref in passive.aux_refs:
            _check_ref(max_ref, ref)
        for ref in passive.agent_by_phrase:
            _check_ref(max_ref, ref)
        if passive.patient_subject is not None:
            _check_ref(max_ref, passive.patient_subject)
    for diagnostic in features.diagnostics:
        if diagnostic.code not in DIAGNOSTIC_CODE_SET:
            raise AssertionError(f"Unknown diagnostic code: {diagnostic.code}.")
        for ref in diagnostic.refs:
            _check_ref(max_ref, ref)


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
    if construction.signature not in REGISTERED_CONSTRUCTION_SIGNATURE_SET:
        raise AssertionError(
            f"Unknown construction signature: {construction.signature}."
        )
    if not construction.evidence_refs:
        raise AssertionError(
            f"Construction {construction.key} has empty evidence_refs."
        )
    _validate_provenance(max_ref, construction.provenance)
    for ref in construction.evidence_refs:
        _check_ref(max_ref, ref)
    for slot_name, value in construction.slots.items():
        if value is None:
            raise AssertionError(
                f"Construction {construction.key} has null slot {slot_name}."
            )
        if isinstance(value, int):
            _check_ref(max_ref, value)
        if isinstance(value, tuple):
            if not value:
                raise AssertionError(
                    f"Construction {construction.key} has empty slot {slot_name}."
                )
            for ref in value:
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
