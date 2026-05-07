from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    ClauseFeature,
    NPFeature,
    RelativeClauseFeature,
    RelativeMarkerText,
    RelativeRole,
    RelativeType,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

_RELATIVE_MARKERS: dict[str, RelativeMarkerText] = {
    "who": "who",
    "whom": "whom",
    "whose": "whose",
    "which": "which",
    "that": "that",
    "where": "where",
    "when": "when",
}


def build_relative_clauses(
    ctx: SentenceContext,
    clauses: tuple[ClauseFeature, ...],
    np_profiles: tuple[NPFeature, ...] = (),
) -> tuple[RelativeClauseFeature, ...]:
    items: list[RelativeClauseFeature] = []
    next_id = 1
    for clause in clauses:
        if clause.type not in {"relcl", "acl"}:
            continue
        head_word = ctx.word_by_ref[clause.head]
        head_noun = head_word.head if head_word.head != 0 else clause.head
        marker_ref, marker_text = _find_marker(ctx, clause.head)
        relative_type = _relative_type(ctx, clause, marker_ref, marker_text)
        role = _relative_role(ctx, marker_ref, marker_text, relative_type)
        object_gap = _object_gap(clause, marker_ref, role)
        if object_gap is True and role == "unknown":
            role = "object"
        if marker_ref is None and clause.type == "acl" and object_gap is not True:
            continue
        evidence_set = {head_noun, clause.head, *clause.local_tokens}
        if marker_ref is not None:
            evidence_set.add(marker_ref)
        evidence_refs = tuple(sorted(evidence_set))
        items.append(
            RelativeClauseFeature(
                id=f"relcl-{next_id}",
                clause_id=clause.id,
                antecedent_np_id=_np_id_for_head(np_profiles, head_noun),
                head_noun=head_noun,
                relative_marker=marker_ref,
                marker_text=marker_text,
                relative_role=role,
                object_gap=object_gap,
                is_omitted_relative_pronoun=marker_ref is None and object_gap is True,
                defining_status="defining",
                comma_delimited=False,
                relative_type=relative_type,
                restrictive=None,
                source="heuristic",
                evidence_refs=evidence_refs,
                confidence="medium" if marker_ref is not None or object_gap else "low",
            )
        )
        next_id += 1
    return tuple(items)


def _find_marker(
    ctx: SentenceContext,
    clause_head: int,
) -> tuple[int | None, RelativeMarkerText | None]:
    for child in ctx.children_by_head.get(clause_head, ()):
        word = ctx.word_by_ref[child]
        surface = word.text.casefold()
        if surface in _RELATIVE_MARKERS and word.deprel in {
            "nsubj",
            "nsubj:pass",
            "obj",
            "nmod:poss",
            "advmod",
            "obl",
            "mark",
        }:
            return child, _RELATIVE_MARKERS[surface]
    return None, None


def _relative_type(
    ctx: SentenceContext,
    clause: ClauseFeature,
    marker_ref: int | None,
    marker_text: RelativeMarkerText | None,
) -> RelativeType:
    if marker_text == "where":
        return "place_relative"
    if marker_text == "whose" or (
        marker_ref is not None
        and ctx.word_by_ref[marker_ref].deprel == "nmod:poss"
    ):
        return "possessive_relative"
    if marker_ref is not None:
        deprel = ctx.word_by_ref[marker_ref].deprel
        if deprel in {"nsubj", "nsubj:pass"}:
            return "subject_relative"
        if deprel in {"obj", "obl"}:
            return "object_relative"
    head_word = ctx.word_by_ref[clause.head]
    if head_word.upos == "VERB":
        feats = ctx.morph_by_ref[clause.head].features
        if feats.get("VerbForm") == "Part":
            return "reduced_participle_relative"
        if feats.get("VerbForm") == "Inf":
            return "reduced_to_infinitive_relative"
    return "unknown"


def _relative_role(
    ctx: SentenceContext,
    marker_ref: int | None,
    marker_text: RelativeMarkerText | None,
    relative_type: RelativeType,
) -> RelativeRole:
    if marker_text == "whose":
        return "possessive"
    if marker_text in {"where", "when"}:
        return "oblique"
    if marker_ref is not None:
        deprel = ctx.word_by_ref[marker_ref].deprel
        if deprel in {"nsubj", "nsubj:pass"}:
            return "subject"
        if deprel == "obj":
            return "object"
        if deprel in {"obl", "advmod"}:
            return "oblique"
    if relative_type == "object_relative":
        return "object"
    if relative_type == "subject_relative":
        return "subject"
    return "unknown"


def _object_gap(
    clause: ClauseFeature,
    marker_ref: int | None,
    role: RelativeRole,
) -> bool | None:
    if marker_ref is not None:
        return False
    if role == "object":
        return True
    if clause.roles.object is None and clause.roles.subject is not None:
        return True
    return None


def _np_id_for_head(np_profiles: tuple[NPFeature, ...], head: int) -> str | None:
    for np in np_profiles:
        if np.head == head:
            return np.id
    return None


__all__ = ["build_relative_clauses"]
