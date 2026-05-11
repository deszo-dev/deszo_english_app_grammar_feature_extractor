from __future__ import annotations

import json
from dataclasses import replace

import pytest

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.catalog_validation import (
    validate_catalog_projection,
)
from grammar_feature_extractor._internal.errors import ConfigurationError
from grammar_feature_extractor._internal.proof_surface import make_provenance
from grammar_feature_extractor._internal.proof_surface_validator import (
    validate_proof_surface,
)
from grammar_feature_extractor._internal.serialization import (
    loads_document,
    page_to_dict,
)
from tests.conftest import sample_document


def test_provenance_serializes_in_stable_key_order() -> None:
    document = loads_document(json.dumps(sample_document()))
    page = GrammarFeatureExtractor().extract_page(document)
    predicate = page_to_dict(page)["features"][0]["features"]["syntax"]["predicates"][0]  # type: ignore[index]

    assert predicate["provenance"] == {
        "tier": "deterministic",
        "source": "dependency",
        "evidence_refs": [2, 3, 4, 5],
        "confidence": "high",
    }
    assert predicate["evidence_refs"]  # type: ignore[index]
    assert predicate["confidence"] == "high"  # type: ignore[index]


def test_make_provenance_sorts_and_deduplicates_refs() -> None:
    provenance = make_provenance("deterministic", "dependency", [3, 1, 3], "high")

    assert provenance.evidence_refs == (1, 3)


def test_invalid_ref_in_provenance_fails_validation() -> None:
    document = loads_document(json.dumps(sample_document()))
    features = GrammarFeatureExtractor().extract(document).sentences[0].features
    predicate = features.syntax.predicates[0]
    bad_predicate = replace(
        predicate,
        provenance=make_provenance("deterministic", "dependency", [999], "high"),
    )
    bad_features = replace(
        features,
        syntax=replace(features.syntax, predicates=(bad_predicate,)),
    )

    with pytest.raises(AssertionError):
        validate_proof_surface(document.sentences[0], bad_features)


def test_duplicate_predicate_ids_fail_validation() -> None:
    document = loads_document(json.dumps(sample_document()))
    features = GrammarFeatureExtractor().extract(document).sentences[0].features
    predicate = features.syntax.predicates[0]
    bad_features = replace(
        features,
        syntax=replace(features.syntax, predicates=(predicate, predicate)),
    )

    with pytest.raises(AssertionError):
        validate_proof_surface(document.sentences[0], bad_features)


def test_matcher_facing_features_expose_provenance() -> None:
    document = loads_document(json.dumps(sample_document()))
    features = GrammarFeatureExtractor().extract(document).sentences[0].features

    assert features.syntax.predicates[0].provenance.evidence_refs
    assert features.syntax.complements[0].provenance.evidence_refs
    assert features.syntax.clauses[0].provenance.evidence_refs
    assert features.constructions


def test_arbitrary_unknown_enum_value_is_rejected() -> None:
    document = loads_document(json.dumps(sample_document()))
    features = GrammarFeatureExtractor().extract(document).sentences[0].features
    predicate = features.syntax.predicates[0]
    bad_predicate = replace(predicate, predicate_type="banana")  # type: ignore[arg-type]
    bad_features = replace(
        features,
        syntax=replace(features.syntax, predicates=(bad_predicate,)),
    )

    with pytest.raises(AssertionError):
        validate_proof_surface(document.sentences[0], bad_features)


def test_explicit_unknown_enum_value_is_accepted() -> None:
    document = loads_document(json.dumps(sample_document()))
    features = GrammarFeatureExtractor().extract(document).sentences[0].features
    predicate = features.syntax.predicates[0]
    unknown_predicate = replace(predicate, predicate_type="unknown")
    good_features = replace(
        features,
        syntax=replace(features.syntax, predicates=(unknown_predicate,)),
    )

    validate_proof_surface(document.sentences[0], good_features)


def test_catalog_projection_rejects_unknown_signature() -> None:
    with pytest.raises(ConfigurationError):
        validate_catalog_projection(
            {"construction_signatures": ["not_registered"], "feature_paths": []}
        )
