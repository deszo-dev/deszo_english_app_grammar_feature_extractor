from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    PronounCase,
    PronounFeature,
    PronounNumber,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

_PERSONAL_SUBJECT: dict[str, tuple[int, PronounNumber | None]] = {
    "i": (1, "singular"),
    "we": (1, "plural"),
    "you": (2, None),
    "he": (3, "singular"),
    "she": (3, "singular"),
    "it": (3, "singular"),
    "they": (3, "plural"),
}
_PERSONAL_OBJECT: dict[str, tuple[int, PronounNumber]] = {
    "me": (1, "singular"),
    "us": (1, "plural"),
    "him": (3, "singular"),
    "her": (3, "singular"),
    "them": (3, "plural"),
}
_POSSESSIVE_DETERMINER = {"my", "our", "your", "his", "her", "its", "their"}
_POSSESSIVE_PRONOUN = {"mine", "ours", "yours", "hers", "theirs"}
_REFLEXIVE = {
    "myself",
    "ourselves",
    "yourself",
    "yourselves",
    "himself",
    "herself",
    "itself",
    "themselves",
}
_RELATIVE = {"who", "whom", "whose", "which", "that"}
_INTERROGATIVE = {"who", "whom", "whose", "what", "which"}
_DEMONSTRATIVE = {"this", "that", "these", "those"}
_INDEFINITE = {
    "someone",
    "somebody",
    "something",
    "anyone",
    "anybody",
    "anything",
    "everyone",
    "everybody",
    "everything",
    "no_one",
    "nobody",
    "nothing",
    "one",
}


def build_pronouns(ctx: SentenceContext) -> tuple[PronounFeature, ...]:
    items: list[PronounFeature] = []
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        if word.upos != "PRON" and word.upos != "DET":
            continue
        feature = _classify(ctx, ref)
        if feature is not None:
            items.append(feature)
    return tuple(items)


def _classify(ctx: SentenceContext, ref: int) -> PronounFeature | None:
    word = ctx.word_by_ref[ref]
    lemma = (word.lemma or word.text).casefold()
    surface = word.text.casefold()
    deprel = word.deprel
    feats = ctx.morph_by_ref[ref].features
    pron_type_feat = feats.get("PronType")

    if surface == "there" and deprel == "expl":
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="existential_there",
            person=None,
            number=None,
            case=None,
        )
    if surface == "it" and deprel == "expl":
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="dummy_it",
            person=3,
            number="singular",
            case=None,
        )
    if surface in _REFLEXIVE:
        person, number = _person_number_for_reflexive(surface)
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="reflexive",
            person=person,
            number=number,
            case=None,
        )
    if pron_type_feat == "Rel" or (
        deprel in {"nsubj", "nsubj:pass", "obj", "obl"}
        and surface in _RELATIVE
        and word.head != 0
        and ctx.word_by_ref[word.head].deprel in {"acl:relcl", "acl"}
    ):
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="relative",
            person=None,
            number=None,
            case=_case_from_deprel(deprel),
        )
    if pron_type_feat == "Int" or surface in _INTERROGATIVE and deprel == "root":
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="interrogative",
            person=None,
            number=None,
            case=_case_from_deprel(deprel),
        )
    if surface in _DEMONSTRATIVE and word.upos == "PRON":
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="demonstrative",
            person=3,
            number=_demonstrative_number(surface),
            case=None,
        )
    if surface in _PERSONAL_SUBJECT:
        person, number = _PERSONAL_SUBJECT[surface]
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="personal_subject",
            person=person,
            number=number,
            case="subject",
        )
    if surface in _PERSONAL_OBJECT:
        person, number = _PERSONAL_OBJECT[surface]
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="personal_object",
            person=person,
            number=number,
            case="object",
        )
    if surface in _POSSESSIVE_DETERMINER and word.upos == "DET":
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="possessive_determiner",
            person=None,
            number=None,
            case="possessive",
        )
    if surface in _POSSESSIVE_PRONOUN:
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="possessive_pronoun",
            person=None,
            number=None,
            case="possessive",
        )
    if surface in _INDEFINITE or pron_type_feat == "Ind":
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="indefinite",
            person=3,
            number=None,
            case=None,
        )
    if word.upos == "PRON":
        return PronounFeature(
            ref=ref,
            lemma=lemma,
            pronoun_type="unknown",
            person=None,
            number=None,
            case=None,
        )
    return None


def _person_number_for_reflexive(
    surface: str,
) -> tuple[int | None, PronounNumber | None]:
    table: dict[str, tuple[int | None, PronounNumber | None]] = {
        "myself": (1, "singular"),
        "ourselves": (1, "plural"),
        "yourself": (2, "singular"),
        "yourselves": (2, "plural"),
        "himself": (3, "singular"),
        "herself": (3, "singular"),
        "itself": (3, "singular"),
        "themselves": (3, "plural"),
    }
    return table.get(surface, (None, None))


def _demonstrative_number(surface: str) -> PronounNumber | None:
    if surface in {"this", "that"}:
        return "singular"
    if surface in {"these", "those"}:
        return "plural"
    return None


def _case_from_deprel(deprel: str) -> PronounCase | None:
    if deprel in {"nsubj", "nsubj:pass"}:
        return "subject"
    if deprel in {"obj", "iobj"}:
        return "object"
    return None


__all__ = ["build_pronouns"]
