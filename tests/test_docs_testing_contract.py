from __future__ import annotations

import json
from pathlib import Path

import pytest

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.cli import main as cli_main
from grammar_feature_extractor._internal.errors import InputValidationError
from grammar_feature_extractor._internal.serialization import dumps_page, loads_document
from grammar_feature_extractor._internal.validation import parse_annotated_document
from tests.conftest import sample_document

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "docs" / "architecture" / "schema"


def test_required_contract_artifacts_exist() -> None:
    required = [
        "annotated_document.input.v3.schema.json",
        "cli_error.v3.schema.json",
        "construction_signature_registry.v3.json",
        "diagnostic_registry.v3.json",
        "feature_path_registry.v3.json",
        "grammar_feature_common.v3.schema.json",
        "grammar_feature_config.input.v3.schema.json",
        "grammar_feature_config.v3.schema.json",
        "grammar_feature_document.v3.schema.json",
        "grammar_feature_manifest.v3.schema.json",
        "grammar_feature_page.v3.schema.json",
        "predicate_form_signature_registry.v3.json",
        "semantic_validation_registry.v3.json",
    ]
    for name in required:
        assert (SCHEMA_DIR / name).exists(), name


def test_registry_counts_match_testing_guide() -> None:
    diagnostics = json.loads(
        (SCHEMA_DIR / "diagnostic_registry.v3.json").read_text(encoding="utf-8")
    )
    semantic = json.loads(
        (SCHEMA_DIR / "semantic_validation_registry.v3.json").read_text(
            encoding="utf-8"
        )
    )
    constructions = json.loads(
        (SCHEMA_DIR / "construction_signature_registry.v3.json").read_text(
            encoding="utf-8"
        )
    )
    predicates = json.loads(
        (SCHEMA_DIR / "predicate_form_signature_registry.v3.json").read_text(
            encoding="utf-8"
        )
    )
    feature_paths = json.loads(
        (SCHEMA_DIR / "feature_path_registry.v3.json").read_text(encoding="utf-8")
    )
    assert len(diagnostics["codes"]) == 21
    assert len(semantic["codes"]) == 21
    assert len(constructions["signatures"]) == 24
    assert len(predicates["form_signatures"]) == 21
    assert len(feature_paths["paths"]) == 21


def test_input_requires_schema_version_and_rejects_unknown_fields() -> None:
    raw = sample_document()
    raw.pop("schema_version")
    with pytest.raises(InputValidationError):
        parse_annotated_document(raw)
    raw = sample_document()
    raw["unknown"] = 1
    with pytest.raises(InputValidationError):
        parse_annotated_document(raw)


def test_input_rejects_null_feats() -> None:
    raw = sample_document()
    raw["sentences"][0]["words"][0]["feats"] = None
    raw["sentences"][0]["tokens"][0]["words"][0]["feats"] = None
    with pytest.raises(InputValidationError):
        parse_annotated_document(raw)


def test_cli_invalid_json_emits_single_cli_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema_version":', encoding="utf-8")
    code = cli_main(["--input", str(bad)])
    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == ""
    assert captured.err.endswith("\n")
    payload = json.loads(captured.err)
    assert payload["kind"] == "cli_error"
    assert payload["schema_version"] == "grammar_feature_extractor.v3"
    assert payload["error_code"] == "input_json_serialization_error"


def test_cli_rejects_config_flag_as_usage_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = cli_main(["--config", "x.json"])
    captured = capsys.readouterr()
    assert code == 2
    payload = json.loads(captured.err)
    assert payload["error_code"] == "cli_usage_error"


def test_output_dir_requires_overwrite_for_non_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload_path = tmp_path / "input.json"
    payload_path.write_text(json.dumps(sample_document()), encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "existing.txt").write_text("x", encoding="utf-8")
    code = cli_main(["--input", str(payload_path), "--output-dir", str(out_dir)])
    captured = capsys.readouterr()
    assert code == 3
    payload = json.loads(captured.err)
    assert payload["error_code"] == "output_write_error"


def test_canonical_output_is_stable() -> None:
    document = loads_document(json.dumps(sample_document()))
    extractor = GrammarFeatureExtractor()
    page1 = dumps_page(extractor.extract_page(document))
    page2 = dumps_page(extractor.extract_page(document))
    assert page1.endswith("\n")
    assert page1 == page2
