from __future__ import annotations

import json

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.serialization import loads_document
from tests.conftest import stanza_document_from_words


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


def _sentence(text: str, words: list[dict[str, object]]):
    payload = stanza_document_from_words(text, words)
    document = loads_document(json.dumps(payload))
    return GrammarFeatureExtractor().extract(document).sentences[0].features


def test_quote_segmentation_splits_quote_and_speaker_tag() -> None:
    features = _sentence(
        '"You are wrong," she said.',
        [
            _word('"You', "you", "PRON", 3, "nsubj", 0, 4),
            _word("are", "be", "AUX", 3, "cop", 5, 8, "Tense=Pres|VerbForm=Fin"),
            _word('wrong,"', "wrong", "ADJ", 5, "ccomp", 9, 16),
            _word("she", "she", "PRON", 5, "nsubj", 17, 20),
            _word("said", "say", "VERB", 0, "root", 21, 25, "Tense=Past|VerbForm=Fin"),
        ],
    )

    quote = features.discourse.direct_speech_segments[0]
    narr = features.discourse.narration_segments[0]
    assert quote.token_refs == (1, 2, 3)
    assert quote.speaker_tag_predicate_id == "pred-5"
    assert quote.speaker_np_id == "np-4"
    assert narr.token_refs == (4, 5)


def test_question_classification_handles_discourse_marker_wh_question() -> None:
    features = _sentence(
        "Pray, what is the reason of that?",
        [
            _word("Pray", "pray", "INTJ", 4, "discourse", 0, 4),
            _word("what", "what", "PRON", 4, "nsubj", 6, 10, "PronType=Int"),
            _word("is", "be", "AUX", 4, "cop", 11, 13, "Tense=Pres|VerbForm=Fin"),
            _word("reason", "reason", "NOUN", 0, "root", 18, 24, "Number=Sing"),
        ],
    )

    assert features.lexical.sentence.sentence_type == "wh_question"
    assert features.lexical.sentence.question_type == "wh"
    assert features.lexical.sentence.terminal_question_mark is True


def test_relative_clause_object_gap_is_conservative_and_explicit() -> None:
    features = _sentence(
        "The book I read was old.",
        [
            _word("The", "the", "DET", 2, "det", 0, 3),
            _word("book", "book", "NOUN", 6, "nsubj", 4, 8, "Number=Sing"),
            _word("I", "I", "PRON", 4, "nsubj", 9, 10),
            _word("read", "read", "VERB", 2, "acl", 11, 15, "Tense=Past|VerbForm=Fin"),
            _word("was", "be", "AUX", 6, "cop", 16, 19, "Tense=Past|VerbForm=Fin"),
            _word("old", "old", "ADJ", 0, "root", 20, 23),
        ],
    )

    relcl = features.syntax.relative_clauses[0]
    assert relcl.antecedent_np_id == "np-2"
    assert relcl.relative_marker is None
    assert relcl.relative_role == "object"
    assert relcl.object_gap is True
    assert relcl.is_omitted_relative_pronoun is True


def test_multiword_cues_require_exact_span_and_scope_caps_confidence() -> None:
    have_to = _sentence(
        "I have to go.",
        [
            _word("I", "I", "PRON", 2, "nsubj", 0, 1),
            _word("have", "have", "VERB", 0, "root", 2, 6, "Tense=Pres|VerbForm=Fin"),
            _word("to", "to", "PART", 4, "mark", 7, 9),
            _word("go", "go", "VERB", 2, "xcomp", 10, 12, "VerbForm=Inf"),
        ],
    )
    infinitive = _sentence(
        "to grow here",
        [
            _word("to", "to", "PART", 2, "mark", 0, 2),
            _word("grow", "grow", "VERB", 0, "root", 3, 7, "VerbForm=Inf"),
            _word("here", "here", "ADV", 2, "advmod", 8, 12),
        ],
    )

    cue = have_to.lexical.multiword_cues[0]
    assert cue.cue_key == "have_to"
    assert cue.scope_owner_id == "pred-2"
    assert cue.confidence == "high"
    assert infinitive.lexical.multiword_cues == ()


def test_future_time_orientation_and_time_expressions_are_curated() -> None:
    features = _sentence(
        "She is going to leave tomorrow.",
        [
            _word("She", "she", "PRON", 3, "nsubj", 0, 3),
            _word("is", "be", "AUX", 3, "aux", 4, 6, "Tense=Pres|VerbForm=Fin"),
            _word("going", "go", "VERB", 0, "root", 7, 12, "VerbForm=Part"),
            _word("to", "to", "PART", 5, "mark", 13, 15),
            _word("leave", "leave", "VERB", 3, "xcomp", 16, 21, "VerbForm=Inf"),
            _word("tomorrow", "tomorrow", "ADV", 5, "advmod", 22, 30),
        ],
    )

    assert features.time_expressions[0].time_kind == "future_specific"
    future = features.syntax.predicates[0].future_marking
    assert future is not None
    assert future.be_going_to is True
    assert future.future_time_expression_ids == ("time-1",)
    assert future.future_orientation == "explicit_future"


def test_existential_there_expanded_shape_and_negative_case() -> None:
    existential = _sentence(
        "Are there books on the table?",
        [
            _word("Are", "be", "AUX", 0, "root", 0, 3, "Tense=Pres|VerbForm=Fin"),
            _word("there", "there", "PRON", 1, "expl", 4, 9),
            _word("books", "book", "NOUN", 1, "nsubj", 10, 15, "Number=Plur"),
        ],
    )
    ordinary = _sentence(
        "Are you fond of music?",
        [
            _word("Are", "be", "AUX", 3, "cop", 0, 3, "Tense=Pres|VerbForm=Fin"),
            _word("you", "you", "PRON", 3, "nsubj", 4, 7),
            _word("fond", "fond", "ADJ", 0, "root", 8, 12),
            _word("of", "of", "ADP", 5, "case", 13, 15),
            _word("music", "music", "NOUN", 3, "obl", 16, 21),
        ],
    )

    pred = existential.syntax.predicates[0]
    assert pred.predicate_type == "existential_there"
    assert pred.expletive_subject == 2
    assert ordinary.syntax.predicates[0].predicate_type == "copular_adjectival"


def test_feature_support_is_exposed_on_api_model() -> None:
    features = _sentence(
        "She left.",
        [
            _word("She", "she", "PRON", 2, "nsubj", 0, 3),
            _word("left", "leave", "VERB", 0, "root", 4, 8, "Tense=Past|VerbForm=Fin"),
        ],
    )

    assert features.feature_support["document_structure"].status == (
        "not_supported_in_v4_scope"
    )
