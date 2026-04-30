from __future__ import annotations

from collections import defaultdict

from grammar_feature_extractor._internal.features.dependency_helpers import sorted_refs
from grammar_feature_extractor._internal.models import Coordination, WordRef
from grammar_feature_extractor._internal.proof_surface import make_provenance
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def build_coordination(ctx: SentenceContext) -> tuple[Coordination, ...]:
    groups: dict[WordRef, list[WordRef]] = defaultdict(list)
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        if word.deprel != "conj":
            continue
        head = word.head
        seen: set[WordRef] = {ref}
        while (
            head in ctx.word_by_ref
            and ctx.word_by_ref[head].deprel == "conj"
            and head not in seen
        ):
            seen.add(head)
            head = ctx.word_by_ref[head].head
        if head in ctx.word_by_ref:
            groups[head].append(ref)
    return tuple(
        Coordination(
            head=head,
            conjuncts=sorted_refs(conjuncts),
            provenance=make_provenance(
                "deterministic", "dependency", [head, *conjuncts], "high"
            ),
        )
        for head, conjuncts in sorted(groups.items())
    )
