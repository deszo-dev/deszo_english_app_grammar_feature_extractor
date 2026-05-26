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
                    severity="warning",
                    code="unknown_predicate_type",
                    message=(
                        "Predicate type could not be classified from local evidence."
                    ),
                    refs=(predicate.main,),
                    feature_path="syntax.predicates",
                )
            )
        main_morph = ctx.morph_by_ref[predicate.main].features
        if (
            predicate.form_signature == "unknown"
            and main_morph.get("VerbForm") in {"Part", "Ger", "Inf"}
            and not predicate.finite
        ):
            diagnostics.append(
                FeatureDiagnostic(
                    severity="info",
                    code="non_finite_clause_candidate",
                    message=(
                        "Non-finite verb form was kept as a candidate instead of "
                        "being emitted as a finite tense-aspect construction."
                    ),
                    refs=(predicate.main,),
                    feature_path="syntax.predicates",
                )
            )
    _fragment_diagnostic(ctx, predicates, diagnostics)
    for np in np_profiles:
        if np.article_slot.requiredness == "not_applicable":
            diagnostics.append(
                FeatureDiagnostic(
                    severity="info",
                    code="article_slot_not_applicable",
                    message="Article slot is not applicable for this NP type.",
                    refs=(np.head,),
                    feature_path="syntax.np_profiles.article_slot",
                )
            )
        elif (
            np.article_slot.requiredness == "unknown"
            and np.phrase_type == "common_noun_np"
        ):
            diagnostics.append(
                FeatureDiagnostic(
                    severity="info",
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
                    severity="info",
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
    text = ctx.text.strip()
    root_word = ctx.word_by_ref[root]
    if root_word.upos not in {"VERB", "AUX", "ADJ"}:
        code = "fragment_non_predicative_root"
        if _looks_like_heading(text, ctx):
            code = "heading_fragment"
        elif _looks_like_address_or_date(ctx):
            code = "address_or_date_fragment"
        elif text.startswith(('"', "'")) or text.endswith(('"', "'")):
            code = "quoted_speech_fragment"
        diagnostics.append(
            FeatureDiagnostic(
                severity="info",
                code=code,
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
                code="possible_parser_error",
                message="Only low-confidence predicate evidence was available.",
                refs=(root,),
                feature_path="syntax.predicates",
            )
        )


def _looks_like_heading(text: str, ctx: SentenceContext) -> bool:
    return (
        text.endswith(".")
        and len(ctx.refs) <= 5
        and not any(word.upos in {"VERB", "AUX"} for word in ctx.words)
    )


def _looks_like_address_or_date(ctx: SentenceContext) -> bool:
    month_tokens = {
        "jan",
        "january",
        "feb",
        "february",
        "mar",
        "march",
        "apr",
        "april",
        "may",
        "jun",
        "june",
        "jul",
        "july",
        "aug",
        "august",
        "sep",
        "sept",
        "september",
        "oct",
        "october",
        "nov",
        "november",
        "dec",
        "december",
    }
    lowers = {word.text.strip(".,").casefold() for word in ctx.words}
    return bool(lowers & month_tokens)
