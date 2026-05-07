from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    ClauseFeature,
    PredicateFeature,
    ReportedSpeechFeature,
    ReportType,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

REPORTING_VERBS = frozenset(
    {
        "say",
        "tell",
        "ask",
        "answer",
        "reply",
        "report",
        "claim",
        "explain",
        "mention",
        "state",
        "suggest",
        "warn",
        "promise",
        "advise",
        "order",
        "command",
        "request",
        "wonder",
        "think",
        "believe",
        "know",
        "guess",
        "hope",
        "doubt",
    }
)
_WH_MARKERS = frozenset(
    {"what", "who", "whom", "whose", "which", "when", "where", "why", "how"}
)


def build_reported_speech_features(
    ctx: SentenceContext,
    predicates: tuple[PredicateFeature, ...],
    clauses: tuple[ClauseFeature, ...],
) -> tuple[ReportedSpeechFeature, ...]:
    items: list[ReportedSpeechFeature] = []
    clause_by_head = {clause.head: clause for clause in clauses}
    for predicate in predicates:
        if predicate.main_lemma not in REPORTING_VERBS:
            continue
        complement_clause = _find_reported_complement(ctx, predicate, clause_by_head)
        if complement_clause is None:
            continue
        marker_ref, report_type = _classify_marker(ctx, complement_clause)
        backshift = _backshift_candidate(predicate, complement_clause)
        speakers = _speakers(predicate)
        items.append(
            ReportedSpeechFeature(
                reporting_verb=predicate.main,
                reported_clause_head=complement_clause.head,
                marker=marker_ref,
                report_type=report_type,
                backshift_candidate=backshift,
                speaker_or_addressee_refs=speakers,
                confidence="medium",
            )
        )
    return tuple(items)


def _find_reported_complement(
    ctx: SentenceContext,
    predicate: PredicateFeature,
    clause_by_head: dict[int, ClauseFeature],
) -> ClauseFeature | None:
    for child in ctx.children_by_head.get(predicate.main, ()):
        word = ctx.word_by_ref[child]
        if word.deprel in {"ccomp", "xcomp"} and child in clause_by_head:
            return clause_by_head[child]
    return None


def _classify_marker(
    ctx: SentenceContext,
    clause: ClauseFeature,
) -> tuple[int | None, ReportType]:
    if clause.marker is not None:
        marker_surface = clause.marker.marker.casefold()
        if marker_surface == "that":
            return clause.marker.marker_ref, "that_clause"
        if marker_surface in _WH_MARKERS:
            return clause.marker.marker_ref, "reported_question"
        if marker_surface == "to":
            return clause.marker.marker_ref, "reported_command"
    head_word = ctx.word_by_ref[clause.head]
    feats = ctx.morph_by_ref[clause.head].features
    if feats.get("VerbForm") == "Inf":
        return None, "reported_command"
    if head_word.text.startswith(('"', '“', "'", "‘")):
        return None, "direct_quote"
    return None, "that_clause"


def _backshift_candidate(
    reporting: PredicateFeature,
    reported: ClauseFeature,
) -> bool:
    if reporting.tense != "past":
        return False
    return reported.predicate is not None


def _speakers(predicate: PredicateFeature) -> tuple[int, ...]:
    refs: list[int] = []
    if predicate.subject is not None:
        refs.append(predicate.subject)
    if predicate.indirect_object is not None:
        refs.append(predicate.indirect_object)
    return tuple(sorted(set(refs)))


__all__ = ["build_reported_speech_features", "REPORTING_VERBS"]
