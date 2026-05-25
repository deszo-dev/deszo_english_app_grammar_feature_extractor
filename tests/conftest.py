from __future__ import annotations


def sample_document() -> dict[str, object]:
    words: list[dict[str, object]] = [
        {
            "text": "The",
            "lemma": "the",
            "upos": "DET",
            "head": 2,
            "deprel": "det",
            "start_char": 0,
            "end_char": 3,
        },
        {
            "text": "students",
            "lemma": "student",
            "upos": "NOUN",
            "feats": "Number=Plur|Person=3",
            "head": 4,
            "deprel": "nsubj",
            "start_char": 4,
            "end_char": 12,
        },
        {
            "text": "will",
            "lemma": "will",
            "upos": "AUX",
            "head": 4,
            "deprel": "aux",
            "start_char": 13,
            "end_char": 17,
        },
        {
            "text": "read",
            "lemma": "read",
            "upos": "VERB",
            "feats": "Tense=Pres|Person=3|Number=Plur",
            "head": 0,
            "deprel": "root",
            "start_char": 18,
            "end_char": 22,
        },
        {
            "text": "books",
            "lemma": "book",
            "upos": "NOUN",
            "feats": "Number=Plur",
            "head": 4,
            "deprel": "obj",
            "start_char": 23,
            "end_char": 28,
        },
    ]
    for index, word in enumerate(words, start=1):
        word["id"] = f"u-test:s0000:w{index:04d}"
        word["word_number"] = index
    sentence = {
        "id": "u-test:s0000",
        "text": "The students will read books.",
        "global_sentence_id": "doc_test:s000000",
        "global_sentence_index": 0,
        "local_sentence_index": 0,
        "tokens": [
            {
                "text": str(word["text"]),
                "word_ids": [str(word["id"])],
                "words": [word],
            }
            for word in words
        ],
        "words": words,
    }
    return {
        "producer": "stanza_annotator_document",
        "document_id": "doc-test",
        "schema_version": "stanza_annotation_handoff.v1",
        "status": "succeeded",
        "language": "en",
        "execution_status": "completed",
        "traversal": {
            "order": "abstract_document_annotation_unit_order",
            "selected_unit_count": 1,
            "global_sentence_count": 1,
            "global_word_count": len(words),
        },
        "unit_selection": {
            "selected_unit_ids": ["u-test"],
            "excluded_units": [],
        },
        "units": [
            {
                "unit_id": "u-test",
                "unit_type": "paragraph",
                "role": "body",
                "order": 0,
                "unit_order": 0,
                "text_hash": "sha256:" + ("0" * 64),
                "execution_status": "completed",
                "annotation": {
                    "status": "succeeded",
                    "execution_status": "completed",
                    "sentences": [sentence],
                    "diagnostics": [],
                },
            }
        ],
        "entities": [],
        "diagnostics": [],
        "sentence_stream": {"sentences": [sentence]},
        "validation_summary": {
            "is_handoff_ready": True,
            "error_count": 0,
            "warning_count": 0,
        },
        # Test compatibility alias only; the implementation ignores it.
        "sentences": [sentence],
    }


def stanza_document_from_words(
    text: str,
    words: list[dict[str, object]],
    *,
    document_id: str = "doc-test",
    unit_id: str = "u-test",
) -> dict[str, object]:
    prepared_words: list[dict[str, object]] = []
    for index, raw_word in enumerate(words, start=1):
        word = dict(raw_word)
        word.setdefault("id", f"{unit_id}:s0000:w{index:04d}")
        word.setdefault("word_number", index)
        prepared_words.append(word)
    sentence = {
        "id": f"{unit_id}:s0000",
        "text": text,
        "global_sentence_id": f"{document_id}:s000000",
        "global_sentence_index": 0,
        "local_sentence_index": 0,
        "tokens": [
            {
                "text": str(word["text"]),
                "word_ids": [str(word["id"])],
                "words": [word],
            }
            for word in prepared_words
        ],
        "words": prepared_words,
    }
    return {
        "producer": "stanza_annotator_document",
        "document_id": document_id,
        "schema_version": "stanza_annotation_handoff.v1",
        "status": "succeeded",
        "language": "en",
        "execution_status": "completed",
        "traversal": {
            "order": "abstract_document_annotation_unit_order",
            "selected_unit_count": 1,
            "global_sentence_count": 1,
            "global_word_count": len(prepared_words),
        },
        "unit_selection": {
            "selected_unit_ids": [unit_id],
            "excluded_units": [],
        },
        "units": [
            {
                "unit_id": unit_id,
                "unit_type": "paragraph",
                "role": "body",
                "order": 0,
                "unit_order": 0,
                "text_hash": "sha256:" + ("0" * 64),
                "execution_status": "completed",
                "annotation": {
                    "status": "succeeded",
                    "execution_status": "completed",
                    "sentences": [sentence],
                    "diagnostics": [],
                },
            }
        ],
        "diagnostics": [],
        "sentence_stream": {"sentences": [sentence]},
        "validation_summary": {
            "is_handoff_ready": True,
            "error_count": 0,
            "warning_count": 0,
        },
        "sentences": [sentence],
    }
