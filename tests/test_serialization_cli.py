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
    assert payload.startswith('{"schema_version":"grammar_feature_extractor.v3"')
    assert '"evidence"' in payload
    assert '"morphology"' in payload
    assert '"predicate_groups"' not in payload


def test_cli_stdout_contains_json_and_stderr_contains_logs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "grammar_feature_extractor"],
        input=json.dumps(sample_document()),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["schema_version"] == "grammar_feature_extractor.v3"
    assert "pipeline start" in result.stderr


def test_cli_no_evidence_keeps_empty_evidence_object() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "grammar_feature_extractor", "--no-evidence"],
        input=json.dumps(sample_document()),
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)
    feature_set = payload["features"][0]["features"]
    assert result.returncode == 0
    assert feature_set["evidence"] == {"words": [], "dependencies": []}
    assert feature_set["diagnostics"][0]["code"] == "evidence_omitted_by_config"


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
