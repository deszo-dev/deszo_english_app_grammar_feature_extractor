from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    ClauseFeature,
    NegationFeature,
    NegatorType,
    PredicateFeature,
    SentenceFeature,
    SentenceKind,
    SentenceType,
    WordOrderFeature,
    WordOrderPattern,
)
from grammar_feature_extractor._internal.proof_surface import make_provenance
from grammar_feature_extractor._internal.sentence_context import SentenceContext

WH_WORDS = frozenset(
    {"what", "who", "whom", "whose", "which", "when", "where", "why", "how"}
)


def build_sentence_feature(
    ctx: SentenceContext,
    clauses: tuple[ClauseFeature, ...],
    predicates: tuple[PredicateFeature, ...],
) -> SentenceFeature:
    text = ctx.text.rstrip()
    has_negation = any(predicate.polarity == "negative" for predicate in predicates)
    has_subject_aux_inversion = _has_subject_aux_inversion(ctx)
    lower_words = tuple(word.text.casefold() for word in ctx.words)
    return SentenceFeature(
        sentence_kind=_sentence_kind(ctx),
        clause_count=len(clauses),
        sentence_type=_sentence_type(ctx, has_subject_aux_inversion),
        polarity="negative" if has_negation else "positive",
        has_subject_aux_inversion=has_subject_aux_inversion,
        has_do_support=any(
            auxiliary.role == "do_support"
            for predicate in predicates
            for auxiliary in predicate.auxiliaries
        ),
        has_wh_fronting=bool(lower_words and lower_words[0] in WH_WORDS),
        has_tag_question=False,
        has_exclamation_marker=text.endswith("!"),
    )


def build_word_order(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[WordOrderFeature, ...]:
    items: list[WordOrderFeature] = []
    lower_words = tuple(word.text.casefold() for word in ctx.words)
    wh_fronted = bool(lower_words and lower_words[0] in WH_WORDS)
    for predicate in predicates:
        refs = _predicate_order_refs(predicate)
        if not refs:
            continue
        pattern: WordOrderPattern = "unknown"
        if predicate.copula is not None and predicate.subject is not None:
            pattern = (
                "be_subject_complement"
                if predicate.subject < predicate.copula
                else "aux_subject_verb"
            )
        elif predicate.subject is not None and predicate.object is not None:
            pattern = "subject_verb_object"
        elif predicate.subject is not None and predicate.auxiliaries:
            first_aux = predicate.auxiliaries[0].ref
            if wh_fronted and first_aux < predicate.subject:
                pattern = "wh_aux_subject_verb"
            elif first_aux < predicate.subject:
                pattern = "aux_subject_verb"
            else:
                pattern = "subject_aux_verb"
        if predicate.negation is not None and predicate.auxiliaries:
            pattern = "negative_aux_not_verb"
        items.append(
            WordOrderFeature(
                pattern=pattern,
                ordered_refs=tuple(sorted(refs)),
                confidence="high" if pattern != "unknown" else "low",
                provenance=make_provenance(
                    "deterministic",
                    "word_order",
                    refs,
                    "high" if pattern != "unknown" else "low",
                ),
            )
        )
    return tuple(items)


def build_negation(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[NegationFeature, ...]:
    items: list[NegationFeature] = []
    for predicate in predicates:
        if predicate.negation is None:
            continue
        negator = _negator(ctx.word_by_ref[predicate.negation].text.casefold())
        items.append(
            NegationFeature(
                ref=predicate.negation,
                negator=negator,
                scope="predicate",
                governor=predicate.main,
                confidence="high",
                provenance=make_provenance(
                    "deterministic",
                    "dependency",
                    (predicate.negation, predicate.main),
                    "high",
                ),
            )
        )
    return tuple(items)


def _predicate_order_refs(predicate: PredicateFeature) -> tuple[int, ...]:
    refs = [predicate.main]
    if predicate.subject is not None:
        refs.append(predicate.subject)
    if predicate.object is not None:
        refs.append(predicate.object)
    refs.extend(auxiliary.ref for auxiliary in predicate.auxiliaries)
    if predicate.copula is not None:
        refs.append(predicate.copula)
    if predicate.negation is not None:
        refs.append(predicate.negation)
    return tuple(refs)


def _sentence_kind(ctx: SentenceContext) -> SentenceKind:
    text = ctx.text.strip()
    if text.startswith(('"', "'")) and text.endswith(('"', "'")):
        return "quote"
    if any(word.upos in {"VERB", "AUX"} for word in ctx.words):
        return "normal"
    if text.endswith("!"):
        return "exclamation_fragment"
    if len(ctx.words) <= 8:
        return "fragment"
    return "unknown"


def _sentence_type(
    ctx: SentenceContext,
    has_subject_aux_inversion: bool,
) -> SentenceType:
    text = ctx.text.rstrip()
    lower_words = tuple(word.text.casefold() for word in ctx.words)
    if text.endswith("?"):
        if lower_words and lower_words[0] in WH_WORDS:
            return "wh_question"
        if has_subject_aux_inversion:
            return "yes_no_question"
        return "unknown"
    if text.endswith("!"):
        return "exclamative"
    if not any(word.upos in {"VERB", "AUX"} for word in ctx.words):
        return "fragment"
    return "declarative"


def _has_subject_aux_inversion(ctx: SentenceContext) -> bool:
    aux_positions = tuple(ref for ref in ctx.refs if ctx.word_by_ref[ref].upos == "AUX")
    subjects = tuple(
        ref
        for ref in ctx.refs
        if ctx.word_by_ref[ref].deprel in {"nsubj", "nsubj:pass"}
    )
    return bool(subjects and aux_positions and min(aux_positions) < min(subjects))


def _negator(value: str) -> NegatorType:
    if value == "not":
        return "not"
    if value == "n't":
        return "n't"
    if value == "never":
        return "never"
    if value == "no":
        return "no"
    if value == "none":
        return "none"
    if value == "nothing":
        return "nothing"
    if value == "neither":
        return "neither"
    return "unknown"
