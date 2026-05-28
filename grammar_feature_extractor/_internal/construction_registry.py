from __future__ import annotations

from typing import Literal, TypeAlias

SUBJECT_BE_PRESENT_COMPLEMENT = "subject_be_present_complement"
BE_SUBJECT_COMPLEMENT_QUESTION = "be_subject_complement_question"
THERE_BE_NP = "there_be_np"
PRESENT_SIMPLE_LEXICAL_AFFIRMATIVE = "present_simple_lexical_affirmative"
PRESENT_SIMPLE_DO_NEGATIVE = "present_simple_do_negative"
PRESENT_SIMPLE_DO_NEGATIVE_QUESTION = "present_simple_do_negative_question"
PRESENT_SIMPLE_DO_QUESTION = "present_simple_do_question"
PRESENT_PROGRESSIVE_AFFIRMATIVE = "present_progressive_affirmative"
PRESENT_PERFECT_HAVE_PARTICIPLE = "present_perfect_have_participle"
PAST_SIMPLE_REGULAR = "past_simple_regular"
PAST_SIMPLE_LEXICAL_AFFIRMATIVE = "past_simple_lexical_affirmative"
PAST_SIMPLE_NEGATIVE = "past_simple_negative"
COPULAR_BE_NEGATIVE = "copular_be_negative"
MODAL_NEGATIVE_BASE = "modal_negative_base"
PERFECT_NEGATIVE = "perfect_negative"
PASSIVE_NEGATIVE = "passive_negative"
MODAL_MUST_BASE = "modal_must_base"
SEMI_MODAL_BE_ABLE_TO = "semi_modal_be_able_to"
PASSIVE_BE_PARTICIPLE = "passive_be_participle"
ARTICLE_INDEFINITE_A_NP = "article_indefinite_a_np"
ARTICLE_INDEFINITE_AN_NP = "article_indefinite_an_np"
ARTICLE_DEFINITE_THE_NP = "article_definite_the_np"
ZERO_ARTICLE_PLURAL_GENERIC_CANDIDATE = "zero_article_plural_generic_candidate"
COMPARISON_AS_AS = "comparison_as_as"

# Progressive/perfect-progressive/passive clauses (A6).
PRESENT_PROGRESSIVE_CLAUSE = "present_progressive_clause"
PAST_PROGRESSIVE_CLAUSE = "past_progressive_clause"
MODAL_PROGRESSIVE_CLAUSE = "modal_progressive_clause"
PRESENT_PERFECT_PROGRESSIVE_CLAUSE = "present_perfect_progressive_clause"
PAST_PERFECT_PROGRESSIVE_CLAUSE = "past_perfect_progressive_clause"
MODAL_PERFECT_PROGRESSIVE_CLAUSE = "modal_perfect_progressive_clause"
PRESENT_PERFECT_PASSIVE_CLAUSE = "present_perfect_passive_clause"
PAST_PERFECT_PASSIVE_CLAUSE = "past_perfect_passive_clause"
PROGRESSIVE_PASSIVE_CLAUSE = "progressive_passive_clause"

ConstructionSignature: TypeAlias = Literal[
    "subject_be_present_complement",
    "be_subject_complement_question",
    "there_be_np",
    "present_simple_lexical_affirmative",
    "present_simple_do_negative",
    "present_simple_do_negative_question",
    "present_simple_do_question",
    "present_progressive_affirmative",
    "present_perfect_have_participle",
    "past_simple_regular",
    "past_simple_lexical_affirmative",
    "past_simple_negative",
    "copular_be_negative",
    "modal_negative_base",
    "perfect_negative",
    "passive_negative",
    "modal_must_base",
    "semi_modal_be_able_to",
    "passive_be_participle",
    "article_indefinite_a_np",
    "article_indefinite_an_np",
    "article_definite_the_np",
    "zero_article_plural_generic_candidate",
    "comparison_as_as",
    "present_progressive_clause",
    "past_progressive_clause",
    "modal_progressive_clause",
    "present_perfect_progressive_clause",
    "past_perfect_progressive_clause",
    "modal_perfect_progressive_clause",
    "present_perfect_passive_clause",
    "past_perfect_passive_clause",
    "progressive_passive_clause",
]

REGISTERED_CONSTRUCTION_SIGNATURES = (
    SUBJECT_BE_PRESENT_COMPLEMENT,
    BE_SUBJECT_COMPLEMENT_QUESTION,
    THERE_BE_NP,
    PRESENT_SIMPLE_LEXICAL_AFFIRMATIVE,
    PRESENT_SIMPLE_DO_NEGATIVE,
    PRESENT_SIMPLE_DO_NEGATIVE_QUESTION,
    PRESENT_SIMPLE_DO_QUESTION,
    PRESENT_PROGRESSIVE_AFFIRMATIVE,
    PRESENT_PERFECT_HAVE_PARTICIPLE,
    PAST_SIMPLE_REGULAR,
    PAST_SIMPLE_LEXICAL_AFFIRMATIVE,
    PAST_SIMPLE_NEGATIVE,
    COPULAR_BE_NEGATIVE,
    MODAL_NEGATIVE_BASE,
    PERFECT_NEGATIVE,
    PASSIVE_NEGATIVE,
    MODAL_MUST_BASE,
    SEMI_MODAL_BE_ABLE_TO,
    PASSIVE_BE_PARTICIPLE,
    ARTICLE_INDEFINITE_A_NP,
    ARTICLE_INDEFINITE_AN_NP,
    ARTICLE_DEFINITE_THE_NP,
    ZERO_ARTICLE_PLURAL_GENERIC_CANDIDATE,
    COMPARISON_AS_AS,
    PRESENT_PROGRESSIVE_CLAUSE,
    PAST_PROGRESSIVE_CLAUSE,
    MODAL_PROGRESSIVE_CLAUSE,
    PRESENT_PERFECT_PROGRESSIVE_CLAUSE,
    PAST_PERFECT_PROGRESSIVE_CLAUSE,
    MODAL_PERFECT_PROGRESSIVE_CLAUSE,
    PRESENT_PERFECT_PASSIVE_CLAUSE,
    PAST_PERFECT_PASSIVE_CLAUSE,
    PROGRESSIVE_PASSIVE_CLAUSE,
)
