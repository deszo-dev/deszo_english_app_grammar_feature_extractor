from __future__ import annotations

UNKNOWN = "unknown"
NOT_APPLICABLE = "not_applicable"

PRESENT_SIMPLE_LEXICAL = "present_simple_lexical"
PRESENT_SIMPLE_DO_NEGATIVE = "present_simple_do_negative"
PRESENT_SIMPLE_DO_QUESTION = "present_simple_do_question"
PRESENT_PROGRESSIVE = "present_progressive"
PRESENT_PERFECT = "present_perfect"
PRESENT_PERFECT_PROGRESSIVE = "present_perfect_progressive"
PAST_SIMPLE = "past_simple"
PAST_SIMPLE_DO_NEGATIVE = "past_simple_do_negative"
PAST_SIMPLE_DO_QUESTION = "past_simple_do_question"
PAST_PROGRESSIVE = "past_progressive"
PAST_PERFECT = "past_perfect"
PAST_PERFECT_PROGRESSIVE = "past_perfect_progressive"
FUTURE_SIMPLE = "future_simple"
FUTURE_PROGRESSIVE = "future_progressive"
FUTURE_PERFECT = "future_perfect"
MODAL_BASE_VERB = "modal_base_verb"
MODAL_PERFECT = "modal_perfect"
MODAL_PROGRESSIVE = "modal_progressive"
PASSIVE_BE_PARTICIPLE = "passive_be_participle"
PASSIVE_PERFECT = "passive_perfect"
PASSIVE_PROGRESSIVE = "passive_progressive"
BE_PRESENT_COPULAR = "be_present_copular"
BE_PAST_COPULAR = "be_past_copular"
THERE_BE_EXISTENTIAL_PRESENT = "there_be_existential_present"
THERE_BE_EXISTENTIAL_PAST = "there_be_existential_past"
PRESENT_PARTICIPLE_FRAGMENT = "present_participle_fragment"
PAST_PARTICIPLE_FRAGMENT = "past_participle_fragment"
TO_INFINITIVE_FRAGMENT = "to_infinitive_fragment"

REGISTERED_FORM_SIGNATURES: frozenset[str] = frozenset(
    {
        UNKNOWN,
        NOT_APPLICABLE,
        PRESENT_SIMPLE_LEXICAL,
        PRESENT_SIMPLE_DO_NEGATIVE,
        PRESENT_SIMPLE_DO_QUESTION,
        PRESENT_PROGRESSIVE,
        PRESENT_PERFECT,
        PRESENT_PERFECT_PROGRESSIVE,
        PAST_SIMPLE,
        PAST_SIMPLE_DO_NEGATIVE,
        PAST_SIMPLE_DO_QUESTION,
        PAST_PROGRESSIVE,
        PAST_PERFECT,
        PAST_PERFECT_PROGRESSIVE,
        FUTURE_SIMPLE,
        FUTURE_PROGRESSIVE,
        FUTURE_PERFECT,
        MODAL_BASE_VERB,
        MODAL_PERFECT,
        MODAL_PROGRESSIVE,
        PASSIVE_BE_PARTICIPLE,
        PASSIVE_PERFECT,
        PASSIVE_PROGRESSIVE,
        BE_PRESENT_COPULAR,
        BE_PAST_COPULAR,
        THERE_BE_EXISTENTIAL_PRESENT,
        THERE_BE_EXISTENTIAL_PAST,
        PRESENT_PARTICIPLE_FRAGMENT,
        PAST_PARTICIPLE_FRAGMENT,
        TO_INFINITIVE_FRAGMENT,
    }
)
