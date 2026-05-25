from __future__ import annotations

import copy
import json
from pathlib import Path

SOURCE = Path(
    r"C:\my\2026\deszo_english_app\tmp\stanza_testing_dracula\Dracula by Bram Stoker.json"
)
OUT_DIR = Path(__file__).resolve().parent


def _compact_document(source: dict[str, object], units: list[dict[str, object]]) -> dict[str, object]:
    units = copy.deepcopy(units)
    sentence_stream: list[dict[str, object]] = []
    global_word_count = 0
    for expected_index, sentence in enumerate(
        sent
        for unit in units
        for sent in unit["annotation"]["sentences"]  # type: ignore[index]
    ):
        sentence["global_sentence_index"] = expected_index
        sentence["global_sentence_id"] = f"fixture:dracula:s{expected_index:06d}"
        global_word_count += len(sentence.get("words", []))
        sentence_stream.append(
            {
                "global_sentence_id": sentence["global_sentence_id"],
                "global_sentence_index": expected_index,
                "local_sentence_index": sentence.get("local_sentence_index", 0),
                "text": sentence.get("text", ""),
            }
        )
    return {
        "producer": source["producer"],
        "document_id": source["document_id"],
        "schema_version": source["schema_version"],
        "status": source["status"],
        "language": source.get("language"),
        "execution_status": source.get("execution_status"),
        "traversal": {
            "order": "abstract_document_annotation_unit_order",
            "selected_unit_count": len(units),
            "global_sentence_count": len(sentence_stream),
            "global_word_count": global_word_count,
        },
        "unit_selection": {
            "selected_unit_ids": [unit["unit_id"] for unit in units],
            "excluded_units": [],
        },
        "units": units,
        "diagnostics": [],
        "sentence_stream": {"sentences": sentence_stream},
        "validation_summary": {
            "is_handoff_ready": True,
            "error_count": 0,
            "warning_count": 0,
        },
    }


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    units = source["units"]
    empty = {
        "producer": source["producer"],
        "document_id": "fixture-empty",
        "schema_version": source["schema_version"],
        "status": source["status"],
        "language": source.get("language"),
        "execution_status": source.get("execution_status"),
        "traversal": {
            "order": "abstract_document_annotation_unit_order",
            "selected_unit_count": 0,
            "global_sentence_count": 0,
            "global_word_count": 0,
        },
        "unit_selection": {"selected_unit_ids": [], "excluded_units": []},
        "units": [],
        "diagnostics": [],
        "sentence_stream": {"sentences": []},
        "validation_summary": {
            "is_handoff_ready": True,
            "error_count": 0,
            "warning_count": 0,
        },
    }
    fixtures = {
        "minimal_empty_stanza_document.json": empty,
        "dracula_single_unit_stanza_document.json": _compact_document(source, units[:1]),
        "dracula_multi_unit_stanza_document.json": _compact_document(source, units[:3]),
    }
    invalid_missing = copy.deepcopy(empty)
    invalid_missing["document_id"] = "fixture-invalid-missing-units"
    invalid_missing.pop("units")
    fixtures["invalid_stanza_document_missing_units.json"] = invalid_missing
    invalid_duplicate = copy.deepcopy(fixtures["dracula_single_unit_stanza_document.json"])
    invalid_duplicate["document_id"] = "fixture-invalid-duplicate-index"
    sentences = invalid_duplicate["units"][0]["annotation"]["sentences"]  # type: ignore[index]
    if len(sentences) > 1:
        sentences[1]["global_sentence_index"] = sentences[0]["global_sentence_index"]
    fixtures["invalid_stanza_document_duplicate_global_index.json"] = invalid_duplicate

    for name, payload in fixtures.items():
        (OUT_DIR / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
