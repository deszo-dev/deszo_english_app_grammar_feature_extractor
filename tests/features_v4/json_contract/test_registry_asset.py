from __future__ import annotations

import json
from pathlib import Path

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import (
    loads_document,
    page_to_dict,
)
from tests.conftest import sample_document


def test_v3_output_has_kind_and_no_registry_version_field() -> None:
    page = GrammarFeatureExtractor().extract_page(
        loads_document(json.dumps(sample_document()))
    )
    payload = page_to_dict(page)

    assert payload["kind"] == "grammar_feature_page"
    assert "construction_signature_registry_version" not in payload


def test_construction_registry_v3_exists_and_has_signatures() -> None:
    root = Path(__file__).resolve().parents[3]
    registry_path = (
        root
        / "docs"
        / "architecture"
        / "schema"
        / "construction_signature_registry.v3.json"
    )
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    signatures = {item["signature"] for item in registry["signatures"]}

    assert registry["schema_version"] == "grammar_feature_extractor.v3"
    assert "there_be_np" in signatures
    assert len(signatures) >= 20
