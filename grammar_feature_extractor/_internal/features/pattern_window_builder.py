from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    NPFeature,
    PatternWindow,
    PredicateFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def _window_around(
    ctx: SentenceContext, anchor: int, radius: int
) -> tuple[int, ...]:
    refs = sorted(ctx.refs)
    return tuple(ref for ref in refs if abs(ref - anchor) <= radius)


def _surface_from_refs(ctx: SentenceContext, refs: tuple[int, ...]) -> str:
    parts: list[str] = []
    for ref in refs:
        word = ctx.word_by_ref[ref]
        parts.append(word.text)
    return " ".join(parts)


def _window_payload(
    ctx: SentenceContext, anchor: int, refs: tuple[int, ...]
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], str]:
    lemmas: list[str] = []
    upos: list[str] = []
    deprels: list[str] = []
    for ref in refs:
        word = ctx.word_by_ref[ref]
        lemmas.append((word.lemma or word.text).casefold())
        upos.append(word.upos)
        deprels.append(word.deprel or "_")
    return tuple(lemmas), tuple(upos), tuple(deprels), _surface_from_refs(ctx, refs)


def build_predicate_windows(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[PatternWindow, ...]:
    windows: list[PatternWindow] = []
    for index, predicate in enumerate(predicates):
        refs = _window_around(ctx, predicate.main, radius=2)
        if not refs:
            continue
        lemmas, upos, deprels, surface = _window_payload(ctx, predicate.main, refs)
        windows.append(
            PatternWindow(
                window_id=f"window.predicate.{index}",
                anchor_ref=predicate.main,
                window_type="predicate_window",
                refs=refs,
                surface=surface,
                lemmas=lemmas,
                upos=upos,
                deprels=deprels,
            )
        )
    return tuple(windows)


def build_np_windows(
    ctx: SentenceContext,
    np_profiles: tuple[NPFeature, ...],
) -> tuple[PatternWindow, ...]:
    windows: list[PatternWindow] = []
    for index, profile in enumerate(np_profiles):
        anchor = profile.head
        refs = _window_around(ctx, anchor, radius=2)
        if not refs:
            continue
        lemmas, upos, deprels, surface = _window_payload(ctx, anchor, refs)
        windows.append(
            PatternWindow(
                window_id=f"window.np.{index}",
                anchor_ref=anchor,
                window_type="np_window",
                refs=refs,
                surface=surface,
                lemmas=lemmas,
                upos=upos,
                deprels=deprels,
            )
        )
    return tuple(windows)


__all__ = ["build_predicate_windows", "build_np_windows"]
