"""Normalize the committed raw synthetic fixture into the strict v5 input envelope.

Run from repository root:
    python scripts/normalize_filtered_annotated_fixture_v5.py
"""
from __future__ import annotations

import json
from pathlib import Path

RAW_PATH = Path("fixtures/inputs/filtered_annotated_document.raw.json")
OUT_PATH = Path("fixtures/inputs/filtered_annotated_document.v5.json")


def main() -> None:
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    normalized = {
        "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
        "entities": raw["entities"],
        "sentences": raw["sentences"],
    }
    OUT_PATH.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
