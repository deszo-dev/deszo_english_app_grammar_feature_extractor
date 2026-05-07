from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    ClauseFeature,
    Confidence,
    LexicalItemFeature,
    NegationFeature,
    NegationScope,
    NegationType,
    NegatorType,
    Polarity,
    PredicateFeature,
    ProofSource,
    QuestionType,
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
STRICT_NEGATORS = frozenset(
    {"not", "n't", "never", "no", "none", "nothing", "nobody", "neither", "nowhere"}
)
NEGATIVE_LIKE_ADVERBS = frozenset({"scarcely", "hardly"})
NEGATIVE_COORDINATORS = frozenset({"nor"})
CONTRACTION_SUFFIXES = ("n't", "'m", "'re", "'ve", "'ll", "'s", "'d")
DISCOURSE_MARKERS = frozenset(
    {"certainly", "therefore", "however", "but", "then", "indeed", "well"}
)
MONTH_NAMES = frozenset(
    {
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
        "yesterday",
        "today",
        "tomorrow",
        "now",
        "soon",
        "again",
    }
)


def build_sentence_feature(
    ctx: SentenceContext,
    clauses: tuple[ClauseFeature, ...],
    predicates: tuple[PredicateFeature, ...],
) -> SentenceFeature:
    text = ctx.text.rstrip()
    negative_count = sum(
        1 for predicate in predicates if predicate.polarity == "negative"
    )
    mixed_count = sum(1 for predicate in predicates if predicate.polarity == "mixed")
    positive_count = sum(
        1 for predicate in predicates if predicate.polarity == "positive"
    )
    has_subject_aux_inversion = _has_subject_aux_inversion(ctx)
    lower_words = tuple(word.text.casefold() for word in ctx.words)
    sentence_type = _sentence_type(ctx, has_subject_aux_inversion)
    has_wh_fronting = _has_wh_fronting(lower_words)
    return SentenceFeature(
        sentence_kind=_sentence_kind(ctx),
        clause_count=len(clauses),
        sentence_type=sentence_type,
        terminal_punctuation=_terminal_punctuation(text),
        terminal_question_mark=text.endswith("?"),
        question_type=_question_type(sentence_type),
        polarity=_sentence_polarity(negative_count, mixed_count, positive_count),
        has_subject_aux_inversion=has_subject_aux_inversion,
        has_do_support=any(
            auxiliary.role == "do_support"
            for predicate in predicates
            for auxiliary in predicate.auxiliaries
        ),
        has_wh_fronting=has_wh_fronting,
        has_tag_question=False,
        has_exclamation_marker=text.endswith("!"),
        sentence_type_confidence="high" if sentence_type != "unknown" else "low",
        evidence_refs=ctx.refs,
    )


