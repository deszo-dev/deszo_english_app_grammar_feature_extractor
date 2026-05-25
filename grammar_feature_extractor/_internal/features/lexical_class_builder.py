from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    LexicalClass,
    LexicalClassFeature,
    LexicalClassSource,
)
from grammar_feature_extractor._internal.sentence_context import SentenceContext

STATIVE_VERBS = frozenset(
    {
        "be",
        "have",
        "know",
        "believe",
        "love",
        "like",
        "hate",
        "want",
        "need",
        "own",
        "owe",
        "seem",
        "appear",
        "understand",
        "remember",
        "forget",
        "prefer",
        "wish",
        "mean",
        "matter",
    }
)

DYNAMIC_VERBS = frozenset(
    {
        "run",
        "walk",
        "go",
        "come",
        "make",
        "do",
        "take",
        "give",
        "write",
        "read",
        "play",
        "build",
        "speak",
        "eat",
        "drink",
        "open",
        "close",
        "jump",
        "fall",
        "throw",
    }
)

LINKING_VERBS = frozenset(
    {"be", "seem", "appear", "become", "feel", "look", "sound", "smell", "taste", "stay", "remain"}
)

REPORTING_VERBS = frozenset(
    {
        "say",
        "tell",
        "ask",
        "answer",
        "reply",
        "explain",
        "describe",
        "report",
        "claim",
        "state",
        "remark",
        "whisper",
        "shout",
        "cry",
        "exclaim",
        "inquire",
        "observe",
        "murmur",
        "mention",
        "argue",
        "declare",
        "announce",
        "insist",
        "admit",
        "deny",
    }
)

MENTAL_STATE_VERBS = frozenset(
    {
        "know",
        "think",
        "believe",
        "understand",
        "doubt",
        "suppose",
        "guess",
        "imagine",
        "realise",
        "realize",
        "recognize",
        "recognise",
        "remember",
        "forget",
        "consider",
        "wonder",
        "feel",
    }
)

MOTION_VERBS = frozenset(
    {
        "go",
        "come",
        "walk",
        "run",
        "ride",
        "drive",
        "fly",
        "swim",
        "climb",
        "jump",
        "fall",
        "enter",
        "leave",
        "depart",
        "arrive",
        "travel",
        "move",
        "approach",
        "return",
        "follow",
    }
)

COMMUNICATION_VERBS = frozenset(
    {
        "say",
        "tell",
        "speak",
        "talk",
        "ask",
        "answer",
        "reply",
        "explain",
        "describe",
        "discuss",
        "argue",
        "shout",
        "whisper",
        "call",
        "write",
        "read",
        "report",
    }
)

FREQUENCY_ADVERBS = frozenset(
    {
        "always",
        "often",
        "usually",
        "sometimes",
        "rarely",
        "seldom",
        "never",
        "occasionally",
        "frequently",
        "generally",
        "normally",
    }
)

TIME_ADVERBS = frozenset(
    {
        "now",
        "today",
        "yesterday",
        "tomorrow",
        "soon",
        "later",
        "earlier",
        "tonight",
        "afterwards",
        "afterward",
        "recently",
        "already",
        "still",
        "yet",
    }
)

GRADABLE_ADJECTIVES = frozenset(
    {
        "good",
        "bad",
        "big",
        "small",
        "tall",
        "short",
        "young",
        "old",
        "hot",
        "cold",
        "warm",
        "cool",
        "happy",
        "sad",
        "fast",
        "slow",
        "easy",
        "hard",
        "strong",
        "weak",
        "beautiful",
        "ugly",
        "bright",
        "dark",
    }
)

ABSOLUTE_ADJECTIVES = frozenset(
    {
        "dead",
        "alive",
        "unique",
        "perfect",
        "infinite",
        "absolute",
        "complete",
        "total",
        "impossible",
        "essential",
    }
)


def _classes_for_lemma(lemma: str, upos: str) -> tuple[LexicalClass, ...]:
    classes: list[LexicalClass] = []
    if upos == "VERB" or upos == "AUX":
        if lemma in STATIVE_VERBS:
            classes.append("stative_verb")
        if lemma in DYNAMIC_VERBS:
            classes.append("dynamic_verb")
        if lemma in LINKING_VERBS:
            classes.append("linking_verb")
        if lemma in REPORTING_VERBS:
            classes.append("reporting_verb")
        if lemma in MENTAL_STATE_VERBS:
            classes.append("mental_state_verb")
        if lemma in MOTION_VERBS:
            classes.append("motion_verb")
        if lemma in COMMUNICATION_VERBS:
            classes.append("communication_verb")
    elif upos == "ADV":
        if lemma in FREQUENCY_ADVERBS:
            classes.append("frequency_adverb")
        if lemma in TIME_ADVERBS:
            classes.append("time_adverb")
    elif upos == "ADJ":
        if lemma in GRADABLE_ADJECTIVES:
            classes.append("gradable_adjective")
        if lemma in ABSOLUTE_ADJECTIVES:
            classes.append("absolute_adjective")
    return tuple(classes)


def build_lexical_classes(
    ctx: SentenceContext,
) -> tuple[LexicalClassFeature, ...]:
    features: list[LexicalClassFeature] = []
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        lemma = (word.lemma or word.text).casefold()
        classes = _classes_for_lemma(lemma, word.upos)
        if not classes:
            continue
        features.append(
            LexicalClassFeature(
                ref=ref,
                lemma=lemma,
                classes=classes,
                source="closed_list",
                confidence="high",
            )
        )
    return tuple(features)


__all__ = ["build_lexical_classes"]
