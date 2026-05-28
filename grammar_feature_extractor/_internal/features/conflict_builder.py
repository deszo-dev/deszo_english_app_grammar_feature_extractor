from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    FeatureConflict,
    NPFeature,
    PassiveFeature,
    PredicateFeature,
    TypedQuantifierFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def build_predicate_conflicts(
    predicates: tuple[PredicateFeature, ...],
    passive: tuple[PassiveFeature, ...],
    sentence_index: int,
) -> tuple[FeatureConflict, ...]:
    conflicts: list[FeatureConflict] = []
    passive_predicates = {
        item.predicate for item in passive if getattr(item, "predicate", None) is not None
    }
    for index, predicate in enumerate(predicates):
        if predicate.voice == "passive" and predicate.main not in passive_predicates:
            conflicts.append(
                FeatureConflict(
                    conflict_id=f"s{sentence_index}.conflict.passive.{index}",
                    type="surface_vs_dependency",
                    feature_paths=(
                        "features.syntax.predicates[*].voice",
                        "features.syntax.passive",
                    ),
                    evidence_refs=tuple(predicate.evidence_refs),
                    resolution="downgrade_confidence",
                    winner="dependency",
                    confidence_after_resolution="medium",
                )
            )
    return tuple(conflicts)


def build_quantifier_conflicts(
    ctx: SentenceContext,
    quantifiers: tuple[TypedQuantifierFeature, ...],
    sentence_index: int,
) -> tuple[FeatureConflict, ...]:
    """Emit quantifier_vs_adjective_amod when a quantifier ref has upos=ADJ
    and deprel=amod (indicates surface adjective-like usage)."""
    conflicts: list[FeatureConflict] = []
    for index, quantifier in enumerate(quantifiers):
        word = ctx.word_by_ref.get(quantifier.ref)
        if word is None:
            continue
        if word.upos == "ADJ" and word.deprel == "amod":
            conflicts.append(
                FeatureConflict(
                    conflict_id=(
                        f"s{sentence_index}.conflict.quantifier_adj_amod.{index}"
                    ),
                    type="quantifier_vs_adjective_amod",
                    feature_paths=(
                        "features.lexical.quantifiers[*].quantifier_type",
                        "features.evidence.words[*].deprel",
                    ),
                    evidence_refs=(quantifier.ref,),
                    resolution="downgrade_confidence",
                    winner="lexicon",
                    confidence_after_resolution=quantifier.confidence,
                )
            )
    return tuple(conflicts)


def build_morphology_xpos_conflicts(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
    sentence_index: int,
) -> tuple[FeatureConflict, ...]:
    """Emit morphology_vs_xpos when XPOS and FEATS disagree on VBG vs VBN."""
    conflicts: list[FeatureConflict] = []
    for index, predicate in enumerate(predicates):
        word = ctx.word_by_ref[predicate.main]
        xpos = (word.xpos or "").upper()
        feats = ctx.morph_by_ref[predicate.main].features
        verb_form = feats.get("VerbForm")
        tense = feats.get("Tense")
        morph_vbg = verb_form == "Part" and tense == "Pres"
        morph_vbn = verb_form == "Part" and tense == "Past"
        if xpos == "VBG" and morph_vbn:
            mismatch = True
        elif xpos == "VBN" and morph_vbg:
            mismatch = True
        else:
            mismatch = False
        if mismatch:
            conflicts.append(
                FeatureConflict(
                    conflict_id=(
                        f"s{sentence_index}.conflict.morph_xpos.{index}"
                    ),
                    type="morphology_vs_xpos",
                    feature_paths=(
                        "features.morphology.normalized[*]",
                        "features.evidence.words[*].xpos",
                    ),
                    evidence_refs=(predicate.main,),
                    resolution="prefer_morphology",
                    winner="morphology",
                    confidence_after_resolution="medium",
                )
            )
    return tuple(conflicts)


__all__ = [
    "build_morphology_xpos_conflicts",
    "build_predicate_conflicts",
    "build_quantifier_conflicts",
]
