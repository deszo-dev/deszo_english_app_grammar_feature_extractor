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
    return {
        "schema_version": "grammar_feature_extractor.annotated_document.input.v3",
        "sentences": [
            {
                "text": "The students will read books.",
                "tokens": [
                    {"text": str(word["text"]), "words": [word]} for word in words
                ],
                "words": words,
            }
        ],
        "entities": [],
    }


def sample_aqf_document() -> dict[str, object]:
    legacy = sample_document()
    sentence = legacy["sentences"][0]  # type: ignore[index]
    words = sentence["words"]  # type: ignore[index]
    tokens = sentence["tokens"]  # type: ignore[index]
    stanza_words: list[dict[str, object]] = []
    stanza_tokens: list[dict[str, object]] = []
    for index, word in enumerate(words, start=1):
        word_id = f"w{index}"
        stanza_words.append(
            {
                "id": word_id,
                "text_unit_id": "tu1",
                "sentence_id": "s1",
                "word_number": index,
                **word,
            }
        )
    for index, token in enumerate(tokens, start=1):
        stanza_tokens.append(
            {
                "id": f"t{index}",
                "text_unit_id": "tu1",
                "sentence_id": "s1",
                "token_number": index,
                "text": token["text"],
                "start_char": words[index - 1]["start_char"],
                "end_char": words[index - 1]["end_char"],
                "word_ids": [f"w{index}"],
            }
        )
    return {
        "schema_version": "annotation_quality_filter.v2.0",
        "status": "succeeded",
        "diagnostics": [],
        "annotation_quality": {
            "module_name": "annotation_quality_filter",
            "module_version": "2.0.0",
            "config_version": "annotation_quality_filter_config.v2.0",
            "status": "succeeded",
            "duration_ms": 1,
        },
        "quality": {
            "source": {
                "stanza_schema_version": "stanza_annotator.v2.0",
                "quality_input_fingerprint": "sha256:" + ("0" * 64),
            },
            "text_units": [],
            "summary": {},
            "config_version": "annotation_quality_filter_config.v2.0",
        },
        "document": {
            "book": {
                "chapters": [
                    {
                        "id": "ch1",
                        "chapter_number": 1,
                        "type": "chapter",
                        "text": sentence["text"],
                        "text_annotation_status": "annotated",
                        "text_annotation": {
                            "text_unit_id": "tu1",
                            "ref": {
                                "kind": "chapter_text",
                                "text_unit_id": "tu1",
                                "owner_type": "chapter",
                                "owner_id": "ch1",
                                "source_field": "text",
                            },
                            "text": sentence["text"],
                            "sentences": [
                                {
                                    "id": "s1",
                                    "text_unit_id": "tu1",
                                    "sentence_number": 1,
                                    "text": sentence["text"],
                                    "start_char": 0,
                                    "end_char": words[-1]["end_char"],
                                    "tokens": stanza_tokens,
                                    "words": stanza_words,
                                    "summary": {},
                                }
                            ],
                            "entities": [],
                            "summary": {},
                        },
                        "footnotes": [],
                    }
                ]
            }
        },
    }
