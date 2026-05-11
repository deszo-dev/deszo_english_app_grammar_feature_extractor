from __future__ import annotations

import json

from grammar_feature_extractor import (
    ExtractorConfig,
    GrammarFeatureExtractor,
    PagingConfig,
)
from grammar_feature_extractor._internal.serialization import (
    loads_document,
    page_to_dict,
)
from tests.conftest import sample_document


def test_extracts_v3_shell_evidence_and_morphology() -> None:
    document = loads_document(json.dumps(sample_document()))
    page = GrammarFeatureExtractor().extract_page(document)
    first = page.features[0].features

    assert page.schema_version == "grammar_feature_extractor.v3"
    assert first.evidence.words[0].ref == 1
    assert first.evidence.words[0].lower == "the"
    assert first.evidence.words[1].children == (1,)
    assert first.evidence.words[3].children == (2, 3, 5)
    assert first.evidence.dependencies[3].governor == 0
    assert first.evidence.dependencies[3].dependent == 4
    assert first.morphology.word_morphology[1].features == {
        "Number": "Plur",
        "Person": "3",
    }
    assert first.morphology.normalized[1].is_plural_noun is True
    assert first.morphology.normalized[3].is_finite_verb is True
    assert first.syntax.predicates[0].main == 4
    assert first.constructions
    assert first.contrastive_support
    assert first.absences


def test_out_of_range_page_is_empty_range_at_offset() -> None:
    document = loads_document(json.dumps(sample_document()))
    page = GrammarFeatureExtractor().extract_page(
        document,
        paging=PagingConfig(page_number=3, page_size=2),
    )

    assert page.page.sentence_start == 4
    assert page.page.sentence_end_exclusive == 4
    assert page.features == ()
    assert page.page.next_page is None


def test_diagnostics_can_be_disabled_but_field_remains() -> None:
    raw = sample_document()
    sentence = raw["sentences"][0]  # type: ignore[index]
    word = sentence["words"][3]  # type: ignore[index]
    word["feats"] = "Tense=Pres|Broken"  # type: ignore[index]
    sentence["tokens"][3]["words"][0]["feats"] = "Tense=Pres|Broken"  # type: ignore[index]
    document = loads_document(json.dumps(raw))
    extractor = GrammarFeatureExtractor()

    page = extractor.extract_page(document)
    disabled = extractor.extract_page(
        document,
        config=ExtractorConfig(include_diagnostics=False),
    )

    assert page.features[0].features.diagnostics[0].code == "malformed_feats"
    disabled_payload = page_to_dict(disabled)
    assert disabled_payload["features"][0]["features"]["diagnostics"] == []  # type: ignore[index]


def test_debug_does_not_change_payload() -> None:
    document = loads_document(json.dumps(sample_document()))
    extractor = GrammarFeatureExtractor()
    normal = page_to_dict(extractor.extract_page(document))
    debug = page_to_dict(
        extractor.extract_page(document, config=ExtractorConfig(debug=True))
    )

    assert debug == normal


def test_no_evidence_keeps_empty_evidence_field_and_internal_morphology() -> None:
    document = loads_document(json.dumps(sample_document()))
    page = GrammarFeatureExtractor().extract_page(
        document,
        config=ExtractorConfig(include_evidence=False),
    )
    feature_set = page.features[0].features

    assert feature_set.evidence.words == ()
    assert feature_set.evidence.dependencies == ()
    assert feature_set.morphology.normalized[1].is_plural_noun is True
    assert feature_set.diagnostics[0].code == "evidence_omitted_by_config"


def test_evidence_ref_position_head_lower_and_missing_feats() -> None:
    raw = sample_document()
    sentence = raw["sentences"][0]  # type: ignore[index]
    word = sentence["words"][2]  # type: ignore[index]
    word.pop("feats", None)  # type: ignore[attr-defined]
    document = loads_document(json.dumps(raw))
    evidence = (
        GrammarFeatureExtractor().extract_page(document).features[0].features.evidence
    )

    assert evidence.words[2].ref == 3
    assert evidence.words[2].position == 2
    assert evidence.words[2].head == 4
    assert evidence.words[2].lower == "will"
    assert evidence.words[2].feats == {}
    assert evidence.dependencies[3].governor == 0


