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
FeatureTier: TypeAlias = Literal[
    "structural",
    "deterministic",
    "heuristic",
    "external_oracle",
]
ProofSource: TypeAlias = Literal[
    "word_order",
    "upos",
    "xpos",
    "morphology",
    "dependency",
    "surface",
    "lemma",
    "closed_list",
    "lexicon",
    "phonology",
    "task_context",
    "discourse_heuristic",
]
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
AuxiliaryRole: TypeAlias = Literal[
    "tense_aux",
    "perfect_aux",
    "progressive_aux",
    "passive_aux",
    "do_support",
    "modal",
    "semi_modal",
    "copula",
    "unknown",
]
PredicateType: TypeAlias = Literal[
    "verbal",
    "copular_adjectival",
    "copular_nominal",
    "copular_prepositional",
    "existential_there",
    "unknown",
]
TenseValue: TypeAlias = Literal["present", "past", "future_like", "none", "unknown"]
AspectValue: TypeAlias = Literal[
    "simple",
    "progressive",
    "perfect",
    "perfect_progressive",
    "none",
    "unknown",
]
VoiceValue: TypeAlias = Literal["active", "passive", "unknown"]
ModalityValue: TypeAlias = Literal[
    "ability",
    "obligation",
    "permission",
    "advice",
    "necessity",
    "possibility",
    "prohibition",
    "prediction",
    "expectation",
    "past_habit",
    "none",
    "unknown",
]
AgreementType: TypeAlias = Literal[
    "subject_verb",
    "subject_copula",
    "demonstrative_noun",
    "determiner_noun",
    "existential_there_noun",
    "unknown",
]
NumberValue: TypeAlias = Literal["sing", "plur"]
PhraseType: TypeAlias = Literal["NP", "VP", "PP"]
ClauseType: TypeAlias = Literal[
    "root",
    "ccomp",
    "xcomp",
    "advcl",
    "relcl",
    "acl",
    "participle",
    "infinitive",
    "conditional",
    "reported_speech",
    "unknown",
]
MarkerType: TypeAlias = Literal[
    "finite_subordinator",
    "infinitive_to",
    "prepositional_gerund",
    "comparative_than",
    "relative_pronoun",
    "conditional_if",
    "conditional_unless",
    "reported_that",
    "purpose_to",
    "ambiguous",
    "unknown",
]
ComplementType: TypeAlias = Literal[
    "object_np",
    "indirect_object_np",
    "object_complement_adj",
    "object_complement_np",
    "subject_complement_adj",
    "subject_complement_np",
    "subject_complement_pp",
    "to_infinitive",
    "bare_infinitive",
    "gerund",
    "participle_clause",
    "that_clause",
    "wh_clause",
    "prepositional_phrase",
    "comparative_than_phrase",
    "as_as_phrase",
    "unknown",
]
SemanticRelation: TypeAlias = Literal[
    "time",
    "reason",
    "condition",
    "purpose",
    "result",
    "contrast",
    "relative",
    "reported_content",
    "unknown",
]
NPType: TypeAlias = Literal[
    "common_noun_np", "proper_noun_np", "pronoun_np", "gerund_np", "unknown"
]
ArticleRequiredness: TypeAlias = Literal[
    "article_present",
    "zero_article",
    "determiner_present",
    "missing_required_determiner_candidate",
    "not_applicable",
    "unknown",
]
ArticleForm: TypeAlias = Literal["a", "an", "the", "zero"]
SpellingClass: TypeAlias = Literal["vowel_letter", "consonant_letter", "unknown"]
SoundClass: TypeAlias = Literal["vowel_sound", "consonant_sound", "unknown"]
Definiteness: TypeAlias = Literal["definite", "indefinite", "generic", "unknown"]
DeterminerType: TypeAlias = Literal[
    "article_definite",
    "article_indefinite",
    "demonstrative",
    "possessive",
    "quantifier",
    "number",
    "negative_no",
    "interrogative",
    "none",
    "unknown",
]
DeterminerNumber: TypeAlias = Literal["singular", "plural", "both", "unknown"]
ModifierType: TypeAlias = Literal[
    "adjective",
    "compound",
    "number",
    "possessive",
    "relative_clause",
    "prepositional_phrase",
    "participle",
    "unknown",
]
SyntacticRole: TypeAlias = Literal[
    "subject",
    "object",
    "indirect_object",
    "oblique",
    "predicative_complement",
    "appositive",
    "unknown",
]
WordOrderPattern: TypeAlias = Literal[
    "subject_verb_object",
    "subject_aux_verb",
    "aux_subject_verb",
    "wh_aux_subject_verb",
    "be_subject_complement",
    "there_be_np",
    "negative_aux_not_verb",
    "unknown",
]
NegatorType: TypeAlias = Literal[
    "not", "n't", "never", "no", "none", "nothing", "neither", "unknown"
]
NegationScope: TypeAlias = Literal[
    "predicate", "noun_phrase", "clause", "sentence", "unknown"
]
ConstructionType: TypeAlias = Literal[
    "tense_aspect",
    "copular",
    "existential",
    "article_np",
    "demonstrative_np",
    "plural_noun",
    "modal",
    "passive",
    "question",
    "negation",
    "comparison",
    "subordination",
    "relative_clause",
    "conditional",
    "gerund_infinitive",
    "complement_pattern",
    "reported_speech",
]
AbsenceScope: TypeAlias = Literal["np", "predicate", "clause", "sentence"]
AbsenceTarget: TypeAlias = Literal[
    "determiner",
    "article",
    "auxiliary",
    "subject",
    "object",
    "negation",
    "preposition",
    "relative_marker",
]
AbsencePosition: TypeAlias = Literal[
    "before_head", "after_aux", "before_clause", "unknown"
]
ContrastiveHint: TypeAlias = Literal[
    "present_simple_vs_present_progressive",
    "present_perfect_vs_past_simple",
    "a_vs_an",
    "a_an_vs_the",
    "article_vs_zero_article",
    "singular_vs_plural",
    "this_that_vs_these_those",
    "comparative_vs_as_as",
    "some_vs_any",
    "much_vs_many",
    "gerund_vs_infinitive",
    "unknown",
]


