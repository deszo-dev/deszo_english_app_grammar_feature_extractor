from __future__ import annotations

from grammar_feature_extractor._internal.features.dependency_helpers import (
    children_with_deprel,
    sorted_refs,
)
from grammar_feature_extractor._internal.models import (
    ComplementType,
    PredicateComplementFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def build_complements(ctx: SentenceContext) -> tuple[PredicateComplementFeature, ...]:
    complements: list[PredicateComplementFeature] = []
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        if word.head <= 0:
            continue
        complement_type = _complement_type(ctx, ref)
        if complement_type is None:
            continue
        prepositions = children_with_deprel(ctx, ref, "case")
        markers = children_with_deprel(ctx, ref, "mark")
        evidence_refs = sorted_refs([word.head, ref, *prepositions, *markers])
        complements.append(
            PredicateComplementFeature(
                governor=word.head,
                head=ref,
                type=complement_type,
                preposition=(
                    ctx.word_by_ref[prepositions[0]].text if prepositions else None
                ),
                marker=ctx.word_by_ref[markers[0]].text if markers else None,
                deprel_source=word.deprel,
                evidence_refs=evidence_refs,
                confidence=(
                    "medium" if complement_type == "prepositional_phrase" else "high"
                ),
            )
        )
    return tuple(complements)


def _complement_type(
    ctx: SentenceContext,
    ref: int,
) -> ComplementType | None:
    word = ctx.word_by_ref[ref]
    if word.deprel == "obj":
        return "object_np"
    if word.deprel == "iobj":
        return "indirect_object_np"
    if word.deprel == "obl":
        return (
            "prepositional_phrase"
            if children_with_deprel(ctx, ref, "case")
            else "unknown"
        )
    if word.deprel == "ccomp":
        markers = tuple(
            ctx.word_by_ref[item].text.casefold()
            for item in children_with_deprel(ctx, ref, "mark")
        )
        if "that" in markers:
            return "that_clause"
        if any(
            item in {"what", "who", "which", "when", "where", "why", "how"}
            for item in markers
        ):
            return "wh_clause"
        return "unknown"
    if word.deprel == "xcomp":
        markers = tuple(
            ctx.word_by_ref[item].text.casefold()
            for item in children_with_deprel(ctx, ref, "mark")
        )
        return "to_infinitive" if "to" in markers else "bare_infinitive"
    return None
