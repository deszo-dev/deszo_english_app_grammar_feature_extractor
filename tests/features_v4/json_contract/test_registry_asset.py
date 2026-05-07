from __future__ import annotations

import json
from pathlib import Path

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import (
    loads_document,
    page_to_dict,
)
from tests.conftest import sample_document


def test_v4_output_references_external_construction_registry() -> None:
    page = GrammarFeatureExtractor().extract_page(
        loads_document(json.dumps(sample_document()))
    )
    payload = page_to_dict(page)

    assert payload["construction_signature_registry_version"] == (
        "construction_signature_registry.v1"
    )


def test_construction_registry_contains_neutral_signatures_only() -> None:
    root = Path(__file__).resolve().parents[3]
    registry_path = (
        root
        / "schema"
        / "grammar_feature_extractor.v4"
        / "construction_signature_registry.json"
    )
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    signatures = {item["signature"] for item in registry["signatures"]}

    assert registry["schema_version"] == "grammar_feature_extractor.v4"
    assert "existential_there_be" in signatures
    assert "article_marked_np" in signatures
    assert not any(signature.startswith("articles_") for signature in signatures)
    assert "present_simple_be_i_am_affirmative" not in signatures
