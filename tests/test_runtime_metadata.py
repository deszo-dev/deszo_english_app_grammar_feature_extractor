from __future__ import annotations

import json
import shutil
from pathlib import Path

from grammar_feature_extractor import ExtractorConfig, GrammarFeatureExtractor
from grammar_feature_extractor._internal.cli import main as cli_main
from grammar_feature_extractor._internal.runtime_metadata import (
    canonical_json,
    directory_source_fingerprint,
)
from tests.conftest import sample_document


def test_all_stages_expose_runtime_metadata() -> None:
    metadata = GrammarFeatureExtractor().runtime_metadata()

    assert metadata.stages
    for stage_name, stage_metadata in metadata.stages.items():
        assert stage_metadata.stage_name == stage_name
        assert stage_metadata.stage_contract_version
        assert stage_metadata.output_schema_version
        assert stage_metadata.config_contract_version
        assert stage_metadata.module_version


def test_local_runtime_metadata_has_source_fingerprints() -> None:
    metadata = GrammarFeatureExtractor().runtime_metadata()

    for stage in metadata.stages.values():
        assert stage.source_fingerprint is not None
        assert stage.source_fingerprint.startswith(("git:", "tree-sha256:", "build:"))
        for dependency in stage.dependencies:
            assert isinstance(dependency, str) and dependency


def test_runtime_metadata_is_deterministic() -> None:
    extractor = GrammarFeatureExtractor()

    first = canonical_json(extractor.runtime_metadata())
    second = canonical_json(extractor.runtime_metadata())

    assert first == second


def test_stage_fingerprint_includes_normalized_config() -> None:
    extractor = GrammarFeatureExtractor()

    first = extractor.stage_fingerprint(ExtractorConfig(include_evidence=True))
    second = extractor.stage_fingerprint(ExtractorConfig(include_evidence=False))

    assert first != second


def test_source_fingerprint_changes_when_relevant_source_changes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    source_file = source / "stage.py"
    source_file.write_text("VALUE = 1\n", encoding="utf-8")
    before = directory_source_fingerprint(source)

    source_file.write_text("VALUE = 2\n", encoding="utf-8")
    after = directory_source_fingerprint(source)

    assert before != after


def test_manifest_includes_contract_runtime_metadata(
    tmp_path: Path,
) -> None:
    payload_path = tmp_path / "input.json"
    payload_path.write_text(json.dumps(sample_document()), encoding="utf-8")
    out_dir = tmp_path / "out"

    exit_code = cli_main(
        [
            "--input",
            str(payload_path),
            "--output-dir",
            str(out_dir),
        ]
    )

    assert exit_code == 0
    manifest = json.loads(
        (out_dir / "grammar_features.manifest.json").read_text(encoding="utf-8")
    )
    runtime_metadata = manifest["runtime_metadata"]
    assert runtime_metadata["schema_version"] == "grammar_feature_extractor.v5"
    assert runtime_metadata["extractor_version"]
    assert runtime_metadata["resources"]


def test_source_fingerprint_ignores_ignored_directories(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(
        Path(__file__).parent.parent / "grammar_feature_extractor",
        source / "grammar_feature_extractor",
    )

    before = directory_source_fingerprint(source)
    cache_dir = source / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "ignored.pyc").write_bytes(b"ignored")

    assert directory_source_fingerprint(source) == before
