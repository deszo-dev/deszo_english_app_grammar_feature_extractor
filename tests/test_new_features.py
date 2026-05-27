from __future__ import annotations

import hashlib
import json
from pathlib import Path

from grammar_feature_extractor import GrammarFeatureExtractor
from grammar_feature_extractor._internal.cli import main as cli_main
from grammar_feature_extractor._internal.serialization import loads_document
from tests.conftest import sample_document, stanza_document_from_words


def _extract():
    document = loads_document(json.dumps(sample_document()))
    return GrammarFeatureExtractor().extract(document)


def test_pronouns_emitted_for_known_pronoun() -> None:
    words: list[dict[str, object]] = [
        {
            "text": "She",
            "lemma": "she",
            "upos": "PRON",
            "feats": "Person=3|Number=Sing",
            "head": 2,
            "deprel": "nsubj",
            "start_char": 0,
            "end_char": 3,
        },
        {
            "text": "reads",
            "lemma": "read",
            "upos": "VERB",
            "feats": "Tense=Pres|VerbForm=Fin|Person=3|Number=Sing",
            "head": 0,
            "deprel": "root",
            "start_char": 4,
            "end_char": 9,
        },
        {
            "text": "books",
            "lemma": "book",
            "upos": "NOUN",
            "feats": "Number=Plur",
            "head": 2,
            "deprel": "obj",
            "start_char": 10,
            "end_char": 15,
        },
    ]
    payload = stanza_document_from_words("She reads books.", words)
    document = loads_document(json.dumps(payload))
    result = GrammarFeatureExtractor().extract(document)
    pronouns = result.sentences[0].features.syntax.pronouns
    assert len(pronouns) == 1
    assert pronouns[0].pronoun_type == "personal_subject"
    assert pronouns[0].person == 3
    assert pronouns[0].number == "singular"
    assert pronouns[0].case == "subject"


def test_syntax_has_all_new_typed_groups() -> None:
    result = _extract()
    syntax = result.sentences[0].features.syntax
    assert isinstance(syntax.pronouns, tuple)
    assert isinstance(syntax.special_subject_constructions, tuple)
    assert isinstance(syntax.relative_clauses, tuple)
    assert isinstance(syntax.conditionals, tuple)
    assert isinstance(syntax.reported_speech, tuple)
    assert isinstance(syntax.passive, tuple)


def test_little_adjective_on_plural_count_noun_is_not_quantifier() -> None:
    payload = stanza_document_from_words(
        "Little ducks came out.",
        [
            _word("Little", "little", "ADJ", 2, "amod", 0, 6),
            _word("ducks", "duck", "NOUN", 3, "nsubj", 7, 12, "Number=Plur"),
            _word("came", "come", "VERB", 0, "root", 13, 17, "Tense=Past|VerbForm=Fin"),
            _word("out", "out", "ADV", 3, "advmod", 18, 21),
        ],
    )
    result = GrammarFeatureExtractor().extract(loads_document(json.dumps(payload)))

    assert result.sentences[0].features.lexical.quantifiers == ()


def test_a_little_uncountable_pattern_remains_quantifier_candidate() -> None:
    payload = stanza_document_from_words(
        "A little water spilled.",
        [
            _word("A", "a", "DET", 3, "det", 0, 1),
            _word("little", "little", "ADJ", 3, "amod", 2, 8),
            _word("water", "water", "NOUN", 4, "nsubj", 9, 14),
            _word("spilled", "spill", "VERB", 0, "root", 15, 22, "Tense=Past|VerbForm=Fin"),
        ],
    )
    result = GrammarFeatureExtractor().extract(loads_document(json.dumps(payload)))
    quantifiers = result.sentences[0].features.lexical.quantifiers

    assert len(quantifiers) == 1
    assert quantifiers[0].quantifier_type == "little"


def test_noun_inflection_serialization_uses_ud_number() -> None:
    payload = stanza_document_from_words(
        "A duck slept.",
        [
            _word("A", "a", "DET", 2, "det", 0, 1),
            _word("duck", "duck", "NOUN", 3, "nsubj", 2, 6, "Number=Sing"),
            _word("slept", "sleep", "VERB", 0, "root", 7, 12, "Tense=Past|VerbForm=Fin"),
        ],
    )
    page = GrammarFeatureExtractor().extract_page(loads_document(json.dumps(payload)))
    from grammar_feature_extractor._internal.serialization import page_to_dict

    noun_inflections = page_to_dict(page)["features"][0]["features"]["lexical"][
        "noun_inflections"
    ]
    assert noun_inflections[0]["number"] == "singular"


def test_output_dir_writes_pages_and_manifest(tmp_path: Path) -> None:
    payload_path = tmp_path / "input.json"
    payload_path.write_text(json.dumps(sample_document()), encoding="utf-8")
    out_dir = tmp_path / "out"
    exit_code = cli_main(
        [
            "--input",
            str(payload_path),
            "--output-dir",
            str(out_dir),
            "--page-size",
            "1",
        ]
    )
    assert exit_code == 0
    manifest_path = out_dir / "grammar_features.manifest.json"
    page_path = out_dir / "grammar_features.page_00001.json"
    assert manifest_path.exists()
    assert page_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["kind"] == "grammar_feature_manifest"
    assert manifest["schema_version"] == "grammar_feature_extractor.v5"
    assert manifest["page_count"] == 1
    assert manifest["total_sentences"] == 1
    assert len(manifest["pages"]) == 1
    page_text = page_path.read_text(encoding="utf-8")
    expected_sha = hashlib.sha256(page_text.encode("utf-8")).hexdigest()
    assert manifest["pages"][0]["sha256"] == expected_sha
    assert manifest["pages"][0]["file_name"] == "grammar_features.page_00001.json"


def test_output_and_output_dir_are_mutually_exclusive(tmp_path: Path) -> None:
    payload_path = tmp_path / "input.json"
    payload_path.write_text(json.dumps(sample_document()), encoding="utf-8")
    exit_code = cli_main(
        [
            "--input",
            str(payload_path),
            "--output",
            str(tmp_path / "page.json"),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert exit_code == 1


def test_output_dir_is_deterministic_under_debug(tmp_path: Path) -> None:
    payload_path = tmp_path / "input.json"
    payload_path.write_text(json.dumps(sample_document()), encoding="utf-8")
    plain_dir = tmp_path / "plain"
    debug_dir = tmp_path / "debug"
    cli_main(["--input", str(payload_path), "--output-dir", str(plain_dir)])
    cli_main(["--input", str(payload_path), "--output-dir", str(debug_dir), "--debug"])
    plain_manifest = json.loads(
        (plain_dir / "grammar_features.manifest.json").read_text(encoding="utf-8")
    )
    debug_manifest = json.loads(
        (debug_dir / "grammar_features.manifest.json").read_text(encoding="utf-8")
    )
    assert plain_manifest["pages"][0]["sha256"] == debug_manifest["pages"][0]["sha256"]


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
    word: dict[str, object] = {
        "text": text,
        "lemma": lemma,
        "upos": upos,
        "head": head,
        "deprel": deprel,
        "start_char": start_char,
        "end_char": end_char,
    }
    if feats is not None:
        word["feats"] = feats
    return word
