from __future__ import annotations

import os
from pathlib import Path

import pytest
from regression_corpora.corpus_metrics import (
    CorpusMetrics,
    collect_results_metrics,
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "RESULTS"


def test_results_quality_metrics_can_be_collected() -> None:
    if not RESULTS.exists():
        pytest.skip("RESULTS directory is not available in this checkout.")
    metrics = collect_results_metrics(RESULTS)
    assert metrics
    assert sum(item.sentences for item in metrics.values()) > 0


@pytest.mark.skipif(
    os.environ.get("STRICT_RESULT_QUALITY_GATES") != "1",
    reason="RESULTS may contain pre-hardening generated pages; enable after refresh.",
)
def test_results_quality_gates() -> None:
    metrics = collect_results_metrics(RESULTS)
    totals = _totals(metrics)
    assert totals["slot_zero_count"] == 0
    assert totals["invalid_slot_refs"] == 0
    assert totals["duplicate_feature_ids"] == 0
    assert totals["invalid_absence_anchor_refs"] == 0
    assert totals["construction_empty_evidence_refs"] == 0
    assert totals["pronoun_missing_required_determiner"] == 0
    assert totals["proper_noun_missing_required_determiner"] == 0
    assert totals["lexical_negation_count"] > 0
    assert totals["predicate_negative_count"] > 0
    assert totals["diagnostics_count"] > 0


def _totals(metrics: dict[str, CorpusMetrics]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in metrics.values():
        for key, value in item.__dict__.items():
            if isinstance(value, int):
                result[key] = result.get(key, 0) + value
    return result
