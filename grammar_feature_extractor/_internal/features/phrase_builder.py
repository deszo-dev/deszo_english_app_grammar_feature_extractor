from __future__ import annotations

from grammar_feature_extractor._internal.features.dependency_helpers import (
    children_with_deprel,
    sorted_refs,
)
from grammar_feature_extractor._internal.models import Phrase
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def build_phrases(ctx: SentenceContext) -> tuple[Phrase, ...]:
    phrases: list[Phrase] = []
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        if word.upos in {"NOUN", "PROPN", "PRON"}:
            deps = children_with_deprel(ctx, ref, "det", "amod", "compound", "nummod")
            phrases.append(
                Phrase(type="NP", head=ref, tokens=sorted_refs([ref, *deps]))
            )
            cases = children_with_deprel(ctx, ref, "case")
            if cases:
                phrases.append(
                    Phrase(type="PP", head=ref, tokens=sorted_refs([ref, *cases]))
                )
        if word.upos in {"VERB", "AUX"}:
            deps = children_with_deprel(
                ctx,
                ref,
                "aux",
                "aux:pass",
                "cop",
                "obj",
                "obl",
                "advmod",
                "neg",
            )
            phrases.append(
                Phrase(type="VP", head=ref, tokens=sorted_refs([ref, *deps]))
            )
    return tuple(phrases)
