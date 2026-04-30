from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CorpusMetrics:
    corpus: str
    files: int = 0
    sentences: int = 0
    slot_zero_count: int = 0
    invalid_slot_refs: int = 0
    duplicate_feature_ids: int = 0
    construction_empty_evidence_refs: int = 0
    invalid_absence_anchor_refs: int = 0
    word_order_duplicate_ordered_refs: int = 0
    negation_evidence_sentences: int = 0
    lexical_negation_count: int = 0
    predicate_negative_count: int = 0
    sentence_negative_or_mixed_count: int = 0
    pronoun_missing_required_determiner: int = 0
    proper_noun_missing_required_determiner: int = 0
    diagnostics_count: int = 0
    lexical_contractions_count: int = 0
    lexical_phrasal_verbs_count: int = 0
    lexical_comparisons_count: int = 0
    lexical_time_markers_count: int = 0
    lexical_discourse_markers_count: int = 0


def collect_results_metrics(results_dir: Path) -> dict[str, CorpusMetrics]:
    metrics: dict[str, _MutableCorpusMetrics] = {}
    if not results_dir.exists():
        return {}
    for path in sorted(results_dir.rglob("*.json")):
        corpus = path.relative_to(results_dir).parts[0]
        item = metrics.setdefault(corpus, _MutableCorpusMetrics(corpus=corpus))
        item.files += 1
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for sentence in payload.get("features", []):
            _collect_sentence(item, sentence)
    return {key: value.freeze() for key, value in metrics.items()}


@dataclass
class _MutableCorpusMetrics:
    corpus: str
    files: int = 0
    sentences: int = 0
    slot_zero_count: int = 0
    invalid_slot_refs: int = 0
    duplicate_feature_ids: int = 0
    construction_empty_evidence_refs: int = 0
    invalid_absence_anchor_refs: int = 0
    word_order_duplicate_ordered_refs: int = 0
    negation_evidence_sentences: int = 0
    lexical_negation_count: int = 0
    predicate_negative_count: int = 0
    sentence_negative_or_mixed_count: int = 0
    pronoun_missing_required_determiner: int = 0
    proper_noun_missing_required_determiner: int = 0
    diagnostics_count: int = 0
    lexical_contractions_count: int = 0
    lexical_phrasal_verbs_count: int = 0
    lexical_comparisons_count: int = 0
    lexical_time_markers_count: int = 0
    lexical_discourse_markers_count: int = 0

    def freeze(self) -> CorpusMetrics:
        return CorpusMetrics(**self.__dict__)


def _collect_sentence(metrics: _MutableCorpusMetrics, sentence: dict[str, Any]) -> None:
    metrics.sentences += 1
    features = sentence.get("features", {})
    word_refs = {
        word.get("ref")
        for word in features.get("evidence", {}).get("words", [])
        if isinstance(word.get("ref"), int)
    }
    if _has_negative_evidence(features):
        metrics.negation_evidence_sentences += 1
    syntax = features.get("syntax", {})
    _collect_ids(metrics, syntax)
    _collect_predicates(metrics, syntax)
    _collect_np(metrics, syntax)
    _collect_lexical(metrics, features.get("lexical", {}))
    _collect_constructions(metrics, features.get("constructions", []), word_refs)
    _collect_absences(metrics, features.get("absences", []), word_refs)
    metrics.diagnostics_count += len(features.get("diagnostics", []))


def _has_negative_evidence(features: dict[str, Any]) -> bool:
    negative_words = {
        "not",
        "n't",
        "never",
        "no",
        "none",
        "nothing",
        "nobody",
        "neither",
        "nor",
        "nowhere",
        "scarcely",
        "hardly",
    }
    for word in features.get("evidence", {}).get("words", []):
        lower = str(word.get("lower", "")).casefold()
        feats = word.get("feats", {})
        if lower in negative_words:
            return True
        if feats.get("Polarity") == "Neg" or feats.get("PronType") == "Neg":
            return True
    return False


def _collect_ids(metrics: _MutableCorpusMetrics, syntax: dict[str, Any]) -> None:
    for group_name in ("clauses", "predicates", "np_profiles"):
        ids = [
            item.get("id")
            for item in syntax.get(group_name, [])
            if isinstance(item.get("id"), str)
        ]
        metrics.duplicate_feature_ids += len(ids) - len(set(ids))


def _collect_predicates(metrics: _MutableCorpusMetrics, syntax: dict[str, Any]) -> None:
    for predicate in syntax.get("predicates", []):
        if predicate.get("polarity") == "negative":
            metrics.predicate_negative_count += 1


def _collect_np(metrics: _MutableCorpusMetrics, syntax: dict[str, Any]) -> None:
    for np in syntax.get("np_profiles", []):
        requiredness = np.get("article_slot", {}).get("requiredness")
        if requiredness != "missing_required_determiner_candidate":
            continue
        if np.get("phrase_type") == "pronoun_np":
            metrics.pronoun_missing_required_determiner += 1
        if np.get("phrase_type") == "proper_noun_np":
            metrics.proper_noun_missing_required_determiner += 1


def _collect_lexical(metrics: _MutableCorpusMetrics, lexical: dict[str, Any]) -> None:
    sentence = lexical.get("sentence", {})
    if sentence.get("polarity") in {"negative", "mixed"}:
        metrics.sentence_negative_or_mixed_count += 1
    word_order = lexical.get("word_order", [])
    for item in word_order:
        refs = item.get("ordered_refs", [])
        if len(refs) != len(set(refs)):
            metrics.word_order_duplicate_ordered_refs += 1
    metrics.lexical_negation_count += len(lexical.get("negation", []))
    metrics.lexical_contractions_count += len(lexical.get("contractions", []))
    metrics.lexical_phrasal_verbs_count += len(lexical.get("phrasal_verbs", []))
    metrics.lexical_comparisons_count += len(lexical.get("comparisons", []))
    metrics.lexical_time_markers_count += len(lexical.get("time_markers", []))
    metrics.lexical_discourse_markers_count += len(lexical.get("discourse_markers", []))


def _collect_constructions(
    metrics: _MutableCorpusMetrics,
    constructions: list[dict[str, Any]],
    word_refs: set[int],
) -> None:
    keys = [
        item.get("key") for item in constructions if isinstance(item.get("key"), str)
    ]
    metrics.duplicate_feature_ids += len(keys) - len(set(keys))
    for construction in constructions:
        evidence_refs = construction.get("evidence_refs", [])
        if not evidence_refs:
            metrics.construction_empty_evidence_refs += 1
        for value in construction.get("slots", {}).values():
            values = value if isinstance(value, list) else [value]
            for slot_value in values:
                if isinstance(slot_value, int):
                    if slot_value == 0:
                        metrics.slot_zero_count += 1
                    if slot_value not in word_refs:
                        metrics.invalid_slot_refs += 1


def _collect_absences(
    metrics: _MutableCorpusMetrics,
    absences: list[dict[str, Any]],
    word_refs: set[int],
) -> None:
    for absence in absences:
        anchor = absence.get("anchor_ref")
        if not isinstance(anchor, int) or anchor not in word_refs:
            metrics.invalid_absence_anchor_refs += 1
