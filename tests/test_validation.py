from __future__ import annotations

import pytest

from grammar_feature_extractor import InputValidationError
from grammar_feature_extractor._internal.validation import parse_annotated_document
from tests.conftest import sample_document


def test_validates_structural_document() -> None:
    document = parse_annotated_document(sample_document())

    assert len(document.sentences) == 1
    assert document.sentences[0].words[0].text == "The"


def test_rejects_raw_text() -> None:
    with pytest.raises(InputValidationError):
        parse_annotated_document("The students will read books.")


def test_rejects_bool_as_int_head() -> None:
    raw = sample_document()
    sentence = raw["sentences"][0]  # type: ignore[index]
    word = sentence["words"][0]  # type: ignore[index]
    word["head"] = True  # type: ignore[index]

    with pytest.raises(InputValidationError):
        parse_annotated_document(raw)


def test_rejects_null_feats() -> None:
    raw = sample_document()
    sentence = raw["sentences"][0]  # type: ignore[index]
    sentence["words"][3]["feats"] = None  # type: ignore[index]

    with pytest.raises(InputValidationError):
        parse_annotated_document(raw)


def test_rejects_duplicate_global_sentence_index() -> None:
    raw = sample_document()
    unit = raw["units"][0]  # type: ignore[index]
    annotation = unit["annotation"]  # type: ignore[index]
    sentence = annotation["sentences"][0]  # type: ignore[index]
    duplicate = dict(sentence)
    duplicate["global_sentence_id"] = "doc_test:s000001"
    annotation["sentences"] = [sentence, duplicate]  # type: ignore[index]

    with pytest.raises(InputValidationError):
        parse_annotated_document(raw)
