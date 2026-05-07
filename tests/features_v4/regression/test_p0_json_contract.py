from __future__ import annotations

import json
from typing import Any

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import (
    loads_document,
    page_to_dict,
)


def _word(
    text: str,
    lemma: str,
    upos: str,
    head: int,
    deprel: str,
    start: int,
    end: int,
    feats: str | None = None,
) -> dict[str, object]:
    item: dict[str, object] = {
        "text": text,
        "lemma": lemma,
        "upos": upos,
        "head": head,
        "deprel": deprel,
        "start_char": start,
        "end_char": end,
    }
    if feats is not None:
        item["feats"] = feats
    return item


def _sentence(text: str, words: list[dict[str, object]]) -> dict[str, Any]:
    payload = {
        "sentences": [
            {
                "text": text,
                "tokens": [{"text": word["text"], "words": [word]} for word in words],
                "words": words,
            }
        ],
        "entities": [],
    }
    document = loads_document(json.dumps(payload))
    return page_to_dict(GrammarFeatureExtractor().extract_page(document))["features"][0]


def _np_by_head(sentence: dict[str, Any], head_ref: int) -> dict[str, Any]:
    for np in sentence["syntax"]["np_profiles"]:
        if np["head_ref"] == head_ref:
            return np
    raise AssertionError(f"NP with head_ref={head_ref} not found")


def _predicate(sentence: dict[str, Any]) -> dict[str, Any]:
    return sentence["syntax"]["predicates"][0]


def test_fx_001_it_and_common_noun_np_have_different_owner_ids() -> None:
    sentence = _sentence(
        "It is a melancholy object.",
        [
            _word("It", "it", "PRON", 5, "nsubj", 0, 2, "PronType=Prs"),
            _word("is", "be", "AUX", 5, "cop", 3, 5, "Tense=Pres|VerbForm=Fin"),
            _word("a", "a", "DET", 5, "det", 6, 7),
            _word("melancholy", "melancholy", "ADJ", 5, "amod", 8, 18),
            _word("object", "object", "NOUN", 0, "root", 19, 25, "Number=Sing"),
        ],
    )
    pronoun_np = _np_by_head(sentence, 1)
    object_np = _np_by_head(sentence, 5)

    assert pronoun_np["id"] != object_np["id"]
    assert pronoun_np["phrase_type"] == "pronoun_np"
    assert object_np["article_slot"]["owner_np_id"] == object_np["id"]
    assert object_np["article_slot"]["determiner_ref"] == 3


def test_fx_002_what_and_the_reason_are_different_nps() -> None:
    sentence = _sentence(
        "What is the reason?",
        [
            _word("What", "what", "PRON", 4, "nsubj", 0, 4, "PronType=Int"),
            _word("is", "be", "AUX", 4, "cop", 5, 7, "Tense=Pres|VerbForm=Fin"),
            _word("the", "the", "DET", 4, "det", 8, 11),
            _word("reason", "reason", "NOUN", 0, "root", 12, 18, "Number=Sing"),
        ],
    )
    what_np = _np_by_head(sentence, 1)
    reason_np = _np_by_head(sentence, 4)

    assert what_np["id"] != reason_np["id"]
    assert what_np["grammar_eligibility"]["article_choice_eligible"] is False
    assert reason_np["article_slot"]["owner_np_id"] == reason_np["id"]


def test_fx_003_and_fx_023_copular_adjective_is_not_verbal_main() -> None:
    sentence = _sentence(
        "I'm mad.",
        [
            _word("I", "I", "PRON", 3, "nsubj", 0, 1, "Person=1|Number=Sing"),
            _word("am", "be", "AUX", 3, "cop", 2, 4, "Tense=Pres|VerbForm=Fin"),
            _word("mad", "mad", "ADJ", 0, "root", 5, 8),
        ],
    )
    predicate = _predicate(sentence)

    assert predicate["predicate_type"] == "copular_adjectival"
    assert predicate["main_ref"] == 3
    assert predicate["main_upos"] == "ADJ"
    assert predicate["copula_ref"] == 2


def test_fx_004_fx_005_pronouns_are_not_np_choice_eligible() -> None:
    cried = _sentence(
        "I cried.",
        [
            _word("I", "I", "PRON", 2, "nsubj", 0, 1, "Person=1|Number=Sing"),
            _word("cried", "cry", "VERB", 0, "root", 2, 7, "Tense=Past|VerbForm=Fin"),
        ],
    )
    thank_you = _sentence(
        "Thank you.",
        [
            _word("Thank", "thank", "VERB", 0, "root", 0, 5, "VerbForm=Fin"),
            _word("you", "you", "PRON", 1, "obj", 6, 9, "Person=2"),
        ],
    )

    for np in (_np_by_head(cried, 1), _np_by_head(thank_you, 2)):
        assert np["phrase_type"] == "pronoun_np"
        assert np["grammar_eligibility"] == {
            "article_choice_eligible": False,
            "countability_choice_eligible": False,
            "plural_inflection_choice_eligible": False,
            "reason": "pronoun_np",
        }
        assert np["countability"]["status"] == "pronoun_not_applicable"


