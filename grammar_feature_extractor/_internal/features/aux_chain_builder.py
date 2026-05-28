"""Auxiliary-chain shape resolver.

Produces a stable, machine-readable `AuxChain` shape per predicate so that
downstream rule generation can use the chain signature directly instead of
re-parsing surface tokens.
"""

from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    AuxChain,
    AuxiliaryFeature,
    PredicateFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def _main_verb_form(ctx: SentenceContext, ref: int) -> str:
    word = ctx.word_by_ref[ref]
    xpos = (word.xpos or "").upper()
    if xpos in {"VBG", "VBN", "VBD", "VBP", "VBZ", "VB", "MD"}:
        return xpos
    feats = ctx.morph_by_ref[ref].features
    verb_form = feats.get("VerbForm")
    tense = feats.get("Tense")
    if verb_form == "Part" and tense == "Pres":
        return "VBG"
    if verb_form == "Part" and tense == "Past":
        return "VBN"
    if verb_form == "Fin":
        return "VB_FIN"
    if verb_form == "Inf":
        return "VB"
    return verb_form or word.upos or ""


def _chain_signature(
    ordered: list[tuple[int, str, str, str]],
    main_verb_form: str,
) -> str:
    """Build a deterministic signature like `modal_have_been_vbg`."""
    parts: list[str] = []
    for _ref, _surface, lemma, role in ordered:
        if role == "modal":
            parts.append("modal")
        elif role == "perfect_aux" or lemma == "have":
            parts.append("have")
        elif lemma == "be":
            parts.append("been" if role in {"passive_aux", "tense_aux"} and _surface.casefold() == "been"
                         else ("being" if _surface.casefold() == "being" else "be"))
        elif role == "do_support":
            parts.append("do")
        elif lemma:
            parts.append(lemma)
    parts.append(main_verb_form.lower() if main_verb_form else "verb")
    return "_".join(parts)


def _role_for_been(
    auxiliaries: tuple[AuxiliaryFeature, ...], main_xpos: str
) -> str:
    # When chain has `have + been + VBG` → progressive aux on been.
    # When chain has `have + been + VBN` → passive aux on been.
    has_have = any(aux.lemma == "have" for aux in auxiliaries)
    if has_have and main_xpos == "VBG":
        return "progressive_aux"
    if has_have and main_xpos == "VBN":
        return "passive_aux"
    return "tense_aux"


def build_aux_chain(
    ctx: SentenceContext,
    predicate: PredicateFeature,
) -> AuxChain | None:
    if not predicate.auxiliaries:
        # Still emit a single-element chain for the lexical main when no aux.
        main_form = _main_verb_form(ctx, predicate.main)
        return AuxChain(
            chain_signature=main_form.lower() or "verb",
            ordered_refs=(predicate.main,),
            ordered_lemmas=(predicate.main_lemma,),
            ordered_surfaces=(ctx.word_by_ref[predicate.main].text,),
            main_ref=predicate.main,
            main_verb_form=main_form,
            finite_anchor_ref=predicate.main if predicate.finite else None,
        )

    main_form = _main_verb_form(ctx, predicate.main)
    ordered_items: list[tuple[int, str, str, str]] = []
    finite_anchor: int | None = None
    modal_ref: int | None = None
    perfect_aux_ref: int | None = None
    progressive_aux_ref: int | None = None
    passive_aux_ref: int | None = None

    for aux in sorted(predicate.auxiliaries, key=lambda a: a.ref):
        word = ctx.word_by_ref[aux.ref]
        surface = word.text
        lemma = aux.lemma
        role = aux.role
        if role == "modal":
            modal_ref = aux.ref
            finite_anchor = finite_anchor or aux.ref
        elif lemma == "have":
            perfect_aux_ref = aux.ref
            if finite_anchor is None:
                finite_anchor = aux.ref
        elif lemma == "be":
            if surface.casefold() == "been":
                resolved_role = _role_for_been(predicate.auxiliaries, main_form)
                if resolved_role == "passive_aux":
                    passive_aux_ref = aux.ref
                else:
                    progressive_aux_ref = aux.ref
            elif surface.casefold() == "being":
                passive_aux_ref = aux.ref
            else:
                # finite be (am/is/are/was/were)
                if main_form == "VBG":
                    progressive_aux_ref = aux.ref
                elif main_form == "VBN" and role == "passive_aux":
                    passive_aux_ref = aux.ref
                if finite_anchor is None:
                    finite_anchor = aux.ref
        ordered_items.append((aux.ref, surface, lemma, role))

    # Append main verb
    ordered_items.append(
        (
            predicate.main,
            ctx.word_by_ref[predicate.main].text,
            predicate.main_lemma,
            "main",
        )
    )

    ordered_refs = tuple(item[0] for item in ordered_items)
    ordered_surfaces = tuple(item[1] for item in ordered_items)
    ordered_lemmas = tuple(item[2] for item in ordered_items)

    return AuxChain(
        chain_signature=_chain_signature(ordered_items[:-1], main_form),
        ordered_refs=ordered_refs,
        ordered_lemmas=ordered_lemmas,
        ordered_surfaces=ordered_surfaces,
        main_ref=predicate.main,
        main_verb_form=main_form,
        finite_anchor_ref=finite_anchor,
        modal_ref=modal_ref,
        perfect_aux_ref=perfect_aux_ref,
        progressive_aux_ref=progressive_aux_ref,
        passive_aux_ref=passive_aux_ref,
    )


def build_aux_chains_for_predicates(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[PredicateFeature, ...]:
    """Return a new tuple of predicates with `aux_chain` populated."""
    from dataclasses import replace

    return tuple(
        replace(predicate, aux_chain=build_aux_chain(ctx, predicate))
        for predicate in predicates
    )


__all__ = ["build_aux_chain", "build_aux_chains_for_predicates"]
