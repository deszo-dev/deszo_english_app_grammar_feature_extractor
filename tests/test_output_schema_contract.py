from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from grammar_feature_extractor import GrammarFeatureExtractor, PagingConfig
from grammar_feature_extractor._internal.serialization import (
    document_to_dict,
    loads_document,
    page_to_dict,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT.parent / "docs" / "architecture" / "schemas" / "schema"
FIXTURE_DIR = ROOT / "fixtures" / "inputs"


def _validator(schema_name: str) -> Draft202012Validator:
    resources: dict[str, Resource[object]] = {}
    for path in SCHEMA_DIR.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "$id" in payload:
            resources[payload["$id"]] = Resource.from_contents(payload)
    registry = Registry().with_resources(resources.items())
    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=registry)


def _fixture_document(name: str):
    payload = (FIXTURE_DIR / name).read_text(encoding="utf-8")
    return loads_document(payload)


def test_document_output_validates_against_authoritative_v5_schema() -> None:
    validator = _validator("grammar_feature_document.v5.schema.json")
    extractor = GrammarFeatureExtractor()

    for fixture_name in (
        "valid_minimal_copular.json",
        "valid_empty_document.json",
        "filtered_annotated_document.v3.json",
    ):
        document = _fixture_document(fixture_name)
        payload = document_to_dict(extractor.extract(document))
        errors = list(validator.iter_errors(payload))
        assert errors == [], [
            f"{fixture_name}: {'/'.join(map(str, error.absolute_path))} {error.message}"
            for error in errors[:10]
        ]


def test_page_output_validates_against_authoritative_v5_schema() -> None:
    validator = _validator("grammar_feature_page.v5.schema.json")
    extractor = GrammarFeatureExtractor()

    fixtures = (
        ("valid_minimal_copular.json", PagingConfig(page_number=1, page_size=300)),
        ("valid_empty_document.json", PagingConfig(page_number=1, page_size=300)),
        (
            "filtered_annotated_document.v3.json",
            PagingConfig(page_number=1, page_size=5),
        ),
    )
    for fixture_name, paging in fixtures:
        document = _fixture_document(fixture_name)
        payload = page_to_dict(extractor.extract_page(document, paging))
        errors = list(validator.iter_errors(payload))
        assert errors == [], [
            f"{fixture_name}: {'/'.join(map(str, error.absolute_path))} {error.message}"
            for error in errors[:10]
        ]
