from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    FeatureDiagnostic,
    NPFeature,
    PredicateFeature,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext


def add_baseline_diagnostics(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
    np_profiles: tuple[NPFeature, ...],
    diagnostics: list[FeatureDiagnostic],
) -> None:
    for predicate in predicates:
        if predicate.predicate_type == "unknown":
            diagnostics.append(
                FeatureDiagnostic(
                    severity="info",
                    code="competing_rule_candidates",
                    message=(
                        "Predicate type could not be classified from local evidence."
                    ),
                    refs=(predicate.main,),
                    feature_path="syntax.predicates",
                )
            )
    _fragment_diagnostic(ctx, predicates, diagnostics)
    for np in np_profiles:
        if (
            np.article_slot.requiredness == "unknown"
            and np.phrase_type == "common_noun_np"
        ):
            diagnostics.append(
                FeatureDiagnostic(
                    severity="warning",
                    code="requires_countability_lexicon",
                    message=(
                        "Article requiredness needs countability or reference support."
                    ),
                    refs=(np.head,),
                    feature_path="syntax.np_profiles.article_slot",
                )
            )
        if np.article_slot.article_form in {"a", "an"}:
            refs = (
                (np.determiner.ref, np.head)
                if np.determiner is not None
                else (np.head,)
            )
            diagnostics.append(
                FeatureDiagnostic(
                    severity="warning",
                    code="requires_phonology",
                    message="A/an correctness requires phonology support.",
                    refs=refs,
                    feature_path="syntax.np_profiles.article_slot",
                )
            )


def _fragment_diagnostic(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
    diagnostics: list[FeatureDiagnostic],
) -> None:
    root = next((ref for ref in ctx.refs if ctx.word_by_ref[ref].head == 0), None)
    if root is None:
        return
    root_word = ctx.word_by_ref[root]
    if root_word.upos not in {"VERB", "AUX", "ADJ"}:
        diagnostics.append(
            FeatureDiagnostic(
                severity="warning",
                code="unsupported_feature",
                message=(
                    "Sentence appears to be a non-predicative or parser-degraded "
                    "fragment."
                ),
                refs=(root,),
                feature_path="syntax.clauses",
            )
        )
    if predicates and all(predicate.confidence == "low" for predicate in predicates):
        diagnostics.append(
            FeatureDiagnostic(
                severity="warning",
                code="ambiguous_pos",
                message="Only low-confidence predicate evidence was available.",
                refs=(root,),
                feature_path="syntax.predicates",
            )
        )
