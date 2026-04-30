from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

SCHEMA_VERSION = "grammar_feature_extractor.v3"
DEFAULT_PAGE_SIZE = 300
DEFAULT_PAGE_NUMBER = 1
MAX_PAGE_SIZE = 5000

WordRef: TypeAlias = int

Severity: TypeAlias = Literal["info", "warning", "error"]
Confidence: TypeAlias = Literal["high", "medium", "low"]
FeatureSource: TypeAlias = Literal[
    "surface",
    "lemma",
    "upos",
    "xpos",
    "morphology",
    "dependency",
    "punctuation",
    "closed_list",
    "lexicon",
    "heuristic",
    "cross_sentence_heuristic",
    "input_entity",
    "unknown",
]
SentenceKind: TypeAlias = Literal[
    "normal", "title", "fragment", "exclamation_fragment", "quote", "unknown"
]
SentenceType: TypeAlias = Literal[
    "declarative",
    "yes_no_question",
    "wh_question",
    "tag_question",
    "imperative",
    "exclamative",
    "short_answer",
    "fragment",
    "unknown",
]
Polarity: TypeAlias = Literal["positive", "negative", "mixed", "unknown"]


@dataclass(frozen=True, slots=True)
class AnnotatedWord:
    text: str
    lemma: str
    upos: str
    xpos: str | None
    feats: str | None
    head: int
    deprel: str
    start_char: int
    end_char: int


@dataclass(frozen=True, slots=True)
class AnnotatedToken:
    text: str
    words: tuple[AnnotatedWord, ...]


@dataclass(frozen=True, slots=True)
class Entity:
    text: str
    type: str
    start_char: int
    end_char: int


@dataclass(frozen=True, slots=True)
class AnnotatedSentence:
    text: str
    tokens: tuple[AnnotatedToken, ...]
    words: tuple[AnnotatedWord, ...]


@dataclass(frozen=True, slots=True)
class AnnotatedDocument:
    sentences: tuple[AnnotatedSentence, ...]
    entities: tuple[Entity, ...]


@dataclass(frozen=True, slots=True)
class ExtractorConfig:
    include_diagnostics: bool = True
    include_evidence: bool = True
    include_construction_signatures: bool = True
    include_contrastive_support: bool = True
    enable_heuristics: bool = True
    debug: bool = False


@dataclass(frozen=True, slots=True)
class PagingConfig:
    page_number: int = DEFAULT_PAGE_NUMBER
    page_size: int = DEFAULT_PAGE_SIZE


@dataclass(frozen=True, slots=True)
class FeatureDiagnostic:
    severity: Severity
    code: str
    message: str
    refs: tuple[WordRef, ...]
    feature_path: str | None = None


@dataclass(frozen=True, slots=True)
class TokenEvidence:
    ref: WordRef
    text: str
    lower: str
    lemma: str
    upos: str
    xpos: str | None
    feats: dict[str, str]
    head: WordRef | Literal[0]
    deprel: str
    children: tuple[WordRef, ...]
    start_char: int
    end_char: int
    position: int


@dataclass(frozen=True, slots=True)
class DependencyEvidence:
    governor: WordRef | Literal[0]
    dependent: WordRef
    deprel: str


@dataclass(frozen=True, slots=True)
class EvidenceFeatures:
    words: tuple[TokenEvidence, ...]
    dependencies: tuple[DependencyEvidence, ...]


@dataclass(frozen=True, slots=True)
class MorphFeature:
    ref: WordRef
    pos: str
    xpos: str | None
    lemma: str
    features: dict[str, str]


@dataclass(frozen=True, slots=True)
class NormalizedMorph:
    ref: WordRef
    is_finite_verb: bool
    is_base_verb: bool
    is_to_infinitive: bool
    is_bare_infinitive: bool
    is_gerund: bool
    is_past_participle: bool
    is_present_participle: bool
    is_plural_noun: bool
    is_singular_noun: bool
    is_comparative: bool
    is_superlative: bool


@dataclass(frozen=True, slots=True)
class MorphologyFeatures:
    word_morphology: tuple[MorphFeature, ...]
    normalized: tuple[NormalizedMorph, ...]


@dataclass(frozen=True, slots=True)
class SentenceFeature:
    sentence_kind: SentenceKind
    clause_count: int
    sentence_type: SentenceType
    polarity: Polarity
    has_subject_aux_inversion: bool
    has_do_support: bool
    has_wh_fronting: bool
    has_tag_question: bool
    has_exclamation_marker: bool


@dataclass(frozen=True, slots=True)
class SyntaxFeatures:
    phrases: tuple[object, ...] = ()
    clauses: tuple[object, ...] = ()
    predicates: tuple[object, ...] = ()
    complements: tuple[object, ...] = ()
    coordination: tuple[object, ...] = ()
    subordination: tuple[object, ...] = ()
    np_profiles: tuple[object, ...] = ()
    pronouns: tuple[object, ...] = ()
    special_subject_constructions: tuple[object, ...] = ()
    relative_clauses: tuple[object, ...] = ()
    conditionals: tuple[object, ...] = ()
    reported_speech: tuple[object, ...] = ()
    passive: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class LexicalFeatures:
    sentence: SentenceFeature
    word_order: tuple[object, ...] = ()
    negation: tuple[object, ...] = ()
    time_markers: tuple[object, ...] = ()
    lexical_classes: tuple[object, ...] = ()
    verb_patterns: tuple[object, ...] = ()
    adjective_patterns: tuple[object, ...] = ()
    comparisons: tuple[object, ...] = ()
    quantifiers: tuple[object, ...] = ()
    phrasal_verbs: tuple[object, ...] = ()
    discourse_markers: tuple[object, ...] = ()
    contractions: tuple[object, ...] = ()
    noun_inflections: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class GrammarFeatureSet:
    evidence: EvidenceFeatures
    morphology: MorphologyFeatures
    syntax: SyntaxFeatures
    lexical: LexicalFeatures
    constructions: tuple[object, ...]
    contrastive_support: tuple[object, ...]
    absences: tuple[object, ...]
    diagnostics: tuple[FeatureDiagnostic, ...]


@dataclass(frozen=True, slots=True)
class SentenceGrammarFeatures:
    sentence_index: int
    text: str
    features: GrammarFeatureSet


@dataclass(frozen=True, slots=True)
class GrammarFeatureDocument:
    schema_version: str
    source_sentence_count: int
    sentences: tuple[SentenceGrammarFeatures, ...]


@dataclass(frozen=True, slots=True)
class PageInfo:
    page_number: int
    page_size: int
    total_sentences: int
    sentence_start: int
    sentence_end_exclusive: int
    has_next_page: bool
    next_page: int | None


@dataclass(frozen=True, slots=True)
class GrammarFeaturePage:
    schema_version: str
    page: PageInfo
    features: tuple[SentenceGrammarFeatures, ...]
