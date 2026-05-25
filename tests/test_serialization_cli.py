from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import dumps_page, loads_document
from tests.conftest import sample_document


def test_stable_json_omits_none_fields() -> None:
    document = loads_document(json.dumps(sample_document()))
    page = GrammarFeatureExtractor().extract_page(document)
    payload = dumps_page(page)

    assert payload.endswith("\n")
    assert '"next_page"' not in payload
    assert '"schema_version": "grammar_feature_extractor.v5"' in payload
    assert '"runtime_metadata"' in payload
    assert '"output_completeness"' in payload
    assert '"evidence"' in payload
    assert '"provenance"' in payload
    assert '"predicate_groups"' not in payload


def test_cli_stdout_contains_json_and_stderr_is_empty_on_success() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "grammar_feature_extractor"],
        input=json.dumps(sample_document()),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["schema_version"] == "grammar_feature_extractor.v5"
    assert result.stderr == ""


def test_cli_no_evidence_keeps_empty_evidence_object() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "grammar_feature_extractor", "--no-evidence"],
        input=json.dumps(sample_document()),
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)
    sentence = payload["features"][0]["features"]
    assert result.returncode == 0
    assert sentence["evidence"]["words"] == []
    assert sentence["diagnostics"][0]["code"] == "disabled_feature_group"
    assert (
        sentence["diagnostics"][0]["feature_path"] == "features.evidence.words[*].ref"
    )


def test_cli_output_dir_pages_have_no_crlf_and_match_manifest_hashes(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "grammar_feature_extractor",
            "--output-dir",
            str(out_dir),
            "--page-size",
            "1",
        ],
        input=json.dumps(sample_document()),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr

    manifest_path = out_dir / "grammar_features.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["pages"], "manifest must list pages"
    for page_entry in manifest["pages"]:
        page_path = out_dir / page_entry["file_name"]
        page_bytes = page_path.read_bytes()
        assert b"\r\n" not in page_bytes, (
            f"{page_entry['file_name']} contains CRLF line endings; canonical "
            "serialization requires LF only."
        )
        on_disk_hash = hashlib.sha256(page_bytes).hexdigest()
        assert on_disk_hash == page_entry["sha256"], (
            f"manifest sha256 mismatch for {page_entry['file_name']}: "
            f"manifest={page_entry['sha256']} on_disk={on_disk_hash}"
        )

    assert b"\r\n" not in manifest_path.read_bytes(), (
        "manifest file contains CRLF line endings"
    )


