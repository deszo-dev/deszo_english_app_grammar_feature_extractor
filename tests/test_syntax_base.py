from __future__ import annotations

import json

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import loads_document


def document_from_words(text: str, words: list[dict[str, object]]):
    return loads_document(
        json.dumps(
            {
                "schema_version": "grammar_feature_extractor.annotated_document.input.v3",
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


def test_builds_phrases_roles_valency_and_complements() -> None:
    words: list[dict[str, object]] = [
        _word("She", "she", "PRON", 2, "nsubj", 0, 3, "Person=3|Number=Sing"),
        _word("gave", "give", "VERB", 0, "root", 4, 8, "Tense=Past|VerbForm=Fin"),
        _word("him", "he", "PRON", 2, "iobj", 9, 12, "Person=3|Number=Sing"),
        _word("a", "a", "DET", 5, "det", 13, 14),
        _word("book", "book", "NOUN", 2, "obj", 15, 19, "Number=Sing"),
        _word("in", "in", "ADP", 7, "case", 20, 22),
        _word("class", "class", "NOUN", 2, "obl", 23, 28, "Number=Sing"),
    ]
    page = GrammarFeatureExtractor().extract_page(
        document_from_words("She gave him a book in class.", words)
    )
    syntax = page.features[0].features.syntax

    assert ("NP", 5, (4, 5)) in {
        (phrase.type, phrase.head, phrase.tokens) for phrase in syntax.phrases
    }
    assert ("VP", 2, (2, 5, 7)) in {
        (phrase.type, phrase.head, phrase.tokens) for phrase in syntax.phrases
    }
    assert ("PP", 7, (6, 7)) in {
        (phrase.type, phrase.head, phrase.tokens) for phrase in syntax.phrases
    }
    clause = syntax.clauses[0]
    assert clause.type == "root"
    assert clause.tokens == (1, 2, 3, 4, 5, 6, 7)
    assert clause.roles.subject == 1
    assert clause.roles.object == 5
    assert clause.roles.indirect_object == 3
    assert clause.roles.oblique == (7,)
    assert clause.valency.subject is True
    assert clause.valency.object is True
    assert clause.valency.indirect_object is True
    assert [item.type for item in syntax.complements] == [
        "indirect_object_np",
        "object_np",
        "prepositional_phrase",
    ]
    assert syntax.complements[2].preposition == "in"


def test_builds_ccomp_xcomp_and_subordination_markers() -> None:
    words: list[dict[str, object]] = [
        _word("She", "she", "PRON", 2, "nsubj", 0, 3, "Person=3|Number=Sing"),
        _word("said", "say", "VERB", 0, "root", 4, 8, "Tense=Past|VerbForm=Fin"),
        _word("that", "that", "SCONJ", 5, "mark", 9, 13),
        _word("he", "he", "PRON", 5, "nsubj", 14, 16, "Person=3|Number=Sing"),
        _word("wanted", "want", "VERB", 2, "ccomp", 17, 23, "Tense=Past|VerbForm=Fin"),
        _word("to", "to", "PART", 7, "mark", 24, 26),
        _word("leave", "leave", "VERB", 5, "xcomp", 27, 32, "VerbForm=Inf"),
    ]
    page = GrammarFeatureExtractor().extract_page(
        document_from_words("She said that he wanted to leave.", words)
    )
    syntax = page.features[0].features.syntax

    assert [clause.type for clause in syntax.clauses] == ["root", "ccomp", "xcomp"]
    assert syntax.clauses[0].local_tokens == (1, 2)
    assert syntax.clauses[1].local_tokens == (3, 4, 5)
    assert syntax.clauses[2].local_tokens == (6, 7)
    assert [marker.marker_type for marker in syntax.subordination] == [
        "reported_that",
        "infinitive_to",
    ]
    assert [item.type for item in syntax.complements] == [
        "that_clause",
        "to_infinitive",
    ]
    assert syntax.complements[0].marker == "that"
    assert syntax.complements[1].marker == "to"


def test_builds_coordination() -> None:
    words: list[dict[str, object]] = [
        _word("John", "John", "PROPN", 2, "nsubj", 0, 4, "Number=Sing"),
        _word("reads", "read", "VERB", 0, "root", 5, 10, "Tense=Pres|VerbForm=Fin"),
        _word("and", "and", "CCONJ", 4, "cc", 11, 14),
        _word("writes", "write", "VERB", 2, "conj", 15, 21, "Tense=Pres|VerbForm=Fin"),
    ]
    page = GrammarFeatureExtractor().extract_page(
        document_from_words("John reads and writes.", words)
    )

    coordination = page.features[0].features.syntax.coordination[0]
    assert coordination.head == 2
    assert coordination.conjuncts == (4,)


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
