from __future__ import annotations

import json
import subprocess
import sys

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import dumps_page, loads_document
from tests.conftest import sample_document


def test_stable_json_omits_none_fields() -> None:
    document = loads_document(json.dumps(sample_document()))
    page = GrammarFeatureExtractor().extract_page(document)
    payload = dumps_page(page)

    assert payload.endswith("\n")
    assert '"next_page"' not in payload
    assert payload.startswith('{"schema_version":"grammar_feature_extractor.v5"')
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
