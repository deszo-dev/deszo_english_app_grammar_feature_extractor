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
SCHEMA_DIR = ROOT.parent / "docs" / "docs" / "schemas"
CONTRACT_DIR = ROOT.parent / "docs" / "docs" / "contracts"


def test_required_contract_artifacts_exist() -> None:
    required = [
        str(SCHEMA_DIR / "grammar_feature_config.v5.schema.json"),
        str(SCHEMA_DIR / "grammar_feature_document.v5.schema.json"),
        str(SCHEMA_DIR / "grammar_feature_manifest.v5.schema.json"),
        str(SCHEMA_DIR / "grammar_feature_page.v5.schema.json"),
        str(SCHEMA_DIR / "stanza_annotator_document_output.schema.json"),
        str(SCHEMA_DIR / "stanza_annotator_output.schema.json"),
        str(CONTRACT_DIR / "diagnostics-registry.json"),
        str(CONTRACT_DIR / "fixture-manifest.json"),
    ]
    for name in required:
        assert Path(name).exists(), name


def test_registry_counts_match_testing_guide() -> None:
    diagnostics = json.loads(
        (CONTRACT_DIR / "diagnostics-registry.json").read_text(encoding="utf-8")
    )
    fixture_manifest = json.loads(
        (CONTRACT_DIR / "fixture-manifest.json").read_text(encoding="utf-8")
    )
    assert len(diagnostics["diagnostics"]) == 9
    assert len(fixture_manifest["fixtures"]) == 10


def test_input_requires_stanza_producer_and_allows_upstream_metadata() -> None:
    raw = sample_document()
    raw.pop("producer")
    with pytest.raises(InputValidationError):
        parse_annotated_document(raw)
    raw = sample_document()
    raw["metadata"] = {"source": "upstream"}
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
    assert payload["schema_version"] == "grammar_feature_extractor.v5"
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


def test_rejects_aqf_success_envelope() -> None:
    with pytest.raises(InputValidationError):
        parse_annotated_document(
            {
                "schema_version": "annotation_quality_filter.v2.0",
                "status": "succeeded",
                "diagnostics": [],
            }
        )
