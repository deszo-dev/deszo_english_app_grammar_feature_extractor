"""Defensive contradiction diagnostics for progressive/perfect chains.

These regression-guards fire when the TAVM resolver's output disagrees with
its own evidence (e.g. VBG with finite `be` aux but `aspect=unknown`).
They are intentionally cheap pattern checks; their presence in subsequent
output flags a regression of the A1 fix.
"""

from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    AuxiliaryFeature,
    FeatureDiagnostic,
    PredicateFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def _is_vbg(ctx: SentenceContext, ref: int) -> bool:
    word = ctx.word_by_ref[ref]
    xpos = (word.xpos or "").upper()
    feats = ctx.morph_by_ref[ref].features
    return (
        xpos == "VBG"
        or (feats.get("VerbForm") == "Part" and feats.get("Tense") == "Pres")
        or feats.get("VerbForm") == "Ger"
    )


def _is_vbn(ctx: SentenceContext, ref: int) -> bool:
    word = ctx.word_by_ref[ref]
    xpos = (word.xpos or "").upper()
    feats = ctx.morph_by_ref[ref].features
    return xpos == "VBN" or (
        feats.get("VerbForm") == "Part" and feats.get("Tense") == "Past"
    )


def _has_finite_be(auxiliaries: tuple[AuxiliaryFeature, ...]) -> bool:
    return any(
        aux.lemma == "be"
        and aux.role in {"tense_aux", "passive_aux"}
        and aux.surface.casefold() not in {"been", "being"}
        for aux in auxiliaries
    )


def _has_been(auxiliaries: tuple[AuxiliaryFeature, ...]) -> bool:
    return any(
        aux.lemma == "be" and aux.surface.casefold() == "been"
        for aux in auxiliaries
    )


def _has_modal(auxiliaries: tuple[AuxiliaryFeature, ...]) -> bool:
    return any(aux.role == "modal" for aux in auxiliaries)


def build_progressive_contradiction_diagnostics(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[FeatureDiagnostic, ...]:
    items: list[FeatureDiagnostic] = []
    for index, predicate in enumerate(predicates):
        feature_path = (
            f"features.syntax.predicates[{index}].tavm.form_signature"
        )
        main_is_vbg = _is_vbg(ctx, predicate.main)
        main_is_vbn = _is_vbn(ctx, predicate.main)
        aspect = predicate.aspect or "unknown"
        signature = predicate.form_signature or "unknown"
        auxiliaries = predicate.auxiliaries
        has_finite_be = _has_finite_be(auxiliaries)
        has_been = _has_been(auxiliaries)
        has_have = any(aux.lemma == "have" for aux in auxiliaries)
        has_modal = _has_modal(auxiliaries)
        evidence_refs = (
            predicate.main,
            *tuple(aux.ref for aux in auxiliaries),
        )

        if main_is_vbg and has_finite_be and aspect == "unknown":
            items.append(
                FeatureDiagnostic(
                    severity="warning",
                    code="vbg_with_be_aux_marked_unknown",
                    message=(
                        "VBG main verb with finite `be` auxiliary but aspect "
                        "resolved as unknown; expected progressive."
                    ),
                    refs=evidence_refs,
                    feature_path=feature_path,
                )
            )
        if main_is_vbg and has_finite_be and signature == "past_simple":
            items.append(
                FeatureDiagnostic(
                    severity="warning",
                    code="vbg_with_be_aux_marked_past_simple",
                    message=(
                        "VBG main verb with finite `be` auxiliary but "
                        "form_signature=past_simple; expected past_progressive."
                    ),
                    refs=evidence_refs,
                    feature_path=feature_path,
                )
            )
        if has_have and has_been and main_is_vbn and aspect == "perfect_progressive":
            items.append(
                FeatureDiagnostic(
                    severity="warning",
                    code="have_been_vbn_marked_perfect_progressive",
                    message=(
                        "`have/has/had + been + VBN` chain marked as "
                        "perfect_progressive; expected perfect passive."
                    ),
                    refs=evidence_refs,
                    feature_path=feature_path,
                )
            )
        if (
            has_modal
            and has_finite_be
            and main_is_vbg
            and signature == "modal_base_verb"
        ):
            items.append(
                FeatureDiagnostic(
                    severity="warning",
                    code="modal_be_vbg_collapsed_to_modal_base",
                    message=(
                        "Modal + be + VBG chain collapsed to "
                        "modal_base_verb; expected modal_progressive."
                    ),
                    refs=evidence_refs,
                    feature_path=feature_path,
                )
            )
        if (
            predicate.copula is not None
            and main_is_vbg
            and aspect == "progressive"
            and predicate.confidence == "low"
        ):
            items.append(
                FeatureDiagnostic(
                    severity="info",
                    code="copula_vbg_false_positive",
                    message=(
                        "Copular `be` with VBG complement marked as "
                        "finite progressive at low confidence; review "
                        "for participial-clause complement."
                    ),
                    refs=evidence_refs,
                    feature_path=feature_path,
                )
            )
    return tuple(items)


__all__ = ["build_progressive_contradiction_diagnostics"]
