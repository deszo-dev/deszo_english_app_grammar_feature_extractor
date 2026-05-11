from __future__ import annotations

from grammar_feature_extractor._internal.features.dependency_helpers import (
    local_clause_tokens,
    subtree_tokens,
)
from grammar_feature_extractor._internal.features.subordination_builder import (
    marker_by_clause_head,
)
from grammar_feature_extractor._internal.models import (
    ClauseFeature,
    ClauseMarkerFeature,
    ClauseType,
    FeatureDiagnostic,
    Roles,
    SemanticRelation,
    Valency,
    WordRef,
)
from grammar_feature_extractor._internal.proof_surface import make_provenance
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def build_clauses(
    ctx: SentenceContext,
    markers: tuple[ClauseMarkerFeature, ...],
    diagnostics: list[FeatureDiagnostic],
) -> tuple[ClauseFeature, ...]:
    clause_heads = tuple(
        ref for ref in ctx.refs if _clause_type(ctx.word_by_ref[ref].deprel)
    )
    marker_map = marker_by_clause_head(markers)
    clauses: list[ClauseFeature] = []
    for ref in clause_heads:
        tokens, subtree_cycle_refs = subtree_tokens(ctx, ref)
        local_tokens, local_cycle_refs = local_clause_tokens(ctx, ref, clause_heads)
        cycle_refs = tuple(
            sorted(dict.fromkeys((*subtree_cycle_refs, *local_cycle_refs)))
        )
        if cycle_refs:
            diagnostics.append(
                FeatureDiagnostic(
                    severity="error",
                    code="internal_feature_error",
                    message=(
                        "Dependency cycle detected while collecting clause " "subtree."
                    ),
                    refs=cycle_refs,
                    feature_path="syntax.clauses",
                )
            )
        roles = _roles(ctx, local_tokens)
        marker = marker_map.get(ref)
        clauses.append(
            ClauseFeature(
                id=f"clause-{ref}",
                head=ref,
                type=_clause_type(ctx.word_by_ref[ref].deprel) or "unknown",
                finite=ctx.normalized_morph_by_ref[ref].is_finite_verb,
                subject=roles.subject,
                predicate=ref,
                marker=marker,
                roles=roles,
                valency=Valency(
                    subject=roles.subject is not None,
                    object=roles.object is not None,
                    indirect_object=roles.indirect_object is not None,
                ),
                semantic_relation=_semantic_relation(marker),
                tokens=tokens,
                local_tokens=local_tokens,
                confidence="high",
                provenance=make_provenance(
                    "deterministic", "dependency", tokens, "high"
                ),
            )
        )
    return tuple(clauses)


def _roles(ctx: SentenceContext, local_tokens: tuple[WordRef, ...]) -> Roles:
    subject = _first_ref_with_deprel(ctx, local_tokens, {"nsubj", "nsubj:pass"})
    object_ref = _first_ref_with_deprel(ctx, local_tokens, {"obj"})
    indirect = _first_ref_with_deprel(ctx, local_tokens, {"iobj"})
    oblique = tuple(ref for ref in local_tokens if ctx.word_by_ref[ref].deprel == "obl")
    return Roles(
        subject=subject,
        object=object_ref,
        indirect_object=indirect,
        oblique=oblique,
    )


def _first_ref_with_deprel(
    ctx: SentenceContext,
    refs: tuple[WordRef, ...],
    deprels: set[str],
) -> WordRef | None:
    matches = tuple(ref for ref in refs if ctx.word_by_ref[ref].deprel in deprels)
    return matches[0] if matches else None


def _clause_type(deprel: str) -> ClauseType | None:
    if deprel == "root":
        return "root"
    if deprel == "acl:relcl":
        return "relcl"
    if deprel == "ccomp":
        return "ccomp"
    if deprel == "xcomp":
        return "xcomp"
    if deprel == "advcl":
        return "advcl"
    if deprel == "acl":
        return "acl"
    return None


def _semantic_relation(marker: ClauseMarkerFeature | None) -> SemanticRelation | None:
    if marker is None:
        return None
    if marker.marker_type in {"conditional_if", "conditional_unless"}:
        return "condition"
    if marker.marker_type == "relative_pronoun":
        return "relative"
    if marker.marker_type == "reported_that":
        return "reported_content"
    return "unknown"
