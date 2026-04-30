from __future__ import annotations

from typing import Literal, TypeAlias

SUBJECT_BE_PRESENT_COMPLEMENT = "subject_be_present_complement"
THERE_BE_NP = "there_be_np"
PRESENT_SIMPLE_LEXICAL_AFFIRMATIVE = "present_simple_lexical_affirmative"
PRESENT_SIMPLE_DO_NEGATIVE = "present_simple_do_negative"
PRESENT_SIMPLE_DO_QUESTION = "present_simple_do_question"
PRESENT_PROGRESSIVE_AFFIRMATIVE = "present_progressive_affirmative"
PRESENT_PERFECT_HAVE_PARTICIPLE = "present_perfect_have_participle"
MODAL_MUST_BASE = "modal_must_base"
SEMI_MODAL_BE_ABLE_TO = "semi_modal_be_able_to"
PASSIVE_BE_PARTICIPLE = "passive_be_participle"
ARTICLE_INDEFINITE_A_NP = "article_indefinite_a_np"
ARTICLE_INDEFINITE_AN_NP = "article_indefinite_an_np"
ARTICLE_DEFINITE_THE_NP = "article_definite_the_np"
COMPARISON_AS_AS = "comparison_as_as"

ConstructionSignature: TypeAlias = Literal[
    "subject_be_present_complement",
    "there_be_np",
    "present_simple_lexical_affirmative",
    "present_simple_do_negative",
    "present_simple_do_question",
    "present_progressive_affirmative",
    "present_perfect_have_participle",
    "modal_must_base",
    "semi_modal_be_able_to",
    "passive_be_participle",
    "article_indefinite_a_np",
    "article_indefinite_an_np",
    "article_definite_the_np",
    "comparison_as_as",
]
