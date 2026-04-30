from __future__ import annotations

from typing import Literal

from grammar_feature_extractor._internal.features.morphology_builder import (
    parse_ud_feats,
)
from grammar_feature_extractor._internal.models import (
    AnnotatedSentence,
    DependencyEvidence,
    FeatureDiagnostic,
    TokenEvidence,
    WordRef,
)


def build_token_evidence(
    sentence: AnnotatedSentence,
    children_by_head: dict[WordRef | Literal[0], tuple[WordRef, ...]],
    diagnostics: list[FeatureDiagnostic],
) -> tuple[TokenEvidence, ...]:
    items: list[TokenEvidence] = []
    for position, word in enumerate(sentence.words):
        ref = position + 1
        items.append(
            TokenEvidence(
                ref=ref,
                text=word.text,
                lower=word.text.casefold(),
                lemma=word.lemma,
                upos=word.upos,
                xpos=word.xpos,
                feats=parse_ud_feats(word.feats, ref, diagnostics),
                head=word.head,
                deprel=word.deprel,
                children=children_by_head.get(ref, ()),
                start_char=word.start_char,
                end_char=word.end_char,
                position=position,
            )
        )
    return tuple(items)


def build_dependency_evidence(
    sentence: AnnotatedSentence,
) -> tuple[DependencyEvidence, ...]:
    return tuple(
        DependencyEvidence(
            governor=word.head,
            dependent=ref,
            deprel=word.deprel,
        )
        for ref, word in enumerate(sentence.words, start=1)
    )