def test_suffix_only_comparative_does_not_create_normalized_comparative() -> None:
    words: list[dict[str, object]] = [
        {
            "text": "Forever",
            "lemma": "forever",
            "upos": "ADV",
            "xpos": "RB",
            "head": 2,
            "deprel": "advmod",
            "start_char": 0,
            "end_char": 7,
        },
        {
            "text": "flushing",
            "lemma": "flush",
            "upos": "VERB",
            "feats": "VerbForm=Ger",
            "head": 0,
            "deprel": "root",
            "start_char": 8,
            "end_char": 16,
        },
    ]
    page = GrammarFeatureExtractor().extract_page(
        loads_document(
            json.dumps(
                {
                    "schema_version": "grammar_feature_extractor.annotated_document.input.v3",
                    "sentences": [
                        {
                            "text": "Forever flushing.",
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
    )

    assert page.features[0].features.morphology.normalized[0].is_comparative is False


def test_normalizes_infinitive_gerund_and_participles() -> None:
    words: list[dict[str, object]] = [
        {
            "text": "To",
            "lemma": "to",
            "upos": "PART",
            "head": 2,
            "deprel": "mark",
            "start_char": 0,
            "end_char": 2,
        },
        {
            "text": "go",
            "lemma": "go",
            "upos": "VERB",
            "feats": "VerbForm=Inf",
            "head": 0,
            "deprel": "root",
            "start_char": 3,
            "end_char": 5,
        },
        {
            "text": "running",
            "lemma": "run",
            "upos": "VERB",
            "feats": "VerbForm=Ger",
            "head": 2,
            "deprel": "advcl",
            "start_char": 6,
            "end_char": 13,
        },
        {
            "text": "written",
            "lemma": "write",
            "upos": "VERB",
            "xpos": "VBN",
            "feats": "VerbForm=Part|Tense=Past",
            "head": 2,
            "deprel": "xcomp",
            "start_char": 14,
            "end_char": 21,
        },
        {
            "text": "working",
            "lemma": "work",
            "upos": "VERB",
            "xpos": "VBG",
            "feats": "VerbForm=Part|Tense=Pres",
            "head": 2,
            "deprel": "xcomp",
            "start_char": 22,
            "end_char": 29,
        },
    ]
    page = GrammarFeatureExtractor().extract_page(
        loads_document(
            json.dumps(
                {
                    "schema_version": "grammar_feature_extractor.annotated_document.input.v3",
                    "sentences": [
                        {
                            "text": "To go running written working.",
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
    )
    normalized = page.features[0].features.morphology.normalized

    assert normalized[1].is_to_infinitive is True
    assert normalized[1].is_base_verb is True
    assert normalized[2].is_gerund is True
    assert normalized[3].is_past_participle is True
    assert normalized[4].is_present_participle is True


def test_strong_comparative_signals_create_normalized_comparative() -> None:
    raw = sample_document()
    sentence = raw["sentences"][0]  # type: ignore[index]
    first_word = sentence["words"][0]  # type: ignore[index]
    first_word["upos"] = "ADJ"  # type: ignore[index]
    first_word["xpos"] = "JJR"  # type: ignore[index]
    first_word["feats"] = "Degree=Cmp"  # type: ignore[index]
    sentence["tokens"][0]["words"][0]["upos"] = "ADJ"  # type: ignore[index]
    sentence["tokens"][0]["words"][0]["xpos"] = "JJR"  # type: ignore[index]
    sentence["tokens"][0]["words"][0]["feats"] = "Degree=Cmp"  # type: ignore[index]

    page = GrammarFeatureExtractor().extract_page(loads_document(json.dumps(raw)))

    assert page.features[0].features.morphology.normalized[0].is_comparative is True


def test_fragment_gets_sentence_feature() -> None:
    words: list[dict[str, object]] = [
        {
            "text": "The",
            "lemma": "the",
            "upos": "DET",
            "head": 3,
            "deprel": "det",
            "start_char": 0,
            "end_char": 3,
        },
        {
            "text": "beautiful",
            "lemma": "beautiful",
            "upos": "ADJ",
            "head": 3,
            "deprel": "amod",
            "start_char": 4,
            "end_char": 13,
        },
        {
            "text": "place",
            "lemma": "place",
            "upos": "NOUN",
            "head": 0,
            "deprel": "root",
            "start_char": 14,
            "end_char": 19,
        },
    ]
    document = loads_document(
        json.dumps(
            {
                "schema_version": "grammar_feature_extractor.annotated_document.input.v3",
                "sentences": [
                    {
                        "text": "The beautiful place!",
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
    page = GrammarFeatureExtractor().extract_page(document)
    sentence = page.features[0].features.lexical.sentence

    assert sentence.sentence_kind == "exclamation_fragment"
    assert sentence.sentence_type == "exclamative"
    assert sentence.has_exclamation_marker is True
