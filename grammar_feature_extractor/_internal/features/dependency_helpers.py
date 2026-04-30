from __future__ import annotations

from grammar_feature_extractor._internal.models import WordRef
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def children_with_deprel(
    ctx: SentenceContext,
    head: WordRef,
    *deprels: str,
) -> tuple[WordRef, ...]:
    wanted = set(deprels)
    return tuple(
        ref
        for ref in ctx.children_by_head.get(head, ())
        if ctx.word_by_ref[ref].deprel in wanted
    )


def subtree_tokens(
    ctx: SentenceContext,
    head: WordRef,
) -> tuple[tuple[WordRef, ...], tuple[WordRef, ...]]:
    result: list[WordRef] = []
    cycle_refs: list[WordRef] = []
    visiting: set[WordRef] = set()
    visited: set[WordRef] = set()

    def walk(ref: WordRef) -> None:
        if ref in visiting:
            cycle_refs.append(ref)
            return
        if ref in visited:
            return
        visiting.add(ref)
        result.append(ref)
        for child in ctx.children_by_head.get(ref, ()):
            walk(child)
        visiting.remove(ref)
        visited.add(ref)

    walk(head)
    return tuple(sorted(dict.fromkeys(result))), tuple(
        sorted(dict.fromkeys(cycle_refs))
    )


def local_clause_tokens(
    ctx: SentenceContext,
    head: WordRef,
    clause_heads: tuple[WordRef, ...],
) -> tuple[tuple[WordRef, ...], tuple[WordRef, ...]]:
    tokens, cycle_refs = subtree_tokens(ctx, head)
    nested_tokens: set[WordRef] = set()
    token_set = set(tokens)
    for nested_head in clause_heads:
        if nested_head == head or nested_head not in token_set:
            continue
        nested_subtree, _nested_cycles = subtree_tokens(ctx, nested_head)
        nested_tokens.update(nested_subtree)
    return (
        tuple(ref for ref in tokens if ref not in nested_tokens),
        cycle_refs,
    )


def sorted_refs(refs: tuple[WordRef, ...] | list[WordRef]) -> tuple[WordRef, ...]:
    return tuple(sorted(dict.fromkeys(refs)))
