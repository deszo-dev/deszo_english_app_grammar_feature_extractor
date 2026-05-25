from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    QuantifierCompatibleNumber,
    QuantifierPolaritySensitivity,
    QuantifierType,
    TypedQuantifierFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

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


__all__ = ["build_quantifiers"]
