from __future__ import annotations

import json

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import dumps_page, loads_document


def document_from_words(text: str, words: list[dict[str, object]]):
    return loads_document(
        json.dumps(
            {
                "sentences": [
                    {
                        "text": text,
                        "tokens": [
                            {"text": str(word["text"]), "words": [word]}
                            for word in words
                        ],
                        "words": words,
                    }
                ],
                "entities": [],
            }
        )
    )


def predicates_for(text: str, words: list[dict[str, object]]):
    page = GrammarFeatureExtractor().extract_page(document_from_words(text, words))
    return page.features[0].features.syntax.predicates


def test_verbal_predicate_v2_parity() -> None:
    predicates = predicates_for(
        "She reads books.",
        [
            _word("She", "she", "PRON", 2, "nsubj", 0, 3, "Person=3|Number=Sing"),
            _word(
                "reads",
                "read",
                "VERB",
                0,
                "root",
                4,
                9,
                "Tense=Pres|VerbForm=Fin|Person=3|Number=Sing",
            ),
            _word("books", "book", "NOUN", 2, "obj", 10, 15, "Number=Plur"),
        ],
    )

    predicate = predicates[0]
    assert predicate.main == 2
    assert predicate.predicate_type == "verbal"
    assert predicate.subject == 1
    assert predicate.object == 3
    assert predicate.finite is True
    assert predicate.polarity == "positive"
    assert predicate.agreement.agreement_type == "subject_verb"
    assert predicate.agreement.match is True


def test_negative_do_support_predicate() -> None:
    predicates = predicates_for(
        "She does not read books.",
        [
            _word("She", "she", "PRON", 4, "nsubj", 0, 3, "Person=3|Number=Sing"),
            _word(
                "does",
                "do",
                "AUX",
                4,
                "aux",
                4,
                8,
                "Tense=Pres|VerbForm=Fin|Person=3|Number=Sing",
            ),
            _word("not", "not", "PART", 4, "neg", 9, 12),
            _word("read", "read", "VERB", 0, "root", 13, 17, "VerbForm=Inf"),
            _word("books", "book", "NOUN", 4, "obj", 18, 23, "Number=Plur"),
        ],
    )

    predicate = predicates[0]
    assert predicate.main == 4
    assert [(item.ref, item.role) for item in predicate.auxiliaries] == [
        (2, "do_support")
    ]
    assert predicate.negation == 3
    assert predicate.polarity == "negative"
    assert predicate.finite is True
    assert predicate.agreement.controller == 2


def test_copular_adjectival_predicate() -> None:
    predicates = predicates_for(
        "She is happy.",
        [
            _word("She", "she", "PRON", 3, "nsubj", 0, 3, "Person=3|Number=Sing"),
            _word(
                "is",
                "be",
                "AUX",
                3,
                "cop",
                4,
                6,
                "Tense=Pres|VerbForm=Fin|Person=3|Number=Sing",
            ),
            _word("happy", "happy", "ADJ", 0, "root", 7, 12),
        ],
    )

    predicate = predicates[0]
    assert predicate.main == 3
    assert predicate.predicate_type == "copular_adjectival"
    assert predicate.copula == 2
    assert predicate.finite is True
    assert predicate.agreement.agreement_type == "subject_copula"
    assert predicate.agreement.controller == 2


def test_copular_nominal_predicate() -> None:
    predicates = predicates_for(
        "She is a teacher.",
        [
            _word("She", "she", "PRON", 4, "nsubj", 0, 3, "Person=3|Number=Sing"),
            _word(
                "is",
                "be",
                "AUX",
                4,
                "cop",
                4,
                6,
                "Tense=Pres|VerbForm=Fin|Person=3|Number=Sing",
            ),
            _word("a", "a", "DET", 4, "det", 7, 8),
            _word("teacher", "teacher", "NOUN", 0, "root", 9, 16, "Number=Sing"),
        ],
    )

    predicate = predicates[0]
    assert predicate.main == 4
    assert predicate.predicate_type == "copular_nominal"
    assert predicate.copula == 2
    assert predicate.subject == 1


def test_modal_auxiliary_predicate() -> None:
    predicates = predicates_for(
        "She can swim.",
        [
            _word("She", "she", "PRON", 3, "nsubj", 0, 3, "Person=3|Number=Sing"),
            _word(
                "can",
                "can",
                "AUX",
                3,
                "aux",
                4,
                7,
                "VerbForm=Fin",
            ),
            _word("swim", "swim", "VERB", 0, "root", 8, 12, "VerbForm=Inf"),
        ],
    )

    predicate = predicates[0]
    assert predicate.main == 3
    assert [(item.ref, item.role) for item in predicate.auxiliaries] == [(2, "modal")]
    assert predicate.modality is not None
    assert predicate.modality.marker_refs == (2,)
    assert predicate.finite is True


def test_subordinate_predicates_are_built_from_clauses() -> None:
    predicates = predicates_for(
        "I know that she reads books.",
        [
            _word("I", "I", "PRON", 2, "nsubj", 0, 1, "Person=1|Number=Sing"),
            _word("know", "know", "VERB", 0, "root", 2, 6, "Tense=Pres|VerbForm=Fin"),
            _word("that", "that", "SCONJ", 5, "mark", 7, 11),
            _word("she", "she", "PRON", 5, "nsubj", 12, 15, "Person=3|Number=Sing"),
            _word(
                "reads",
                "read",
                "VERB",
                2,
                "ccomp",
                16,
                21,
                "Tense=Pres|VerbForm=Fin|Person=3|Number=Sing",
            ),
            _word("books", "book", "NOUN", 5, "obj", 22, 27, "Number=Plur"),
        ],
    )

    assert [predicate.main for predicate in predicates] == [2, 5]
    assert [predicate.clause_head for predicate in predicates] == [2, 5]
    assert predicates[1].subject == 4
    assert predicates[1].object == 6


def test_unknown_predicate_degrades_without_crashing() -> None:
    predicates = predicates_for(
        "Perhaps.",
        [_word("Perhaps", "perhaps", "ADV", 0, "root", 0, 7)],
    )

    predicate = predicates[0]
    assert predicate.main == 1
    assert predicate.predicate_type == "unknown"
    assert predicate.confidence == "low"
    assert predicate.form_signature == "unknown"


def test_serialized_predicates_do_not_restore_predicate_groups() -> None:
    page = GrammarFeatureExtractor().extract_page(
        document_from_words(
            "She reads books.",
            [
                _word(
                    "She",
                    "she",
                    "PRON",
                    2,
                    "nsubj",
                    0,
                    3,
                    "Person=3|Number=Sing",
                ),
                _word(
                    "reads",
                    "read",
                    "VERB",
                    0,
                    "root",
                    4,
                    9,
                    "Tense=Pres|VerbForm=Fin|Person=3|Number=Sing",
                ),
                _word("books", "book", "NOUN", 2, "obj", 10, 15, "Number=Plur"),
            ],
        )
    )
    payload = dumps_page(page)

    assert '"predicates":[{' in payload
    assert "predicate_groups" not in payload


def _word(
    text: str,
    lemma: str,
    upos: str,
    head: int,
    deprel: str,
    start_char: int,
    end_char: int,
    feats: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "text": text,
        "lemma": lemma,
        "upos": upos,
        "head": head,
        "deprel": deprel,
        "start_char": start_char,
        "end_char": end_char,
    }
    if feats is not None:
        result["feats"] = feats
    return result
