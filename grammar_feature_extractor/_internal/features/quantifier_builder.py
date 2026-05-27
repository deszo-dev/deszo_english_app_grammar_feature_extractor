from __future__ import annotations

import json
from pathlib import Path

from grammar_feature_extractor._internal.models import (
    QuantifierCompatibleNumber,
    QuantifierPolaritySensitivity,
    QuantifierType,
    TypedQuantifierFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def _load_uncountable_lemmas() -> frozenset[str]:
    lex_path = Path(__file__).resolve().parent.parent / "lexicons" / "countability.json"
    try:
        data = json.loads(lex_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return frozenset()
    return frozenset(
        lemma.casefold() for lemma in data.get("uncountable", [])
    )


_UNCOUNTABLE_LEMMAS = _load_uncountable_lemmas()

_QUANTIFIER_LEMMAS: dict[str, QuantifierType] = {
    "some": "some",
    "any": "any",
    "no": "no",
    "none": "no",
    "many": "many",
    "much": "much",
    "few": "few",
    "little": "little",
    "enough": "enough",
    "several": "many",
    "all": "many",
    "both": "many",
    "each": "many",
    "every": "many",
    "lots": "a_lot_of",
    "plenty": "a_lot_of",
}

_COMPATIBLE_NUMBER: dict[QuantifierType, QuantifierCompatibleNumber] = {
    "some": "unknown",
    "any": "unknown",
    "no": "unknown",
    "many": "plural",
    "much": "uncountable",
    "a_lot_of": "unknown",
    "few": "plural",
    "little": "uncountable",
    "enough": "unknown",
    "too_much": "uncountable",
    "too_many": "plural",
    "number": "unknown",
    "ordinal": "unknown",
    "unknown": "unknown",
}

_POLARITY_SENSITIVITY: dict[QuantifierType, QuantifierPolaritySensitivity] = {
    "any": "negative_or_question",
    "no": "negative_or_question",
    "some": "positive",
    "many": "both",
    "much": "both",
    "a_lot_of": "positive",
    "few": "both",
    "little": "both",
    "enough": "both",
    "too_much": "positive",
    "too_many": "positive",
    "number": "positive",
    "ordinal": "positive",
    "unknown": "both",
}


def build_quantifiers(ctx: SentenceContext) -> tuple[TypedQuantifierFeature, ...]:
    items: list[TypedQuantifierFeature] = []
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        lemma = (word.lemma or word.text).casefold()
        if lemma not in _QUANTIFIER_LEMMAS:
            continue
        if word.upos not in {"DET", "PRON", "ADJ", "NUM"}:
            continue
        qtype = _QUANTIFIER_LEMMAS[lemma]
        if not _is_syntactically_compatible_quantifier(ctx, ref, qtype):
            continue
        items.append(
            TypedQuantifierFeature(
                ref=ref,
                text=word.text,
                quantifier_type=qtype,
                compatible_number=_COMPATIBLE_NUMBER.get(qtype, "unknown"),
                polarity_sensitivity=_POLARITY_SENSITIVITY.get(qtype, "both"),
            )
        )
    return tuple(items)


def _is_syntactically_compatible_quantifier(
    ctx: SentenceContext,
    ref: int,
    qtype: QuantifierType,
) -> bool:
    word = ctx.word_by_ref[ref]
    head = ctx.word_by_ref.get(word.head)
    if qtype == "little" and word.upos == "ADJ":
        if word.deprel == "amod" and head is not None:
            head_lemma = (head.lemma or head.text).casefold()
            head_number = ctx.morph_by_ref[word.head].features.get("Number")
            previous = ctx.word_by_ref.get(ref - 1)
            has_a_little = (
                previous is not None and previous.text.casefold() in {"a", "an"}
            )
            head_is_uncountable = head_lemma in _UNCOUNTABLE_LEMMAS
            if head_number == "Plur":
                return False
            return head_is_uncountable and (has_a_little or head_number != "Plur")
        return False
    if qtype == "few" and word.upos == "ADJ":
        if word.deprel == "amod" and head is not None:
            return ctx.morph_by_ref[word.head].features.get("Number") == "Plur"
        return False
    if qtype in {"many", "much"} and word.upos == "ADJ" and word.deprel == "amod":
        if head is None:
            return False
        head_lemma = (head.lemma or head.text).casefold()
        head_number = ctx.morph_by_ref[word.head].features.get("Number")
        head_is_uncountable = head_lemma in _UNCOUNTABLE_LEMMAS
        if qtype == "many":
            return head_number == "Plur"
        # `much` requires uncountable head
        return head_is_uncountable or (head_number == "Sing" and head_is_uncountable)
    return True


__all__ = ["build_quantifiers"]
