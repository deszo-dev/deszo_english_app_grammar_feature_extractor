from __future__ import annotations

from typing import Literal, TypeAlias

SUBJECT_BE_PRESENT_COMPLEMENT = "subject_be_present_complement"
BE_SUBJECT_COMPLEMENT_QUESTION = "be_subject_complement_question"
THERE_BE_NP = "there_be_np"
PRESENT_SIMPLE_LEXICAL_AFFIRMATIVE = "present_simple_lexical_affirmative"
PRESENT_SIMPLE_DO_NEGATIVE = "present_simple_do_negative"
PRESENT_SIMPLE_DO_QUESTION = "present_simple_do_question"
PRESENT_PROGRESSIVE_AFFIRMATIVE = "present_progressive_affirmative"
PRESENT_PERFECT_HAVE_PARTICIPLE = "present_perfect_have_participle"
PAST_SIMPLE_REGULAR = "past_simple_regular"
MODAL_MUST_BASE = "modal_must_base"
SEMI_MODAL_BE_ABLE_TO = "semi_modal_be_able_to"
PASSIVE_BE_PARTICIPLE = "passive_be_participle"
ARTICLE_INDEFINITE_A_NP = "article_indefinite_a_np"
ARTICLE_INDEFINITE_AN_NP = "article_indefinite_an_np"
ARTICLE_DEFINITE_THE_NP = "article_definite_the_np"
ZERO_ARTICLE_PLURAL_GENERIC_CANDIDATE = "zero_article_plural_generic_candidate"
COMPARISON_AS_AS = "comparison_as_as"

ConstructionSignature: TypeAlias = Literal[
    "subject_be_present_complement",
    "be_subject_complement_question",
    "there_be_np",
    "present_simple_lexical_affirmative",
    "present_simple_do_negative",
    "present_simple_do_question",
    "present_progressive_affirmative",
    "present_perfect_have_participle",
    "past_simple_regular",
    "modal_must_base",
    "semi_modal_be_able_to",
    "passive_be_participle",
    "article_indefinite_a_np",
    "article_indefinite_an_np",
    "article_definite_the_np",
    "zero_article_plural_generic_candidate",
    "comparison_as_as",
]

REGISTERED_CONSTRUCTION_SIGNATURES = (
    SUBJECT_BE_PRESENT_COMPLEMENT,
    BE_SUBJECT_COMPLEMENT_QUESTION,
    THERE_BE_NP,
    PRESENT_SIMPLE_LEXICAL_AFFIRMATIVE,
    PRESENT_SIMPLE_DO_NEGATIVE,
    PRESENT_SIMPLE_DO_QUESTION,
    PRESENT_PROGRESSIVE_AFFIRMATIVE,
    PRESENT_PERFECT_HAVE_PARTICIPLE,
    PAST_SIMPLE_REGULAR,
    MODAL_MUST_BASE,
    SEMI_MODAL_BE_ABLE_TO,
    PASSIVE_BE_PARTICIPLE,
    ARTICLE_INDEFINITE_A_NP,
    ARTICLE_INDEFINITE_AN_NP,
    ARTICLE_DEFINITE_THE_NP,
    ZERO_ARTICLE_PLURAL_GENERIC_CANDIDATE,
    COMPARISON_AS_AS,
)
