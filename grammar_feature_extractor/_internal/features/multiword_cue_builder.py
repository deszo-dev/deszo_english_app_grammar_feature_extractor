from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    CueScopeType,
    MultiwordCueFeature,
    PredicateFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

CUE_PATTERNS: tuple[tuple[str, tuple[str, ...], CueScopeType], ...] = (
    ("have_to", ("have", "to"), "predicate"),
    ("need_to", ("need", "to"), "predicate"),
    ("be_able_to", ("be", "able", "to"), "predicate"),
    ("be_supposed_to", ("be", "supposed", "to"), "predicate"),
    ("used_to", ("use", "to"), "predicate"),
    ("going_to", ("go", "to"), "predicate"),
    ("next_to", ("next", "to"), "pp"),
    ("in_front_of", ("in", "front", "of"), "pp"),
    ("because_of", ("because", "of"), "pp"),
    ("as_well_as", ("as", "well", "as"), "unknown"),
)


def build_multiword_cues(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[MultiwordCueFeature, ...]:
    lemmas = tuple(
        (ctx.word_by_ref[ref].lemma or ctx.word_by_ref[ref].text).casefold()
        for ref in ctx.refs
    )
    surfaces = tuple(ctx.word_by_ref[ref].text for ref in ctx.refs)
    items: list[MultiwordCueFeature] = []
    for cue_key, pattern, scope_type in CUE_PATTERNS:
        for start in range(0, len(lemmas) - len(pattern) + 1):
            if not _matches(lemmas[start : start + len(pattern)], pattern):
                continue
            refs = tuple(ctx.refs[start : start + len(pattern)])
            scope_owner_id = _scope_owner_id(refs, predicates, scope_type)
            resolved = scope_owner_id is not None
            items.append(
                MultiwordCueFeature(
                    cue_key=cue_key,
                    surface_refs=refs,
                    lemma_sequence=pattern,
                    surface_sequence=tuple(surfaces[start : start + len(pattern)]),
                    scope_type=scope_type,
                    scope_owner_id=scope_owner_id,
                    scope_status="resolved" if resolved else "unresolved",
                    contiguous=True,
                    source="exact_lemma_span",
                    confidence="high" if resolved else "medium",
                    evidence_refs=refs,
                )
            )
    return tuple(items)


def _matches(observed: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    if observed == pattern:
        return True
    return pattern == ("use", "to") and observed == ("used", "to")


def _scope_owner_id(
    refs: tuple[int, ...],
    predicates: tuple[PredicateFeature, ...],
    scope_type: CueScopeType,
) -> str | None:
    if scope_type != "predicate":
        return None
    ref_set = set(refs)
    for predicate in predicates:
        predicate_refs = {predicate.main, *(aux.ref for aux in predicate.auxiliaries)}
        if ref_set & predicate_refs:
            return predicate.id
    return None


__all__ = ["build_multiword_cues"]
