from __future__ import annotations

import json

from grammar_feature_extractor import ExtractorConfig, GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import loads_document


def test_no_object_np_makes_predicate_negative() -> None:
    page = _extract(
        "Darcy made no answer.",
        [
            _word("Darcy", "Darcy", "PROPN", 2, "nsubj", 0, 5, "Number=Sing"),
            _word(
                "made",
                "make",
                "VERB",
                0,
                "root",
                6,
                10,
                "Tense=Past|VerbForm=Fin",
            ),
            _word("no", "no", "DET", 4, "det", 11, 13, "PronType=Neg"),
            _word("answer", "answer", "NOUN", 2, "obj", 14, 20, "Number=Sing"),
            _word(".", ".", "PUNCT", 2, "punct", 20, 21),
        ],
    )
    features = page.features[0].features

    assert features.syntax.predicates[0].polarity == "negative"
    assert features.lexical.sentence.polarity == "negative"
    assert features.lexical.negation[0].negation_type == "negative_determiner"


def test_rule_like_constructions_are_emitted_by_contract_default() -> None:
    page = _extract(
        "Alice slept.",
        [
            _word("Alice", "Alice", "PROPN", 2, "nsubj", 0, 5, "Number=Sing"),
            _word(
                "slept",
                "sleep",
                "VERB",
                0,
                "root",
                6,
                11,
                "Tense=Past|VerbForm=Fin",
            ),
            _word(".", ".", "PUNCT", 2, "punct", 11, 12),
        ],
    )

    assert page.features[0].features.constructions


def test_pronoun_and_proper_noun_article_slots_are_not_applicable() -> None:
    page = _extract(
        "She met Darcy.",
        [
            _word("She", "she", "PRON", 2, "nsubj", 0, 3, "Person=3"),
            _word(
                "met",
                "meet",
                "VERB",
                0,
                "root",
                4,
                7,
                "Tense=Past|VerbForm=Fin",
            ),
            _word("Darcy", "Darcy", "PROPN", 2, "obj", 8, 13, "Number=Sing"),
            _word(".", ".", "PUNCT", 2, "punct", 13, 14),
        ],
    )
    profiles = {
        item.phrase_type: item.article_slot.requiredness
        for item in page.features[0].features.syntax.np_profiles
    }

    assert profiles["pronoun_np"] == "not_applicable"
    assert profiles["proper_noun_np"] == "not_applicable"


def test_word_order_refs_are_unique() -> None:
    page = _extract(
        "She is happy.",
        [
            _word("She", "she", "PRON", 3, "nsubj", 0, 3, "Person=3"),
            _word(
                "is",
                "be",
                "AUX",
                3,
                "cop",
                4,
                6,
                "Tense=Pres|VerbForm=Fin",
            ),
            _word("happy", "happy", "ADJ", 0, "root", 7, 12),
            _word(".", ".", "PUNCT", 3, "punct", 12, 13),
        ],
    )
    word_order = page.features[0].features.lexical.word_order[0]

    assert word_order.ordered_refs == (1, 2, 3)
    assert word_order.slots == {
        "predicate": 3,
        "subject": 1,
        "copula": 2,
        "complement": 3,
    }


def _extract(
    text: str,
    words: list[dict[str, object]],
    config: ExtractorConfig | None = None,
):
    document = loads_document(
        json.dumps(
            {
                "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
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
    return GrammarFeatureExtractor().extract_page(document, config=config)


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