def test_fx_007_fx_008_article_slots_include_local_sound_class() -> None:
    a_child = _sentence(
        "a child",
        [
            _word("a", "a", "DET", 2, "det", 0, 1),
            _word("child", "child", "NOUN", 0, "root", 2, 7, "Number=Sing"),
        ],
    )
    an_apple = _sentence(
        "an apple",
        [
            _word("an", "an", "DET", 2, "det", 0, 2),
            _word("apple", "apple", "NOUN", 0, "root", 3, 8, "Number=Sing"),
        ],
    )

    child_slot = _np_by_head(a_child, 2)["article_slot"]
    apple_slot = _np_by_head(an_apple, 2)["article_slot"]
    assert child_slot["article_form"] == "a"
    assert child_slot["following_sound_class"] == "consonant_sound"
    assert child_slot["evidence_refs"] == [1, 2]
    assert apple_slot["article_form"] == "an"
    assert apple_slot["following_sound_class"] == "vowel_sound"


def test_fx_009_fx_010_zero_article_only_for_eligible_common_np() -> None:
    dogs = _sentence(
        "Dogs need exercise.",
        [
            _word("Dogs", "dog", "NOUN", 2, "nsubj", 0, 4, "Number=Plur"),
            _word("need", "need", "VERB", 0, "root", 5, 9, "Tense=Pres|VerbForm=Fin"),
            _word("exercise", "exercise", "NOUN", 2, "obj", 10, 18, "Number=Sing"),
        ],
    )
    tired = _sentence(
        "I am tired.",
        [
            _word("I", "I", "PRON", 3, "nsubj", 0, 1, "Person=1|Number=Sing"),
            _word("am", "be", "AUX", 3, "cop", 2, 4, "Tense=Pres|VerbForm=Fin"),
            _word("tired", "tired", "ADJ", 0, "root", 5, 10),
        ],
    )

    dogs_np = _np_by_head(dogs, 1)
    pronoun_np = _np_by_head(tired, 1)
    assert dogs_np["article_slot"]["article_presence"] == "zero"
    assert dogs_np["article_slot"]["article_form"] == "zero"
    assert dogs_np["number"] == "plural"
    assert pronoun_np["grammar_eligibility"]["article_choice_eligible"] is False
    assert pronoun_np["article_slot"]["article_presence"] == "absent_not_applicable"


def test_fx_024_fx_025_fx_026_strict_predicate_types() -> None:
    nominal = _sentence(
        "It is a problem.",
        [
            _word("It", "it", "PRON", 4, "nsubj", 0, 2),
            _word("is", "be", "AUX", 4, "cop", 3, 5, "Tense=Pres|VerbForm=Fin"),
            _word("a", "a", "DET", 4, "det", 6, 7),
            _word("problem", "problem", "NOUN", 0, "root", 8, 15, "Number=Sing"),
        ],
    )
    passive = _sentence(
        "The book was written.",
        [
            _word("The", "the", "DET", 2, "det", 0, 3),
            _word("book", "book", "NOUN", 4, "nsubj:pass", 4, 8, "Number=Sing"),
            _word("was", "be", "AUX", 4, "aux:pass", 9, 12, "Tense=Past|VerbForm=Fin"),
            _word("written", "write", "VERB", 0, "root", 13, 20, "VerbForm=Part"),
        ],
    )
    active = _sentence(
        "She wrote the book.",
        [
            _word("She", "she", "PRON", 2, "nsubj", 0, 3, "Person=3|Number=Sing"),
            _word("wrote", "write", "VERB", 0, "root", 4, 9, "Tense=Past|VerbForm=Fin"),
            _word("the", "the", "DET", 4, "det", 10, 13),
            _word("book", "book", "NOUN", 2, "obj", 14, 18, "Number=Sing"),
        ],
    )

    assert _predicate(nominal)["predicate_type"] == "copular_nominal"
    assert _predicate(passive)["predicate_type"] == "passive_verbal"
    assert _predicate(passive)["voice"] == "passive"
    assert _predicate(active)["predicate_type"] == "verbal"
    assert _predicate(active)["voice"] == "active"