def test_cli_input_dir_writes_one_output_package_per_input(tmp_path: Path) -> None:
    input_dir = tmp_path / "inputs"
    out_dir = tmp_path / "out"
    input_dir.mkdir()
    first = sample_document()
    second = sample_document()
    first["document_id"] = "doc-one"
    second["document_id"] = "doc-two"
    (input_dir / "one.json").write_text(json.dumps(first), encoding="utf-8")
    (input_dir / "two.json").write_text(json.dumps(second), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "grammar_feature_extractor",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(out_dir),
            "--page-size",
            "1",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""

    batch_manifest = json.loads(
        (out_dir / "grammar_features.batch_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert batch_manifest["kind"] == "grammar_feature_batch_manifest"
    assert batch_manifest["input_count"] == 2
    assert [entry["input_file"] for entry in batch_manifest["inputs"]] == [
        "one.json",
        "two.json",
    ]
    for entry in batch_manifest["inputs"]:
        child_dir = out_dir / entry["output_dir"]
        child_manifest = child_dir / "grammar_features.manifest.json"
        assert child_manifest.is_file()
        assert (child_dir / "grammar_features.page_00001.json").is_file()
        assert entry["manifest_file"] == (
            f"{entry['output_dir']}/grammar_features.manifest.json"
        )


def test_cli_input_dir_requires_output_dir(tmp_path: Path) -> None:
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    (input_dir / "one.json").write_text(
        json.dumps(sample_document()),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "grammar_feature_extractor",
            "--input-dir",
            str(input_dir),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert json.loads(result.stderr)["error_code"] == "configuration_error"


def test_lexical_groups_filled_on_dracula_fixture() -> None:
    from grammar_feature_extractor import GrammarFeatureExtractor
    from grammar_feature_extractor._internal.serialization import loads_document

    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "stanza"
        / "dracula_single_unit_stanza_document.json"
    )
    document = loads_document(fixture.read_text(encoding="utf-8"))
    result = GrammarFeatureExtractor().extract(document)

    totals = {
        "quantifiers": 0,
        "lexical_classes": 0,
        "verb_patterns": 0,
        "adjective_patterns": 0,
    }
    for sentence in result.sentences:
        lex = sentence.features.lexical
        totals["quantifiers"] += len(lex.quantifiers)
        totals["lexical_classes"] += len(lex.lexical_classes)
        totals["verb_patterns"] += len(lex.verb_patterns)
        totals["adjective_patterns"] += len(lex.adjective_patterns)

    for key, count in totals.items():
        assert count > 0, f"expected non-empty lexical.{key}, got {count}"


def test_processing_support_present_for_every_sentence() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "grammar_feature_extractor"],
        input=json.dumps(sample_document()),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    for sentence in payload["features"]:
        support = sentence["features"]["processing_support"]
        assert "quality" in support and support["quality"]["overall"] in {
            "high",
            "medium",
            "low",
        }
        assert "coverage" in support
        assert "candidate_features" in support
        assert "normalization_trace" in support
        assert "construction_family_summary" in support
        assert "feature_conflicts" in support
        assert "negative_evidence" in support
        assert "pattern_windows" in support
        local = support["local_context"]
        assert local["paragraph_position"] in {
            "initial",
            "middle",
            "final",
            "single",
            "unknown",
        }
        assert "same_unit_previous_sentence_available" in local
        assert "same_unit_next_sentence_available" in local
        assert "quote_continuation_state" in local


def test_no_internal_feature_error_in_successful_output() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "grammar_feature_extractor"],
        input=json.dumps(sample_document()),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    for sentence in payload["features"]:
        for diagnostic in sentence["features"]["diagnostics"]:
            assert diagnostic["code"] != "internal_feature_error", (
                f"internal_feature_error must not appear in successful output: {diagnostic}"
            )
            assert diagnostic["code"] != "unsupported_feature", (
                f"unsupported_feature must not appear in successful output: {diagnostic}"
            )


def test_manifest_diagnostic_summary_aggregates_page_diagnostics(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "grammar_feature_extractor",
            "--output-dir",
            str(out_dir),
            "--page-size",
            "1",
        ],
        input=json.dumps(sample_document()),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    manifest = json.loads(
        (out_dir / "grammar_features.manifest.json").read_text(encoding="utf-8")
    )
    summary = manifest["diagnostic_summary"]

    assert summary["source"] == "page_diagnostics_plus_document_summary"
    assert isinstance(summary["page_diagnostic_counts"], dict)
    assert isinstance(summary["document_summary_counts"], dict)
    assert summary["total_page_diagnostics"] == sum(
        summary["page_diagnostic_counts"].values()
    )
    assert summary["total_document_summary_diagnostics"] == sum(
        summary["document_summary_counts"].values()
    )

    aggregated: dict[str, int] = {}
    for page_entry in manifest["pages"]:
        page_data = json.loads(
            (out_dir / page_entry["file_name"]).read_text(encoding="utf-8")
        )
        for sentence in page_data["features"]:
            for diagnostic in sentence["features"]["diagnostics"]:
                code = diagnostic["code"]
                aggregated[code] = aggregated.get(code, 0) + 1

    assert summary["page_diagnostic_counts"] == aggregated
    assert "diagnostics" not in manifest


def test_cli_rejects_raw_text_with_no_stdout() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "grammar_feature_extractor"],
        input="raw text",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert result.stdout == ""