@dataclass(frozen=True, slots=True)
class ProofProvenance:
    tier: FeatureTier
    source: ProofSource
    evidence_refs: tuple[WordRef, ...]
    confidence: Confidence


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
class Phrase:
    type: PhraseType
    head: WordRef
    tokens: tuple[WordRef, ...]
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class Roles:
    subject: WordRef | None
    object: WordRef | None
    indirect_object: WordRef | None
    oblique: tuple[WordRef, ...]


@dataclass(frozen=True, slots=True)
class Valency:
    subject: bool
    object: bool
    indirect_object: bool


@dataclass(frozen=True, slots=True)
class ClauseMarkerFeature:
    marker_ref: WordRef
    marker: str
    clause_head: WordRef
    marker_type: MarkerType
    confidence: Confidence
    sources: tuple[FeatureSource, ...]
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class ClauseFeature:
    id: str
    head: WordRef
    type: ClauseType
    finite: bool
    subject: WordRef | None
    predicate: WordRef | None
    marker: ClauseMarkerFeature | None
    roles: Roles
    valency: Valency
    semantic_relation: SemanticRelation | None
    tokens: tuple[WordRef, ...]
    local_tokens: tuple[WordRef, ...]
    confidence: Confidence
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class PredicateComplementFeature:
    governor: WordRef
    head: WordRef
    type: ComplementType
    preposition: str | None
    marker: str | None
    deprel_source: str
    evidence_refs: tuple[WordRef, ...]
    confidence: Confidence
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class Coordination:
    head: WordRef
    conjuncts: tuple[WordRef, ...]
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class AuxiliaryFeature:
    ref: WordRef
    lemma: str
    surface: str
    role: AuxiliaryRole


@dataclass(frozen=True, slots=True)
class ModalFeature:
    marker_refs: tuple[WordRef, ...]
    modal_type: ModalityValue
    complement_verb: WordRef | None
    polarity: Polarity
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class TAVMFeature:
    tense: TenseValue
    aspect: AspectValue
    voice: VoiceValue
    modality: ModalityValue
    form_signature: str


