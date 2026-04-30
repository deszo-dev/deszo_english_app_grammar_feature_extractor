from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from regression_corpora.corpus_metrics import collect_results_metrics  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("RESULTS"))
    args = parser.parse_args()
    metrics = collect_results_metrics(args.results)
    if not metrics:
        print(f"No JSON feature pages found under {args.results}.")
        return 1
    columns = (
        "Corpus",
        "Sent",
        "Slots0",
        "InvSlot",
        "NegEv",
        "LexNeg",
        "PredNeg",
        "PronDet",
        "PropDet",
        "Diag",
        "Contr",
        "PhrV",
        "Comp",
        "Time",
        "Disc",
    )
    rows = [
        (
            item.corpus,
            item.sentences,
            item.slot_zero_count,
            item.invalid_slot_refs,
            item.negation_evidence_sentences,
            item.lexical_negation_count,
            item.predicate_negative_count,
            item.pronoun_missing_required_determiner,
            item.proper_noun_missing_required_determiner,
            item.diagnostics_count,
            item.lexical_contractions_count,
            item.lexical_phrasal_verbs_count,
            item.lexical_comparisons_count,
            item.lexical_time_markers_count,
            item.lexical_discourse_markers_count,
        )
        for item in metrics.values()
    ]
    widths = [
        max(len(str(value)) for value in (column, *(row[index] for row in rows)))
        for index, column in enumerate(columns)
    ]
    print(_format_row(columns, widths))
    print(" ".join("-" * width for width in widths))
    for row in rows:
        print(_format_row(row, widths))
    return 0


def _format_row(row: tuple[object, ...], widths: list[int]) -> str:
    return " ".join(str(value).ljust(widths[index]) for index, value in enumerate(row))


if __name__ == "__main__":
    raise SystemExit(main())
