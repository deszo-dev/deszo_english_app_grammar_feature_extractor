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
