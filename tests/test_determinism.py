"""Determinism gate: running CLI twice on the same input must yield byte-identical pages."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from tests.conftest import sample_document


def _run_cli(out_dir: Path) -> int:
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
    return result.returncode


def test_two_consecutive_cli_runs_produce_identical_pages(tmp_path: Path) -> None:
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    assert _run_cli(out_a) == 0
    assert _run_cli(out_b) == 0

    pages_a = sorted(out_a.glob("grammar_features.page_*.json"))
    pages_b = sorted(out_b.glob("grammar_features.page_*.json"))
    assert pages_a, "expected at least one page in run A"
    assert [p.name for p in pages_a] == [p.name for p in pages_b]
    for path_a, path_b in zip(pages_a, pages_b):
        digest_a = hashlib.sha256(path_a.read_bytes()).hexdigest()
        digest_b = hashlib.sha256(path_b.read_bytes()).hexdigest()
        assert digest_a == digest_b, (
            f"non-deterministic page output: {path_a.name} differs between runs"
        )