@dataclass(frozen=True, slots=True)
class AgreementFeature:
    subject: WordRef | None
    predicate: WordRef | None
    controller: WordRef | None
    subject_person: int | None
    subject_number: NumberValue | None
    predicate_person: int | None
    predicate_number: NumberValue | None
    match: bool | None
    agreement_type: AgreementType
    evidence_refs: tuple[WordRef, ...]
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class PredicateFeature:
    id: str
    main: WordRef
    main_lemma: str
    predicate_type: PredicateType
    finite: bool
    auxiliaries: tuple[AuxiliaryFeature, ...]
    copula: WordRef | None
    negation: WordRef | None
    tense: TenseValue
    aspect: AspectValue
    voice: VoiceValue
    modality: ModalFeature | None
    polarity: Polarity
    clause_head: WordRef
    subject: WordRef | None
    object: WordRef | None
    indirect_object: WordRef | None
    complements: tuple[PredicateComplementFeature, ...]
    agreement: AgreementFeature
    tavm: TAVMFeature
    form_signature: str
    evidence_refs: tuple[WordRef, ...]
    confidence: Confidence
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class WordOrderFeature:
    pattern: WordOrderPattern
    ordered_refs: tuple[WordRef, ...]
    confidence: Confidence
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class NegationFeature:
    ref: WordRef
    negator: NegatorType
    scope: NegationScope
    governor: WordRef | None
    confidence: Confidence
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class DeterminerFeature:
    ref: WordRef
    text: str
    lemma: str
    determiner_type: DeterminerType
    definite: bool | None
    number: DeterminerNumber | None
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class ArticleSlotFeature:
    requiredness: ArticleRequiredness
    article_form: ArticleForm | None
    following_sound_class: SoundClass | None
    following_spelling_class: SpellingClass | None
    definiteness: Definiteness | None
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class ModifierFeature:
    ref: WordRef
    modifier_type: ModifierType


@dataclass(frozen=True, slots=True)
class QuantifierFeature:
    ref: WordRef
    text: str


@dataclass(frozen=True, slots=True)
class NPFeature:
    id: str
    head: WordRef
    head_lemma: str
    phrase_type: NPType
    number: DeterminerNumber | None
    person: int | None
    determiner: DeterminerFeature | None
    has_determiner: bool
    article_slot: ArticleSlotFeature
    modifiers: tuple[ModifierFeature, ...]
    quantifiers: tuple[QuantifierFeature, ...]
    possessive: WordRef | None
    syntactic_role: SyntacticRole
    evidence_refs: tuple[WordRef, ...]
    confidence: Confidence
    provenance: ProofProvenance


SlotValue: TypeAlias = WordRef | tuple[WordRef, ...] | str | bool | int


@dataclass(frozen=True, slots=True)
class ConstructionFeature:
    key: str
    family_hint: str | None
    type: ConstructionType
    signature: str
    slots: dict[str, SlotValue]
    evidence_refs: tuple[WordRef, ...]
    confidence: Confidence
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class AbsenceFeature:
    scope: AbsenceScope
    target: AbsenceTarget
    expected_position: AbsencePosition | None
    anchor_ref: WordRef
    confidence: Confidence
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class ContrastiveSupportFeature:
    contrastive_hint: ContrastiveHint
    observed_choice: str
    competing_choices: tuple[str, ...]
    local_cues: tuple[str, ...]
    missing_context: tuple[str, ...]
    confidence: Confidence
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class SyntaxFeatures:
    phrases: tuple[Phrase, ...] = ()
    clauses: tuple[ClauseFeature, ...] = ()
    predicates: tuple[PredicateFeature, ...] = ()
    complements: tuple[PredicateComplementFeature, ...] = ()
    coordination: tuple[Coordination, ...] = ()
    subordination: tuple[ClauseMarkerFeature, ...] = ()
    np_profiles: tuple[NPFeature, ...] = ()
    pronouns: tuple[object, ...] = ()
    special_subject_constructions: tuple[object, ...] = ()
    relative_clauses: tuple[object, ...] = ()
    conditionals: tuple[object, ...] = ()
    reported_speech: tuple[object, ...] = ()
    passive: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class LexicalFeatures:
    sentence: SentenceFeature
    word_order: tuple[WordOrderFeature, ...] = ()
    negation: tuple[NegationFeature, ...] = ()
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
    constructions: tuple[ConstructionFeature, ...]
    contrastive_support: tuple[ContrastiveSupportFeature, ...]
    absences: tuple[AbsenceFeature, ...]
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
