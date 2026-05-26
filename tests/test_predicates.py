from __future__ import annotations

import json

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import dumps_page, loads_document
from tests.conftest import stanza_document_from_words


def document_from_words(text: str, words: list[dict[str, object]]):
    return loads_document(json.dumps(stanza_document_from_words(text, words)))


def predicates_for(text: str, words: list[dict[str, object]]):
    page = GrammarFeatureExtractor().extract_page(document_from_words(text, words))
    return page.features[0].features.syntax.predicates


def features_for(text: str, words: list[dict[str, object]]):
    page = GrammarFeatureExtractor().extract_page(document_from_words(text, words))
    return page.features[0].features


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


def test_participle_is_not_normalized_as_present_simple() -> None:
    features = features_for(
        "Feeling sick.",
        [_word("Feeling", "feel", "VERB", 0, "root", 0, 7, "Tense=Pres|VerbForm=Part")],
    )

    predicate = features.syntax.predicates[0]
    signatures = {item.signature for item in features.constructions}
    candidate_reasons = {
        item.reason for item in features.processing_support.candidate_features
    }

    assert predicate.finite is False
    assert predicate.form_signature == "unknown"
    assert "present_simple_lexical_affirmative" not in signatures
    assert "non_finite_clause_candidate" in candidate_reasons


def test_irregular_past_uses_neutral_past_simple_construction_signature() -> None:
    features = features_for(
        "He ran home.",
        [
            _word("He", "he", "PRON", 2, "nsubj", 0, 2),
            _word("ran", "run", "VERB", 0, "root", 3, 6, "Tense=Past|VerbForm=Fin"),
            _word("home", "home", "NOUN", 2, "obl", 7, 11),
        ],
    )

    signatures = {item.signature for item in features.constructions}

    assert "past_simple_regular" not in signatures
    assert "past_simple_lexical_affirmative" in signatures


def test_be_past_participle_passive_is_not_progressive() -> None:
    predicates = predicates_for(
        "He was seen.",
        [
            _word("He", "he", "PRON", 3, "nsubj:pass", 0, 2),
            _word("was", "be", "AUX", 3, "aux:pass", 3, 6, "Tense=Past|VerbForm=Fin"),
            _word("seen", "see", "VERB", 0, "root", 7, 11, "Tense=Past|VerbForm=Part"),
        ],
    )

    predicate = predicates[0]
    assert predicate.voice == "passive"
    assert predicate.aspect == "unknown"
    assert predicate.form_signature == "passive_be_participle"


def test_to_be_past_participle_passive_is_not_progressive() -> None:
    predicates = predicates_for(
        "To be taken.",
        [
            _word("To", "to", "PART", 3, "mark", 0, 2),
            _word("be", "be", "AUX", 3, "aux:pass", 3, 5, "VerbForm=Inf"),
            _word("taken", "take", "VERB", 0, "root", 6, 11, "Tense=Past|VerbForm=Part"),
        ],
    )

    predicate = predicates[0]
    assert predicate.voice == "passive"
    assert predicate.form_signature == "passive_be_participle"


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

    assert '"predicates": [' in payload
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
