from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    PredicateComplementFeature,
    PredicateFeature,
    VerbPattern,
    VerbPatternFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def _has_type(predicate: PredicateFeature, *types: str) -> bool:
    return any(comp.type in types for comp in predicate.complements)


def _classify_predicate(predicate: PredicateFeature) -> VerbPattern:
    has_np = _has_type(predicate, "object_np")
    has_indirect_np = _has_type(predicate, "indirect_object_np")
    has_pp = _has_type(predicate, "prepositional_phrase")
    has_to_inf = _has_type(predicate, "to_infinitive")
    has_gerund = _has_type(predicate, "gerund")
    has_that = _has_type(predicate, "that_clause")
    has_wh = _has_type(predicate, "wh_clause")
    has_particle = False  # particles are not modelled as complements
    if has_indirect_np and has_np:
        return "verb_np_np"

    if has_particle and has_np:
        return "verb_particle_object"
    if has_that:
        return "verb_that_clause"
    if has_wh:
        return "verb_wh_clause"
    if has_np and has_to_inf:
        return "verb_object_to_infinitive"
    if has_to_inf:
        return "verb_to_infinitive"
    if has_gerund:
        return "verb_gerund"
    if has_np and has_pp:
        return "verb_np_pp"
    if has_np:
        return "verb_np"
    return "unknown"


def build_verb_patterns(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[VerbPatternFeature, ...]:
    items: list[VerbPatternFeature] = []
    for predicate in predicates:
        if predicate.predicate_type not in ("verbal", "transitive", "ditransitive"):
            if predicate.copula is not None:
                continue
        pattern = _classify_predicate(predicate)
        if pattern == "unknown":
            continue
        items.append(
            VerbPatternFeature(
                predicate=predicate.main,
                lemma=predicate.main_lemma,
                pattern=pattern,
                complements=predicate.complements,
                confidence=predicate.confidence,
            )
        )
    return tuple(items)


__all__ = ["build_verb_patterns"]
