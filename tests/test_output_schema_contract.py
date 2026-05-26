from __future__ import annotations

import json
import subprocess
import sys
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
SCHEMA_DIR = ROOT.parent / "docs" / "docs" / "schemas"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "stanza"


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
        "minimal_empty_stanza_document.json",
        "dracula_single_unit_stanza_document.json",
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
        ("minimal_empty_stanza_document.json", PagingConfig(page_number=1, page_size=300)),
        ("dracula_single_unit_stanza_document.json", PagingConfig(page_number=1, page_size=5)),
    )
    for fixture_name, paging in fixtures:
        document = _fixture_document(fixture_name)
        payload = page_to_dict(extractor.extract_page(document, paging))
        errors = list(validator.iter_errors(payload))
        assert errors == [], [
            f"{fixture_name}: {'/'.join(map(str, error.absolute_path))} {error.message}"
            for error in errors[:10]
        ]


def test_output_dir_manifest_validates_against_authoritative_v5_schema(tmp_path: Path) -> None:
    validator = _validator("grammar_feature_manifest.v5.schema.json")
    document_payload = (FIXTURE_DIR / "dracula_single_unit_stanza_document.json").read_text(
        encoding="utf-8"
    )
    out_dir = tmp_path / "features"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "grammar_feature_extractor",
            "--output-dir",
            str(out_dir),
            "--page-size",
            "5",
        ],
        input=document_payload,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(
        (out_dir / "grammar_features.manifest.json").read_text(encoding="utf-8")
    )
    errors = list(validator.iter_errors(payload))
    assert errors == [], [
        f"{'/'.join(map(str, error.absolute_path))} {error.message}"
        for error in errors[:10]
    ]
