from __future__ import annotations

import json
from pathlib import Path

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import (
    loads_document,
    page_to_dict,
)
from tests.conftest import sample_document


def test_v5_output_has_kind_and_no_registry_version_field() -> None:
    page = GrammarFeatureExtractor().extract_page(
        loads_document(json.dumps(sample_document()))
    )
    payload = page_to_dict(page)

    assert payload["kind"] == "grammar_feature_page"
    assert "construction_signature_registry_version" not in payload


def test_schema_bundle_manifest_tracks_feature_schemas() -> None:
    root = Path(__file__).resolve().parents[4]
    manifest_path = root / "docs" / "docs" / "contracts" / "schema-bundle-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema_paths = {item["path"] for item in manifest["schemas"]}

    assert manifest["schema_version"] == "1.0.0"
    assert "docs/schemas/grammar_feature_document.v5.schema.json" in schema_paths
    assert "docs/schemas/stanza_annotator_document_output.schema.json" in schema_paths
