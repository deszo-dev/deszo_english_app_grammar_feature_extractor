from __future__ import annotations

import json
from pathlib import Path

import pytest

from grammar_feature_extractor import GrammarFeatureExtractor, InputValidationError
from grammar_feature_extractor._internal.serialization import (
    document_to_dict,
    loads_document,
    page_to_dict,
)
from grammar_feature_extractor._internal.validation import parse_annotated_document

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "stanza"


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_accepts_minimal_empty_stanza_document() -> None:
    document = parse_annotated_document(_fixture("minimal_empty_stanza_document.json"))

    assert document.input_lineage.source_module == "stanza_annotator_document"
    assert document.input_lineage.global_sentence_count == 0
    assert document.sentences == ()


def test_accepts_dracula_single_unit_and_preserves_provenance() -> None:
    document = parse_annotated_document(
        _fixture("dracula_single_unit_stanza_document.json")
    )

    assert len(document.sentences) == 3
    first = document.sentences[0]
    assert first.global_sentence_index == 0
    assert first.source_unit_id == "u0000-p-chapter-001"
    assert first.words[0].source_word_id == "u0000-p-chapter-001:s0000:w0001"


def test_extract_serializes_lineage_and_sentence_provenance() -> None:
    document = loads_document(
        (FIXTURE_DIR / "dracula_single_unit_stanza_document.json").read_text(
            encoding="utf-8"
        )
    )
    extractor = GrammarFeatureExtractor()

    payload = document_to_dict(extractor.extract(document))
    page_payload = page_to_dict(extractor.extract_page(document))

    assert payload["input_lineage"]["source_module"] == "stanza_annotator_document"  # type: ignore[index]
    assert payload["sentences"][0]["global_sentence_index"] == 0  # type: ignore[index]
    assert page_payload["input_lineage"] == payload["input_lineage"]


def test_rejects_invalid_stanza_documents() -> None:
    for name in (
        "invalid_stanza_document_missing_units.json",
        "invalid_stanza_document_duplicate_global_index.json",
    ):
        with pytest.raises(InputValidationError):
            parse_annotated_document(_fixture(name))


def test_rejects_legacy_aqf_input() -> None:
    with pytest.raises(InputValidationError):
        parse_annotated_document(
            {
                "schema_version": "annotation_quality_filter.v2.0",
                "status": "succeeded",
                "diagnostics": [],
            }
        )
