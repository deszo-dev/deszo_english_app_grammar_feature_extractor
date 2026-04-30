from __future__ import annotations

from grammar_feature_extractor._internal.features.dependency_helpers import (
    children_with_deprel,
    sorted_refs,
)
from grammar_feature_extractor._internal.models import Phrase
from grammar_feature_extractor._internal.proof_surface import make_provenance
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def build_phrases(ctx: SentenceContext) -> tuple[Phrase, ...]:
    phrases: list[Phrase] = []
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        if word.upos in {"NOUN", "PROPN", "PRON"}:
            deps = children_with_deprel(ctx, ref, "det", "amod", "compound", "nummod")
            tokens = sorted_refs([ref, *deps])
            phrases.append(
                Phrase(
                    type="NP",
                    head=ref,
                    tokens=tokens,
                    provenance=make_provenance(
                        "deterministic", "dependency", tokens, "high"
                    ),
                )
            )
            cases = children_with_deprel(ctx, ref, "case")
            if cases:
                tokens = sorted_refs([ref, *cases])
                phrases.append(
                    Phrase(
                        type="PP",
                        head=ref,
                        tokens=tokens,
                        provenance=make_provenance(
                            "deterministic", "dependency", tokens, "high"
                        ),
                    )
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
            tokens = sorted_refs([ref, *deps])
            phrases.append(
                Phrase(
                    type="VP",
                    head=ref,
                    tokens=tokens,
                    provenance=make_provenance(
                        "deterministic", "dependency", tokens, "high"
                    ),
                )
            )
    return tuple(phrases)
