from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

SCHEMA_VERSION = "grammar_feature_extractor.v4"
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
    "passive_verbal",
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
VoiceValue: TypeAlias = Literal[
    "active", "passive", "copular_not_applicable", "unknown"
]
ModalityValue: TypeAlias = Literal[
    "ability",
    "permission",
    "possibility",
    "obligation",
    "deduction",
    "advice",
    "prediction",
    "conditional",
    "necessity",
    "expectation",
    "past_habit",
    "unknown",
]
ModalType: TypeAlias = Literal[
    "can_ability",
    "could_ability",
    "may_permission",
    "might_possibility",
    "must_obligation",
    "must_deduction",
    "should_advice",
    "will_prediction",
    "would_conditional",
    "shall_prediction",
    "have_to_obligation",
    "need_to_necessity",
    "be_able_to_ability",
    "be_supposed_to_expectation",
    "used_to_past_habit",
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
    "common_noun_np",
    "proper_noun_np",
    "pronoun_np",
    "quantified_np",
    "metadata_label_np",
    "gerund_np",
    "unknown",
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
ArticlePresence: TypeAlias = Literal[
    "overt", "zero", "absent_not_applicable", "unknown"
]
PhonologySource: TypeAlias = Literal[
    "exception_list", "spelling_heuristic", "unknown"
]
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
    "unknown",
]
NegationType: TypeAlias = Literal[
    "strict_negator",
    "negative_determiner",
    "negative_pronoun",
    "negative_coordinator",
    "negative_like_adverb",
    "unknown",
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
PronounType: TypeAlias = Literal[
    "personal_subject",
    "personal_object",
    "possessive_determiner",
    "possessive_pronoun",
    "reflexive",
    "relative",
    "interrogative",
    "demonstrative",
    "indefinite",
    "dummy_it",
    "existential_there",
    "unknown",
]
PronounNumber: TypeAlias = Literal["singular", "plural"]
PronounCase: TypeAlias = Literal["subject", "object", "possessive", "unknown"]
SpecialSubjectType: TypeAlias = Literal[
    "existential_there",
    "dummy_it_weather",
    "dummy_it_extraposition",
    "cleft_it",
    "unknown",
]
RelativeType: TypeAlias = Literal[
    "subject_relative",
    "object_relative",
    "possessive_relative",
    "place_relative",
    "reduced_participle_relative",
    "reduced_to_infinitive_relative",
    "unknown",
]
RelativeMarkerText: TypeAlias = Literal[
    "who", "which", "that", "where", "whose", "whom"
]
ConditionalType: TypeAlias = Literal[
    "zero_conditional_candidate",
    "first_conditional_candidate",
    "second_conditional_candidate",
    "third_conditional_candidate",
    "mixed_conditional_candidate",
    "unless_conditional",
    "unknown",
]
ReportType: TypeAlias = Literal[
    "that_clause",
    "reported_question",
    "reported_command",
    "direct_quote",
    "unknown",
]
PassiveType: TypeAlias = Literal[
    "be_passive",
    "get_passive",
    "modal_passive",
    "perfect_passive",
    "reduced_passive_participle",
    "unknown",
]
TimeMarkerType: TypeAlias = Literal[
    "now",
    "current_period",
    "habitual_frequency",
    "past_finished_time",
    "present_perfect_experience",
    "present_perfect_result",
    "duration_for",
    "duration_since",
    "future_time",
    "sequence",
    "deadline",
    "unknown",
]
LexicalClass: TypeAlias = Literal[
    "stative_verb",
    "dynamic_verb",
    "linking_verb",
    "ditransitive_verb",
    "reporting_verb",
    "mental_state_verb",
    "motion_verb",
    "communication_verb",
    "degree_adjective",
    "gradable_adjective",
    "absolute_adjective",
    "frequency_adverb",
    "time_adverb",
]
LexicalClassSource: TypeAlias = Literal["closed_list", "lexicon", "heuristic"]
VerbPattern: TypeAlias = Literal[
    "verb_np",
    "verb_np_np",
    "verb_np_pp",
    "verb_to_infinitive",
    "verb_object_to_infinitive",
    "verb_gerund",
    "verb_that_clause",
    "verb_wh_clause",
    "verb_object_complement_adj",
    "verb_object_complement_np",
    "verb_particle_object",
    "unknown",
]
AdjectivePattern: TypeAlias = Literal[
    "adjective_to_infinitive",
    "adjective_preposition_gerund",
    "adjective_that_clause",
    "too_adjective_to_infinitive",
    "adjective_enough_to_infinitive",
    "comparative_adjective_than",
    "as_adjective_as",
    "not_as_adjective_as",
    "unknown",
]
ComparisonType: TypeAlias = Literal[
    "comparative_er",
    "comparative_more",
    "comparative_less",
    "superlative_est",
    "superlative_most",
    "equality_as_as",
    "negative_equality_not_as_as",
    "as_much_many_as",
    "comparative_than",
    "unknown",
]
ComparisonRelation: TypeAlias = Literal[
    "greater_degree",
    "lower_degree",
    "equal_degree",
    "not_equal_degree",
    "maximum_degree",
    "unknown",
]
QuantifierType: TypeAlias = Literal[
    "some",
    "any",
    "no",
    "many",
    "much",
    "a_lot_of",
    "few",
    "little",
    "enough",
    "too_much",
    "too_many",
    "number",
    "ordinal",
    "unknown",
]
QuantifierCompatibleNumber: TypeAlias = Literal[
    "singular", "plural", "uncountable", "unknown"
]
QuantifierPolaritySensitivity: TypeAlias = Literal[
    "positive", "negative_or_question", "both", "unknown"
]
PhrasalVerbSeparability: TypeAlias = Literal["separated", "adjacent", "unknown"]
DiscourseMarkerType: TypeAlias = Literal[
    "contrast",
    "addition",
    "consequence",
    "reason",
    "condition",
    "example",
    "sequence",
    "topic_shift",
    "stance",
    "unknown",
]
ContractionExpansion: TypeAlias = Literal[
    "I am",
    "he is",
    "she is",
    "it is",
    "we are",
    "they are",
    "do not",
    "does not",
    "did not",
    "will not",
    "cannot",
    "have",
    "has",
    "had",
    "unknown",
]
ContractionTypeKind: TypeAlias = Literal[
    "be_present", "aux_negative", "modal_negative", "have_perfect", "unknown"
]
PluralPattern: TypeAlias = Literal[
    "regular_s",
    "es_after_sibilant",
    "consonant_y_to_ies",
    "f_fe_to_ves",
    "irregular",
    "zero_plural",
    "foreign_plural",
    "unknown",
]
NounNumberValue: TypeAlias = Literal["singular", "plural", "unknown"]
CountabilityValue: TypeAlias = Literal[
    "count_singular",
    "count_plural",
    "uncountable",
    "proper_name",
    "pronoun_not_applicable",
    "dual_use",
    "unknown",
]
CountabilitySource: TypeAlias = Literal[
    "morphology", "lexicon", "determiner_pattern", "parser", "unknown"
]
PluralSurfaceClass: TypeAlias = Literal[
    "singular",
    "regular_s",
    "regular_es_after_sibilant",
    "consonant_y_ies",
    "irregular",
    "invariant",
    "unknown",
]
ReferenceStatus: TypeAlias = Literal[
    "first_mention_candidate",
    "previously_mentioned_candidate",
    "unique_world_knowledge_candidate",
    "situationally_identifiable_candidate",
    "generic_class_reference_candidate",
    "specific_reference_candidate",
    "unknown",
]
ReferenceEvidenceKind: TypeAlias = Literal[
    "same_lemma_previous_sentence",
    "definite_article",
    "unique_noun_whitelist",
    "plural_generic_subject",
    "context_unavailable",
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
    include_construction_signatures: bool = False
    include_contrastive_support: bool = False
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
    modal_type: ModalType
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
    main_upos: str
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
    slots: dict[str, WordRef]
    confidence: Confidence
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class NegationFeature:
    ref: WordRef
    negator: NegatorType
    negation_type: NegationType
    scope: NegationScope
    governor: WordRef | None
    confidence: Confidence
    provenance: ProofProvenance


@dataclass(frozen=True, slots=True)
class LexicalItemFeature:
    kind: str
    refs: tuple[WordRef, ...]
    text: str
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
    owner_np_id: str
    article_presence: ArticlePresence
    article_form: ArticleForm | None
    determiner_ref: WordRef | None
    head_ref: WordRef
    following_word_ref: WordRef
    following_sound_class: SoundClass | None
    following_sound_source: PhonologySource
    following_sound_confidence: Confidence
    following_spelling_class: SpellingClass | None
    definiteness: Definiteness | None
    evidence_refs: tuple[WordRef, ...]
    source: FeatureSource
    confidence: Confidence
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
class GrammarEligibilityFeature:
    article_choice_eligible: bool
    countability_choice_eligible: bool
    plural_inflection_choice_eligible: bool
    reason: str


@dataclass(frozen=True, slots=True)
class PluralAnalysisFeature:
    number: DeterminerNumber
    surface_plural_class: PluralSurfaceClass
    lemma: str
    surface: str
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class NPFeature:
    id: str
    head: WordRef
    token_refs: tuple[WordRef, ...]
    determiner_refs: tuple[WordRef, ...]
    head_lemma: str
    head_upos: str
    phrase_type: NPType
    number: DeterminerNumber | None
    person: int | None
    grammar_eligibility: GrammarEligibilityFeature
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
    plural_analysis: PluralAnalysisFeature | None = None
    countability: "CountabilityFeature | None" = None
    reference: "ReferenceFeature | None" = None


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
class PronounFeature:
    ref: WordRef
    lemma: str
    pronoun_type: PronounType
    person: int | None
    number: PronounNumber | None
    case: PronounCase | None


@dataclass(frozen=True, slots=True)
class SpecialSubjectConstructionFeature:
    type: SpecialSubjectType
    subject_ref: WordRef
    predicate_ref: WordRef
    notional_subject: WordRef | None
    agreement_controller: WordRef | None
    evidence_refs: tuple[WordRef, ...]
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class RelativeClauseFeature:
    clause_id: str
    head_noun: WordRef
    relative_marker: WordRef | None
    marker_text: RelativeMarkerText | None
    relative_type: RelativeType
    restrictive: bool | None
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class ConditionalFeature:
    if_clause: str
    main_clause: str
    conditional_type: ConditionalType
    if_marker_ref: WordRef | None
    main_tavm: TAVMFeature
    subordinate_tavm: TAVMFeature
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class ReportedSpeechFeature:
    reporting_verb: WordRef
    reported_clause_head: WordRef
    marker: WordRef | None
    report_type: ReportType
    backshift_candidate: bool
    speaker_or_addressee_refs: tuple[WordRef, ...]
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class PassiveFeature:
    predicate: WordRef
    passive_type: PassiveType
    aux_refs: tuple[WordRef, ...]
    participle_ref: WordRef
    agent_by_phrase: tuple[WordRef, ...]
    patient_subject: WordRef | None
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class TimeMarkerFeature:
    refs: tuple[WordRef, ...]
    marker: str
    type: TimeMarkerType
    normalized_value: str | None
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class LexicalClassFeature:
    ref: WordRef
    lemma: str
    classes: tuple[LexicalClass, ...]
    source: LexicalClassSource
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class VerbPatternFeature:
    predicate: WordRef
    lemma: str
    pattern: VerbPattern
    complements: tuple[PredicateComplementFeature, ...]
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class AdjectivePatternFeature:
    adjective: WordRef
    lemma: str
    pattern: AdjectivePattern
    complement: PredicateComplementFeature | None
    degree_modifier: WordRef | None
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class ComparisonFeature:
    type: ComparisonType
    adjective_or_adverb: WordRef | None
    marker_refs: tuple[WordRef, ...]
    than_ref: WordRef | None
    standard_of_comparison: tuple[WordRef, ...]
    semantic_relation: ComparisonRelation
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class TypedQuantifierFeature:
    ref: WordRef
    text: str
    quantifier_type: QuantifierType
    compatible_number: QuantifierCompatibleNumber | None
    polarity_sensitivity: QuantifierPolaritySensitivity | None


@dataclass(frozen=True, slots=True)
class PhrasalVerbFeature:
    verb: WordRef
    particle_ref: WordRef
    particle: str
    object_ref: WordRef | None
    separability: PhrasalVerbSeparability
    lemma_signature: str
    confidence: Confidence
    sources: tuple[FeatureSource, ...]


@dataclass(frozen=True, slots=True)
class DiscourseMarkerFeature:
    refs: tuple[WordRef, ...]
    marker: str
    marker_type: DiscourseMarkerType
    clause_scope: str | None
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class ContractionFeature:
    surface_ref: WordRef
    surface: str
    expansion: ContractionExpansion
    contraction_type: ContractionTypeKind


@dataclass(frozen=True, slots=True)
class NounInflectionFeature:
    ref: WordRef
    lemma: str
    surface: str
    number: NounNumberValue
    plural_pattern: PluralPattern | None
    expected_plural: tuple[str, ...]
    is_plural_error_candidate: bool | None


@dataclass(frozen=True, slots=True)
class CountabilityFeature:
    status: CountabilityValue
    source: CountabilitySource
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class ReferenceFeature:
    reference_status: ReferenceStatus
    evidence: ReferenceEvidenceKind
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class SyntaxFeatures:
    phrases: tuple[Phrase, ...] = ()
    clauses: tuple[ClauseFeature, ...] = ()
    predicates: tuple[PredicateFeature, ...] = ()
    complements: tuple[PredicateComplementFeature, ...] = ()
    coordination: tuple[Coordination, ...] = ()
    subordination: tuple[ClauseMarkerFeature, ...] = ()
    np_profiles: tuple[NPFeature, ...] = ()
    pronouns: tuple[PronounFeature, ...] = ()
    special_subject_constructions: tuple[SpecialSubjectConstructionFeature, ...] = ()
    relative_clauses: tuple[RelativeClauseFeature, ...] = ()
    conditionals: tuple[ConditionalFeature, ...] = ()
    reported_speech: tuple[ReportedSpeechFeature, ...] = ()
    passive: tuple[PassiveFeature, ...] = ()


@dataclass(frozen=True, slots=True)
class LexicalFeatures:
    sentence: SentenceFeature
    word_order: tuple[WordOrderFeature, ...] = ()
    negation: tuple[NegationFeature, ...] = ()
    time_markers: tuple[LexicalItemFeature, ...] = ()
    lexical_classes: tuple[LexicalClassFeature, ...] = ()
    verb_patterns: tuple[VerbPatternFeature, ...] = ()
    adjective_patterns: tuple[AdjectivePatternFeature, ...] = ()
    comparisons: tuple[LexicalItemFeature, ...] = ()
    quantifiers: tuple[TypedQuantifierFeature, ...] = ()
    phrasal_verbs: tuple[LexicalItemFeature, ...] = ()
    discourse_markers: tuple[LexicalItemFeature, ...] = ()
    contractions: tuple[LexicalItemFeature, ...] = ()
    noun_inflections: tuple[LexicalItemFeature, ...] = ()


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