def build_word_order(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
) -> tuple[WordOrderFeature, ...]:
    items: list[WordOrderFeature] = []
    lower_words = tuple(word.text.casefold() for word in ctx.words)
    wh_fronted = bool(lower_words and lower_words[0] in WH_WORDS)
    for predicate in predicates:
        refs, slots = _predicate_order_refs(predicate)
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
                ordered_refs=refs,
                slots=slots,
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
    predicate_by_ref = {
        ref: predicate
        for predicate in predicates
        for ref in (predicate.main, *(aux.ref for aux in predicate.auxiliaries))
    }
    emitted: set[int] = set()
    for predicate in predicates:
        if predicate.negation is None:
            continue
        emitted.add(predicate.negation)
        negator = _negator(ctx.word_by_ref[predicate.negation].text.casefold())
        items.append(
            NegationFeature(
                ref=predicate.negation,
                negator=negator,
                negation_type=_negation_type(negator),
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
    for ref in ctx.refs:
        if ref in emitted:
            continue
        lower = ctx.word_by_ref[ref].text.casefold()
        lemma = (ctx.word_by_ref[ref].lemma or ctx.word_by_ref[ref].text).casefold()
        negator = _negator(lower)
        if negator == "unknown" and _is_negative_morph(ctx, ref):
            negator = _negator(lemma)
        if negator == "unknown":
            continue
        owner = _owning_predicate(ctx, ref, predicate_by_ref)
        negation_type = _negation_type(negator)
        scope: NegationScope = "predicate" if owner is not None else "unknown"
        if negation_type == "negative_determiner":
            scope = "noun_phrase"
        if negation_type == "negative_coordinator" and owner is None:
            scope = "unknown"
        confidence: Confidence = (
            "medium" if negation_type == "negative_like_adverb" else "high"
        )
        source: ProofSource = (
            "discourse_heuristic"
            if negation_type == "negative_like_adverb"
            else "surface"
        )
        refs = (ref,) if owner is None else (ref, owner.main)
        items.append(
            NegationFeature(
                ref=ref,
                negator=negator,
                negation_type=negation_type,
                scope=scope,
                governor=owner.main if owner is not None else None,
                confidence=confidence,
                provenance=make_provenance("heuristic", source, refs, confidence),
            )
        )
    return tuple(items)


def build_lexical_items(
    ctx: SentenceContext,
) -> dict[str, tuple[LexicalItemFeature, ...]]:
    return {
        "time_markers": tuple(_time_markers(ctx)),
        "comparisons": tuple(_comparisons(ctx)),
        "phrasal_verbs": tuple(_phrasal_verbs(ctx)),
        "discourse_markers": tuple(_discourse_markers(ctx)),
        "contractions": tuple(_contractions(ctx)),
        "noun_inflections": tuple(_noun_inflections(ctx)),
    }


def _predicate_order_refs(
    predicate: PredicateFeature,
) -> tuple[tuple[int, ...], dict[str, int]]:
    slots: dict[str, int] = {"predicate": predicate.main}
    if predicate.subject is not None:
        slots["subject"] = predicate.subject
    if predicate.copula is not None:
        slots["copula"] = predicate.copula
        slots["complement"] = predicate.main
        return (
            _unique_order(
                predicate.subject,
                predicate.copula,
                predicate.main,
            ),
            slots,
        )
    first_aux = predicate.auxiliaries[0].ref if predicate.auxiliaries else None
    if first_aux is not None:
        slots["auxiliary"] = first_aux
    if predicate.object is not None:
        slots["object"] = predicate.object
    if predicate.negation is not None:
        slots["negation"] = predicate.negation
    if first_aux is not None and predicate.negation is not None:
        return (
            _unique_order(
                predicate.subject,
                first_aux,
                predicate.negation,
                predicate.main,
                predicate.object,
            ),
            slots,
        )
    if first_aux is not None:
        return (
            _unique_order(
                predicate.subject,
                first_aux,
                predicate.main,
                predicate.object,
            ),
            slots,
        )
    return _unique_order(predicate.subject, predicate.main, predicate.object), slots


def _unique_order(*refs: int | None) -> tuple[int, ...]:
    ordered: list[int] = []
    for ref in refs:
        if ref is not None and ref not in ordered:
            ordered.append(ref)
    return tuple(ordered)


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
        if _has_wh_fronting(lower_words):
            return "wh_question"
        if has_subject_aux_inversion:
            return "yes_no_question"
        return "unknown"
    if text.endswith("!"):
        return "exclamative"
    if not any(word.upos in {"VERB", "AUX"} for word in ctx.words):
        return "fragment"
    return "declarative"


def _terminal_punctuation(text: str) -> str:
    if text.endswith("?"):
        return "?"
    if text.endswith("!"):
        return "!"
    if text.endswith("."):
        return "."
    return "none"


def _has_wh_fronting(lower_words: tuple[str, ...]) -> bool:
    if not lower_words:
        return False
    if lower_words[0] in WH_WORDS:
        return True
    if len(lower_words) > 1 and lower_words[0] in {"pray", "well"}:
        return lower_words[1] in WH_WORDS
    return False


def _question_type(sentence_type: SentenceType) -> QuestionType:
    if sentence_type == "wh_question":
        return "wh"
    if sentence_type == "yes_no_question":
        return "yes_no"
    if sentence_type == "tag_question":
        return "tag"
    return "none"


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
    if value == "nobody":
        return "nobody"
    if value == "neither":
        return "neither"
    if value == "nor":
        return "nor"
    if value == "nowhere":
        return "nowhere"
    if value == "scarcely":
        return "scarcely"
    if value == "hardly":
        return "hardly"
    return "unknown"


def _negation_type(negator: NegatorType) -> NegationType:
    if negator == "no":
        return "negative_determiner"
    if negator in {"none", "nothing", "nobody", "nowhere"}:
        return "negative_pronoun"
    if negator == "nor":
        return "negative_coordinator"
    if negator in {"scarcely", "hardly"}:
        return "negative_like_adverb"
    if negator != "unknown":
        return "strict_negator"
    return "unknown"


def _is_negative_morph(ctx: SentenceContext, ref: int) -> bool:
    features = ctx.morph_by_ref[ref].features
    return features.get("Polarity") == "Neg" or features.get("PronType") == "Neg"


def _owning_predicate(
    ctx: SentenceContext,
    ref: int,
    predicate_by_ref: dict[int, PredicateFeature],
) -> PredicateFeature | None:
    head = ctx.word_by_ref[ref].head
    if head in predicate_by_ref:
        return predicate_by_ref[head]
    if head != 0:
        grand_head = ctx.word_by_ref[head].head
        if grand_head in predicate_by_ref:
            return predicate_by_ref[grand_head]
    if ref in predicate_by_ref:
        return predicate_by_ref[ref]
    return None


def _sentence_polarity(
    negative_count: int,
    mixed_count: int,
    positive_count: int,
) -> Polarity:
    if mixed_count:
        return "mixed"
    if negative_count and positive_count:
        return "mixed"
    if negative_count:
        return "negative"
    return "positive"


def _time_markers(ctx: SentenceContext) -> list[LexicalItemFeature]:
    items: list[LexicalItemFeature] = []
    for ref in ctx.refs:
        lower = ctx.word_by_ref[ref].text.strip(".").casefold()
        if lower in MONTH_NAMES or lower.isdigit():
            confidence: Confidence = "high" if lower in MONTH_NAMES else "medium"
            items.append(_lexical_item(ctx, "time_marker", (ref,), confidence))
    return items


def _comparisons(ctx: SentenceContext) -> list[LexicalItemFeature]:
    items: list[LexicalItemFeature] = []
    for ref in ctx.refs:
        lower = ctx.word_by_ref[ref].text.casefold()
        features = ctx.morph_by_ref[ref].features
        if features.get("Degree") in {"Cmp", "Sup"} or lower in {
            "more",
            "most",
            "less",
            "least",
        }:
            items.append(_lexical_item(ctx, "comparison", (ref,), "high"))
    lowers = {ctx.word_by_ref[ref].text.casefold() for ref in ctx.refs}
    if "as" in lowers:
        as_refs = tuple(
            ref for ref in ctx.refs if ctx.word_by_ref[ref].text.casefold() == "as"
        )
        if len(as_refs) >= 2:
            items.append(_lexical_item(ctx, "comparison_as_as", as_refs[:2], "medium"))
    return items


def _phrasal_verbs(ctx: SentenceContext) -> list[LexicalItemFeature]:
    return [
        _lexical_item(
            ctx,
            "phrasal_verb_particle",
            (ctx.word_by_ref[ref].head, ref),
            "high",
        )
        for ref in ctx.refs
        if ctx.word_by_ref[ref].deprel == "compound:prt"
        and ctx.word_by_ref[ref].head != 0
    ]


def _discourse_markers(ctx: SentenceContext) -> list[LexicalItemFeature]:
    return [
        _lexical_item(ctx, "discourse_marker", (ref,), "medium")
        for ref in ctx.refs
        if ctx.word_by_ref[ref].text.strip(",.").casefold() in DISCOURSE_MARKERS
    ]


def _contractions(ctx: SentenceContext) -> list[LexicalItemFeature]:
    return [
        _lexical_item(ctx, "contraction", (ref,), "high")
        for ref in ctx.refs
        if ctx.word_by_ref[ref].text.casefold().endswith(CONTRACTION_SUFFIXES)
    ]


def _noun_inflections(ctx: SentenceContext) -> list[LexicalItemFeature]:
    items: list[LexicalItemFeature] = []
    for ref in ctx.refs:
        normalized = ctx.normalized_morph_by_ref[ref]
        if normalized.is_plural_noun:
            items.append(_lexical_item(ctx, "plural_noun", (ref,), "high"))
        elif normalized.is_singular_noun:
            items.append(_lexical_item(ctx, "singular_noun", (ref,), "high"))
    return items


def _lexical_item(
    ctx: SentenceContext,
    kind: str,
    refs: tuple[int, ...],
    confidence: Confidence,
) -> LexicalItemFeature:
    text = " ".join(ctx.word_by_ref[ref].text for ref in refs)
    return LexicalItemFeature(
        kind=kind,
        refs=refs,
        text=text,
        confidence=confidence,
        provenance=make_provenance("deterministic", "surface", refs, confidence),
    )
