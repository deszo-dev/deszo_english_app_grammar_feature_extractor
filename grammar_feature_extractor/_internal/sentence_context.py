from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

from grammar_feature_extractor._internal.models import (
    AnnotatedSentence,
    AnnotatedWord,
    DependencyEvidence,
    FeatureDiagnostic,
    MorphFeature,
    NormalizedMorph,
    TokenEvidence,
    WordRef,
)


@dataclass(frozen=True, slots=True)
class SentenceContext:
    sentence_index: int
    text: str
    words: tuple[AnnotatedWord, ...]
    refs: tuple[WordRef, ...]
    word_by_ref: dict[WordRef, AnnotatedWord]
    evidence_by_ref: dict[WordRef, TokenEvidence]
    children_by_head: dict[WordRef | Literal[0], tuple[WordRef, ...]]
    deps: tuple[DependencyEvidence, ...]
    morph_by_ref: dict[WordRef, MorphFeature]
    normalized_morph_by_ref: dict[WordRef, NormalizedMorph]


def words_by_ref(sentence: AnnotatedSentence) -> dict[WordRef, AnnotatedWord]:
    return {index + 1: word for index, word in enumerate(sentence.words)}


def children_by_head(
    sentence: AnnotatedSentence,
) -> dict[WordRef | Literal[0], tuple[WordRef, ...]]:
    children: dict[WordRef | Literal[0], list[WordRef]] = defaultdict(list)
    for ref, word in words_by_ref(sentence).items():
        children[word.head].append(ref)
    return {head: tuple(sorted(refs)) for head, refs in children.items()}


def build_sentence_context(
    sentence_index: int,
    sentence: AnnotatedSentence,
    diagnostics: list[FeatureDiagnostic],
) -> SentenceContext:
    from grammar_feature_extractor._internal.features.evidence_builder import (
        build_dependency_evidence,
        build_token_evidence,
    )
    from grammar_feature_extractor._internal.features.morphology_builder import (
        build_morphology,
    )

    refs = tuple(range(1, len(sentence.words) + 1))
    word_map = words_by_ref(sentence)
    children = children_by_head(sentence)
    evidence_words = build_token_evidence(sentence, children, diagnostics)
    dependencies = build_dependency_evidence(sentence)
    morphology = build_morphology(sentence, diagnostics)
    return SentenceContext(
        sentence_index=sentence_index,
        text=sentence.text,
        words=sentence.words,
        refs=refs,
        word_by_ref=word_map,
        evidence_by_ref={item.ref: item for item in evidence_words},
        children_by_head=children,
        deps=dependencies,
        morph_by_ref={item.ref: item for item in morphology.word_morphology},
        normalized_morph_by_ref={item.ref: item for item in morphology.normalized},
    )
