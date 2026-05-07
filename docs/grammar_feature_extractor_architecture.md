# grammar_feature_extractor architecture

`grammar_feature_extractor` — модуль чистого извлечения грамматических признаков из уже готовых синтаксико-морфологических аннотаций.

Модуль преобразует `AnnotatedDocument`, полученный от `stanza_annotator`, в стабильный набор `GrammarFeatureSet` по каждому предложению. Он **не выполняет парсинг**, **не вызывает Stanza**, **не принимает raw text** и **не делает preprocessing**.

Начиная с версии `grammar_feature_extractor.v3`, output ориентирован не только на человекочитаемый feature dump, но и на последующий matcher:

```text
sentence + GrammarFeatureSet -> grammar_rule candidates
sentence + GrammarFeatureSet + task/intended meaning -> grammar_contrastive_rule candidates
```

`grammar_feature_extractor` не генерирует `grammar_rule.json` и `grammar_contrastive_rule.json`. Он предоставляет evidence-rich feature graph, на основе которого отдельные компоненты `grammar_rule_matcher` и `contrastive_rule_matcher` могут сопоставлять предложения с уже существующими правилами.

## 1. Цель

Преобразовать низкоуровневые аннотации предложения: tokens, POS / UPOS, morphology `feats`, lemma, dependency graph и character spans — в стабильные grammar features:

1. evidence layer;
2. morphology features;
3. syntax features;
4. predicate / clause / NP features;
5. lexical / heuristic features;
6. construction signatures for rule matching;
7. contrastive support hints;
8. absence features;
9. diagnostics;
10. paginated serialized output для больших документов.

## 2. Граница ответственности

### Входит в ответственность модуля

- чтение `AnnotatedDocument` из `stdin` или файла через CLI;
- валидация входного JSON-контракта до передачи в `core`;
- извлечение grammar features из уже готовых аннотаций;
- формирование `GrammarFeatureDocument` в чистом `core`;
- формирование `GrammarFeaturePage` как детерминированного среза результата;
- нормализация POS/morph/dependency evidence для последующего matcher;
- построение construction signatures как формальных признаков, а не как педагогических правил;
- формирование contrastive support hints с явным указанием недостающего контекста;
- логирование pipeline-шагов в `stderr`;
- debug-трассировка без изменения результата;
- стабильная JSON-сериализация результата.

### Не входит в ответственность модуля

- Stanza pipeline configuration;
- вызов Stanza runtime;
- annotation raw text;
- preprocessing текста;
- sentence splitting;
- исправление parser errors;
- semantic role labeling;
- полноценный coreference;
- deep discourse analysis;
- определение intended meaning;
- принятие педагогического решения `choose/reject` для contrastive rules;
- генерация `grammar_rule.json`;
- генерация `grammar_contrastive_rule.json`.

Если требуется получить аннотации из текста, upstream-компонент обязан сначала вызвать `stanza_annotator`, а затем передать его результат в `grammar_feature_extractor`.

## 3. Архитектурные слои

```text
stdin / input file containing AnnotatedDocument JSON
        |
        v
+------------------------------------+
| CLI                                |
| - parse args                       |
| - resolve config                   |
| - read JSON input                  |
| - validate AnnotatedDocument       |
| - call pipeline                    |
| - write one GrammarFeaturePage     |
| - write logs/errors to stderr      |
+------------------------------------+
        |
        v
+------------------------------------+
| Application pipeline               |
| - no linguistic work               |
| - call pure extractor core         |
| - call pure pagination function    |
+------------------------------------+
        |
        v
+------------------------------------+
| Core                               |
| - no IO                            |
| - no environment access            |
| - no global state                  |
| - deterministic extraction         |
| - deterministic pagination         |
| - matcher-oriented feature graph   |
| - candidate for Coq specification  |
+------------------------------------+
        |
        v
GrammarFeaturePage JSON
```

Основная модель:

```text
GrammarFeatureDocument = extract_core(AnnotatedDocument, ExtractorConfig)
GrammarFeaturePage     = paginate(GrammarFeatureDocument, PagingConfig)
```

`extract_core` и `paginate` являются чистыми функциями. CLI не имеет права менять их семантику.

## 4. Input contract

### 4.1 Источник входа

На вход `grammar_feature_extractor` подаётся **только** `AnnotatedDocument` из `stanza_annotator`.

```text
stanza_annotator:          Prepared UTF-8 text -> AnnotatedDocument
grammar_feature_extractor: AnnotatedDocument  -> GrammarFeaturePage
```

Модуль не принимает raw text. Если CLI получает не JSON `AnnotatedDocument`, это expected data error и exit code `1`.

### 4.2 TypeScript-контракт входа

Контракт совместим с выходом `stanza_annotator`.

```typescript
interface AnnotatedDocument {
  sentences: AnnotatedSentence[];
  entities: Entity[];
}

interface AnnotatedSentence {
  text: string;
  tokens: Token[];
  words: Word[];
}

interface Token {
  text: string;
  words: Word[];
}

interface Word {
  text: string;
  lemma: string;
  upos: string;
  xpos?: string;
  feats?: string;
  head: number;
  deprel: string;
  start_char: number;
  end_char: number;
}

interface Entity {
  text: string;
  type: string;
  start_char: number;
  end_char: number;
}
```

### 4.3 WordRef

Выходные grammar features должны ссылаться на слова через `WordRef`.

```typescript
type WordRef = number;
```

`WordRef` — sentence-local 1-based индекс слова в массиве `AnnotatedSentence.words`.

Правила:

- первое слово предложения имеет `WordRef = 1`;
- `WordRef` не хранится во входном `Word`, а детерминированно выводится из позиции слова в `words`;
- все ссылки в features обязаны указывать на существующие слова этого же предложения;
- ссылка между разными предложениями запрещена;
- `head = 0` во входном dependency graph сохраняет UD-семантику root и не является `WordRef`.

### 4.4 Инварианты входа

- `sentences` присутствует всегда;
- `entities` присутствует всегда, но extractor может не использовать entities;
- `Sentence.text` не пустой для каждого существующего предложения;
- `Sentence.words` не пустой для каждого существующего предложения;
- `Token.words` не пустой для каждого токена;
- `Word.text`, `Word.upos`, `Word.deprel` не пустые;
- `Word.start_char <= Word.end_char`;
- пустой документ допустим: `sentences = []`, `entities = []`.

Нарушение этих инвариантов является expected data error и должно завершать CLI с exit code `1`.

## 5. Output contract

### 5.1 Schema version

```typescript
type GrammarFeatureSchemaVersion = "grammar_feature_extractor.v3";
```

`v3` — breaking change относительно `v2`, потому что output теперь содержит matcher-oriented evidence layer, morphology layer, construction signatures, absences и contrastive support hints.

### 5.2 Core output

`core` возвращает полный результат без paging.

```typescript
interface GrammarFeatureDocument {
  schema_version: "grammar_feature_extractor.v3";
  source_sentence_count: number;
  sentences: SentenceGrammarFeatures[];
}

interface SentenceGrammarFeatures {
  sentence_index: number; // 0-based index in AnnotatedDocument.sentences
  text: string;
  features: GrammarFeatureSet;
}

interface GrammarFeatureSet {
  evidence: EvidenceFeatures;
  morphology: MorphologyFeatures;
  syntax: SyntaxFeatures;
  lexical: LexicalFeatures;
  constructions: ConstructionFeature[];
  contrastive_support: ContrastiveSupportFeature[];
  absences: AbsenceFeature[];
  diagnostics: FeatureDiagnostic[];
}
```

### 5.3 Paginated CLI/API output

CLI выводит одну страницу features.

```typescript
interface GrammarFeaturePage {
  schema_version: "grammar_feature_extractor.v3";
  page: PageInfo;
  features: SentenceGrammarFeatures[];
}

interface PageInfo {
  page_number: number;          // 1-based
  page_size: number;            // default = 300
  total_sentences: number;
  sentence_start: number;       // 0-based inclusive
  sentence_end_exclusive: number;
  has_next_page: boolean;
  next_page?: number;
}
```

Paging rules:

- `page_size` по умолчанию равен `300` предложениям;
- `page_size` задаётся через CLI `--page-size` или Python `PagingConfig.page_size`;
- `page_number` задаётся через CLI `--page` или Python `PagingConfig.page_number`;
- `page_number` начинается с `1`;
- `sentence_start = (page_number - 1) * page_size`;
- `sentence_end_exclusive = min(sentence_start + page_size, total_sentences)`;
- `features.length <= page_size`;
- если `sentence_start >= total_sentences`, возвращается валидная пустая страница;
- paging не меняет features, а только выбирает стабильный срез;
- порядок предложений всегда совпадает с порядком `AnnotatedDocument.sentences`.

## 6. Common primitives

### 6.1 Confidence

```typescript
type Confidence = "high" | "medium" | "low";
```

`confidence` не является вероятностью. Это контрактная метка качества evidence:

- `high`: feature напрямую следует из POS/morph/dependency/surface pattern;
- `medium`: feature следует из комбинации parser evidence и закрытого списка;
- `low`: feature является heuristic candidate и требует внешнего контекста.

### 6.2 Feature source

```typescript
type FeatureSource =
  | "surface"
  | "lemma"
  | "upos"
  | "xpos"
  | "morphology"
  | "dependency"
  | "punctuation"
  | "closed_list"
  | "lexicon"
  | "heuristic"
  | "cross_sentence_heuristic"
  | "input_entity"
  | "unknown";
```

### 6.3 Feature metadata

Каждый нетривиальный feature должен быть traceable.

```typescript
interface FeatureMeta {
  evidence_refs: WordRef[];
  sources: FeatureSource[];
  confidence: Confidence;
}
```

Правила:

- `evidence_refs` всегда sentence-local;
- feature не должен ссылаться на raw payload за пределами предложения;
- если feature основан на heuristic, `sources` обязан включать `"heuristic"`;
- если feature требует внешнего контекста, extractor должен добавить diagnostic или `missing_context`.

## 7. Evidence layer

Evidence layer — обязательная основа matcher. Он делает output самодостаточным: matcher не обязан повторно читать `AnnotatedDocument`, чтобы проверить POS/morph/dependency evidence.

```typescript
interface EvidenceFeatures {
  words: TokenEvidence[];
  dependencies: DependencyEvidence[];
}

interface TokenEvidence {
  ref: WordRef;
  text: string;
  lower: string;
  lemma: string;
  upos: string;
  xpos?: string;
  feats: Record<string, string>;
  head: WordRef | 0;
  deprel: string;
  children: WordRef[];
  start_char: number;
  end_char: number;
  position: number; // 0-based
}

interface DependencyEvidence {
  governor: WordRef | 0;
  dependent: WordRef;
  deprel: string;
}
```

Rules:

- `feats` is parsed from UD-style string into an object;
- missing `feats` becomes `{}`;
- `children` is deterministically derived from `head`;
- `position` is derived from source order;
- `lower` is locale-independent lowercase for matcher normalization.

## 8. Morphology features

```typescript
interface MorphologyFeatures {
  word_morphology: MorphFeature[];
  normalized: NormalizedMorph[];
}
```

### 8.1 Word-level morphology

```typescript
interface MorphFeature {
  ref: WordRef;
  pos: string;
  xpos?: string;
  lemma: string;
  features: {
    VerbForm?: "Fin" | "Inf" | "Ger" | "Part";
    Tense?: "Past" | "Pres";
    Number?: "Sing" | "Plur";
    Person?: "1" | "2" | "3";
    Degree?: "Pos" | "Cmp" | "Sup";
    PronType?: string;
    Definite?: "Def" | "Ind";
    Mood?: string;
    Voice?: string;
    Aspect?: string;
    Case?: string;
    Poss?: string;
  };
}
```

### 8.2 Normalized morphology aliases

```typescript
interface NormalizedMorph {
  ref: WordRef;
  is_finite_verb: boolean;
  is_base_verb: boolean;
  is_to_infinitive: boolean;
  is_bare_infinitive: boolean;
  is_gerund: boolean;
  is_past_participle: boolean;
  is_present_participle: boolean;
  is_plural_noun: boolean;
  is_singular_noun: boolean;
  is_comparative: boolean;
  is_superlative: boolean;
}
```

Rules:

- normalized aliases must not contradict raw morphology;
- if raw morphology is missing or ambiguous, aliases may be `false` and diagnostics may explain the degraded extraction;
- suffix-only guesses, such as word ending in `-er`, must not create high-confidence comparative features.

## 9. Syntax features

```typescript
interface SyntaxFeatures {
  phrases: Phrase[];
  clauses: ClauseFeature[];
  predicates: PredicateFeature[];
  complements: PredicateComplementFeature[];
  coordination: Coordination[];
  subordination: ClauseMarkerFeature[];
  np_profiles: NPFeature[];
  pronouns: PronounFeature[];
  special_subject_constructions: SpecialSubjectConstructionFeature[];
  relative_clauses: RelativeClauseFeature[];
  conditionals: ConditionalFeature[];
  reported_speech: ReportedSpeechFeature[];
  passive: PassiveFeature[];
}
```

## 10. Phrase / chunk structure

```typescript
interface Phrase {
  type: "NP" | "VP" | "PP";
  head: WordRef;
  tokens: WordRef[];
}
```

Rules:

- `NP`: head `NOUN | PROPN | PRON` plus dependents `det`, `amod`, `compound`, `nummod`;
- `VP`: head `VERB | AUX` plus `aux`, `cop`, `obj`, `obl`, `advmod`, `neg`;
- `PP`: nominal head with `case` dependent;
- phrase tokens must be sorted by source position.

## 11. Roles and valency

```typescript
interface Roles {
  subject?: WordRef;
  object?: WordRef;
  indirect_object?: WordRef;
  oblique: WordRef[];
}

interface Valency {
  subject: boolean;
  object: boolean;
  indirect_object: boolean;
}
```

Mapping:

| Dependency | Feature |
| --- | --- |
| `nsubj`, `nsubj:pass` | `subject` |
| `obj` | `object` |
| `iobj` | `indirect_object` |
| `obl` | `oblique[]` |

## 12. Predicate features

Predicate features are the main bridge between syntax, morphology and grammar rules.

```typescript
interface PredicateFeature {
  id: string;
  main: WordRef;
  main_lemma: string;

  predicate_type:
    | "verbal"
    | "copular_adjectival"
    | "copular_nominal"
    | "copular_prepositional"
    | "existential_there"
    | "unknown";

  finite: boolean;

  auxiliaries: AuxiliaryFeature[];
  copula?: WordRef;
  negation?: WordRef;

  tense?: "present" | "past" | "future_like" | "none" | "unknown";
  aspect:
    | "simple"
    | "progressive"
    | "perfect"
    | "perfect_progressive"
    | "none"
    | "unknown";
  voice: "active" | "passive" | "unknown";
  modality?: ModalFeature;

  polarity: "positive" | "negative" | "mixed" | "unknown";
  clause_head: WordRef;

  subject?: WordRef;
  object?: WordRef;
  indirect_object?: WordRef;

  complements: PredicateComplementFeature[];
  agreement: AgreementFeature;

  tavm: TAVMFeature;
  form_signature: string;

  evidence_refs: WordRef[];
  confidence: Confidence;
}
```

### 12.1 Auxiliary chain

```typescript
interface AuxiliaryFeature {
  ref: WordRef;
  lemma: string;
  surface: string;
  role:
    | "tense_aux"
    | "perfect_aux"
    | "progressive_aux"
    | "passive_aux"
    | "do_support"
    | "modal"
    | "semi_modal"
    | "copula"
    | "unknown";
}
```

Rules:

- `have + past participle` may create `perfect_aux`;
- `be + present participle` may create `progressive_aux`;
- `be/get + past participle` may create passive features;
- `do/does/did` before lexical verb may create `do_support`;
- modal auxiliaries create `modal`;
- semi-modal patterns are represented in `ModalFeature`.

### 12.2 TAVM feature

```typescript
interface TAVMFeature {
  tense: "present" | "past" | "future_like" | "none" | "unknown";
  aspect:
    | "simple"
    | "progressive"
    | "perfect"
    | "perfect_progressive"
    | "none"
    | "unknown";
  voice: "active" | "passive" | "unknown";
  modality:
    | "ability"
    | "obligation"
    | "permission"
    | "advice"
    | "necessity"
    | "possibility"
    | "prohibition"
    | "prediction"
    | "expectation"
    | "past_habit"
    | "none"
    | "unknown";
  form_signature: string;
}
```

Example `form_signature` values:

```text
be_present_copular
present_simple_lexical
present_simple_do_negative
present_simple_do_question
present_progressive
present_perfect
present_perfect_progressive
past_simple
past_progressive
passive_be_participle
modal_base_verb
semi_modal_have_to
semi_modal_need_to
semi_modal_be_able_to
semi_modal_be_supposed_to
used_to_base
```

### 12.3 Agreement feature

```typescript
interface AgreementFeature {
  subject?: WordRef;
  predicate?: WordRef;
  controller?: WordRef;

  subject_person?: 1 | 2 | 3;
  subject_number?: "sing" | "plur";
  predicate_person?: 1 | 2 | 3;
  predicate_number?: "sing" | "plur";

  match?: boolean;
  agreement_type:
    | "subject_verb"
    | "subject_copula"
    | "demonstrative_noun"
    | "determiner_noun"
    | "existential_there_noun"
    | "unknown";

  evidence_refs: WordRef[];
  confidence: Confidence;
}
```

Rules:

- agreement compares clause-local subject and finite predicate/copula/controller morphology when available;
- missing morphology produces omitted fields, not extractor failure;
- `there is/are` agreement should prefer notional subject if detected.

## 13. Clause features

```typescript
interface ClauseFeature {
  id: string;
  head: WordRef;
  type:
    | "root"
    | "ccomp"
    | "xcomp"
    | "advcl"
    | "relcl"
    | "acl"
    | "participle"
    | "infinitive"
    | "conditional"
    | "reported_speech"
    | "unknown";

  finite: boolean;
  subject?: WordRef;
  predicate?: WordRef;

  marker?: ClauseMarkerFeature;
  roles: Roles;
  valency: Valency;

  semantic_relation?:
    | "time"
    | "reason"
    | "condition"
    | "purpose"
    | "result"
    | "contrast"
    | "relative"
    | "reported_content"
    | "unknown";

  tokens: WordRef[];
  local_tokens: WordRef[];
  confidence: Confidence;
}
```

Rules:

- `tokens` are the dependency subtree of the clause head, bounded to the current sentence;
- `local_tokens` exclude nested clausal subtrees and are used for local roles and valency;
- `semantic_relation` is heuristic unless directly licensed by a marker.

### 13.1 Clause marker / subordination

```typescript
interface ClauseMarkerFeature {
  marker_ref: WordRef;
  marker: string;
  clause_head: WordRef;
  marker_type:
    | "finite_subordinator"
    | "infinitive_to"
    | "prepositional_gerund"
    | "comparative_than"
    | "relative_pronoun"
    | "conditional_if"
    | "conditional_unless"
    | "reported_that"
    | "purpose_to"
    | "ambiguous"
    | "unknown";
  confidence: Confidence;
  sources: FeatureSource[];
}
```

Rule: `mark` dependents attached to clausal heads are represented as clause markers.

## 14. Complement features

```typescript
interface PredicateComplementFeature {
  governor: WordRef;
  head: WordRef;

  type:
    | "object_np"
    | "indirect_object_np"
    | "object_complement_adj"
    | "object_complement_np"
    | "subject_complement_adj"
    | "subject_complement_np"
    | "subject_complement_pp"
    | "to_infinitive"
    | "bare_infinitive"
    | "gerund"
    | "participle_clause"
    | "that_clause"
    | "wh_clause"
    | "prepositional_phrase"
    | "comparative_than_phrase"
    | "as_as_phrase"
    | "unknown";

  preposition?: string;
  marker?: string;
  deprel_source: string;
  evidence_refs: WordRef[];
  confidence: Confidence;
}
```

Mapping baseline:

| Dependency | Complement type |
| --- | --- |
| `obj` | `object_np` |
| `iobj` | `indirect_object_np` |
| `obl` with `case` | `prepositional_phrase` |
| `ccomp` | `that_clause` or `wh_clause` or generic finite clause |
| `xcomp` with `to` | `to_infinitive` |
| `xcomp` without `to` | `bare_infinitive` or generic nonfinite clause |

## 15. Noun phrase features

```typescript
interface NPFeature {
  id: string;
  head: WordRef;
  head_lemma: string;

  phrase_type:
    | "common_noun_np"
    | "proper_noun_np"
    | "pronoun_np"
    | "gerund_np"
    | "unknown";

  number?: "singular" | "plural" | "unknown";
  person?: 1 | 2 | 3;
  animacy?: "animate" | "inanimate" | "unknown";

  determiner?: DeterminerFeature;
  has_determiner: boolean;
  article_slot: ArticleSlotFeature;

  modifiers: ModifierFeature[];
  quantifiers: QuantifierFeature[];
  possessive?: WordRef;

  syntactic_role:
    | "subject"
    | "object"
    | "indirect_object"
    | "oblique"
    | "predicative_complement"
    | "appositive"
    | "unknown";

  countability?: CountabilityFeature;
  reference?: ReferenceFeature;

  evidence_refs: WordRef[];
  confidence: Confidence;
}

interface ModifierFeature {
  ref: WordRef;
  modifier_type:
    | "adjective"
    | "compound"
    | "number"
    | "possessive"
    | "relative_clause"
    | "prepositional_phrase"
    | "participle"
    | "unknown";
}
```

### 15.1 Determiner feature

```typescript
interface DeterminerFeature {
  ref: WordRef;
  text: string;
  lemma: string;
  determiner_type:
    | "article_definite"
    | "article_indefinite"
    | "demonstrative"
    | "possessive"
    | "quantifier"
    | "number"
    | "negative_no"
    | "interrogative"
    | "none"
    | "unknown";
  definite?: boolean;
  number?: "singular" | "plural" | "both" | "unknown";
}
```

### 15.2 Article slot feature

```typescript
interface ArticleSlotFeature {
  requiredness:
    | "article_present"
    | "zero_article"
    | "determiner_present"
    | "missing_required_determiner_candidate"
    | "not_applicable"
    | "unknown";

  article_form?: "a" | "an" | "the" | "zero";
  following_sound_class?: "vowel_sound" | "consonant_sound" | "unknown";
  following_spelling_class?: "vowel_letter" | "consonant_letter" | "unknown";

  definiteness?: "definite" | "indefinite" | "generic" | "unknown";
}
```

Rules:

- `following_spelling_class` is deterministic from text;
- `following_sound_class` is `unknown` unless a closed pronunciation list or phonology adapter is configured;
- article choice based only on spelling must not be high confidence.

### 15.3 Countability feature

```typescript
interface CountabilityFeature {
  value:
    | "count_singular"
    | "count_plural"
    | "uncountable"
    | "proper_name"
    | "dual_use"
    | "unknown";
  source: "morphology" | "lexicon" | "heuristic" | "unknown";
  confidence: Confidence;
}
```

### 15.4 Reference feature

```typescript
interface ReferenceFeature {
  reference_status:
    | "first_mention_candidate"
    | "previously_mentioned_candidate"
    | "unique_world_knowledge_candidate"
    | "situationally_identifiable_candidate"
    | "generic_class_reference_candidate"
    | "specific_reference_candidate"
    | "unknown";

  evidence:
    | "same_lemma_previous_sentence"
    | "definite_article"
    | "unique_noun_whitelist"
    | "plural_generic_subject"
    | "context_unavailable"
    | "unknown";

  confidence: Confidence;
}
```

Rules:

- this is heuristic and must not be used as final coreference truth;
- if context is unavailable, use `unknown` or low-confidence candidate;
- deep discourse analysis remains out of scope.

## 16. Noun inflection / plural formation features

```typescript
interface NounInflectionFeature {
  ref: WordRef;
  lemma: string;
  surface: string;
  number: "singular" | "plural" | "unknown";

  plural_pattern?:
    | "regular_s"
    | "es_after_sibilant"
    | "consonant_y_to_ies"
    | "f_fe_to_ves"
    | "irregular"
    | "zero_plural"
    | "foreign_plural"
    | "unknown";

  expected_plural?: string[];
  is_plural_error_candidate?: boolean;
}
```

`NounInflectionFeature` should be emitted in lexical features or as part of NP enrichment when noun number is relevant.

## 17. Pronoun features

```typescript
interface PronounFeature {
  ref: WordRef;
  lemma: string;
  pronoun_type:
    | "personal_subject"
    | "personal_object"
    | "possessive_determiner"
    | "possessive_pronoun"
    | "reflexive"
    | "relative"
    | "interrogative"
    | "demonstrative"
    | "indefinite"
    | "dummy_it"
    | "existential_there"
    | "unknown";

  person?: 1 | 2 | 3;
  number?: "singular" | "plural";
  case?: "subject" | "object" | "possessive" | "unknown";
}
```

## 18. Lexical / heuristic features

Lexical features are deterministic in implementation but linguistically approximate. They must carry confidence and sources.

```typescript
interface LexicalFeatures {
  sentence: SentenceFeature;
  word_order: WordOrderFeature[];
  negation: NegationFeature[];
  time_markers: TimeMarkerFeature[];
  lexical_classes: LexicalClassFeature[];
  verb_patterns: VerbPatternFeature[];
  adjective_patterns: AdjectivePatternFeature[];
  comparisons: ComparisonFeature[];
  quantifiers: QuantifierFeature[];
  phrasal_verbs: PhrasalVerbFeature[];
  discourse_markers: DiscourseMarkerFeature[];
  contractions: ContractionFeature[];
  noun_inflections: NounInflectionFeature[];
}
```

### 18.1 Sentence-level feature

```typescript
interface SentenceFeature {
  sentence_kind:
    | "normal"
    | "title"
    | "fragment"
    | "exclamation_fragment"
    | "quote"
    | "unknown";

  clause_count: number;

  sentence_type:
    | "declarative"
    | "yes_no_question"
    | "wh_question"
    | "tag_question"
    | "imperative"
    | "exclamative"
    | "short_answer"
    | "fragment"
    | "unknown";

  polarity: "positive" | "negative" | "mixed" | "unknown";

  has_subject_aux_inversion: boolean;
  has_do_support: boolean;
  has_wh_fronting: boolean;
  has_tag_question: boolean;
  has_exclamation_marker: boolean;
}
```

### 18.2 Word order feature

```typescript
interface WordOrderFeature {
  pattern:
    | "subject_verb_object"
    | "subject_aux_verb"
    | "aux_subject_verb"
    | "wh_aux_subject_verb"
    | "be_subject_complement"
    | "there_be_np"
    | "imperative_base_verb"
    | "negative_aux_not_verb"
    | "unknown";

  ordered_refs: WordRef[];
  confidence: Confidence;
}
```

### 18.3 Negation feature

```typescript
interface NegationFeature {
  ref: WordRef;
  negator: "not" | "n't" | "never" | "no" | "none" | "nothing" | "neither" | string;
  scope:
    | "predicate"
    | "noun_phrase"
    | "clause"
    | "sentence"
    | "unknown";
  governor?: WordRef;
  polarity_effect: "negative" | "negative_quantifier" | "unknown";
}
```

### 18.4 Time / aspect marker feature

```typescript
interface TimeMarkerFeature {
  refs: WordRef[];
  marker: string;
  type:
    | "now"
    | "current_period"
    | "habitual_frequency"
    | "past_finished_time"
    | "present_perfect_experience"
    | "present_perfect_result"
    | "duration_for"
    | "duration_since"
    | "future_time"
    | "sequence"
    | "deadline"
    | "unknown";

  normalized_value?: string;
  confidence: Confidence;
}
```

Examples:

```text
now, right now, at the moment
usually, often, every day, on Mondays
yesterday, last week, in 2020, ago
ever, never, already, yet, just
for, since, how long
tomorrow, next week, soon
```

### 18.5 Lexical class feature

```typescript
interface LexicalClassFeature {
  ref: WordRef;
  lemma: string;
  classes: (
    | "stative_verb"
    | "dynamic_verb"
    | "linking_verb"
    | "ditransitive_verb"
    | "reporting_verb"
    | "mental_state_verb"
    | "motion_verb"
    | "communication_verb"
    | "degree_adjective"
    | "gradable_adjective"
    | "absolute_adjective"
    | "frequency_adverb"
    | "time_adverb"
  )[];

  source: "closed_list" | "lexicon" | "heuristic";
  confidence: Confidence;
}
```

### 18.6 Verb pattern feature

```typescript
interface VerbPatternFeature {
  predicate: WordRef;
  lemma: string;

  pattern:
    | "verb_np"
    | "verb_np_np"
    | "verb_np_pp"
    | "verb_to_infinitive"
    | "verb_object_to_infinitive"
    | "verb_gerund"
    | "verb_that_clause"
    | "verb_wh_clause"
    | "verb_object_complement_adj"
    | "verb_object_complement_np"
    | "verb_particle_object"
    | "unknown";

  complements: PredicateComplementFeature[];
  confidence: Confidence;
}
```

### 18.7 Adjective pattern feature

```typescript
interface AdjectivePatternFeature {
  adjective: WordRef;
  lemma: string;

  pattern:
    | "adjective_to_infinitive"
    | "adjective_preposition_gerund"
    | "adjective_that_clause"
    | "too_adjective_to_infinitive"
    | "adjective_enough_to_infinitive"
    | "comparative_adjective_than"
    | "as_adjective_as"
    | "not_as_adjective_as"
    | "unknown";

  complement?: PredicateComplementFeature;
  degree_modifier?: WordRef;
  confidence: Confidence;
}
```

### 18.8 Comparison feature

```typescript
interface ComparisonFeature {
  type:
    | "comparative_er"
    | "comparative_more"
    | "comparative_less"
    | "superlative_est"
    | "superlative_most"
    | "equality_as_as"
    | "negative_equality_not_as_as"
    | "as_much_many_as"
    | "comparative_than"
    | "unknown";

  adjective_or_adverb?: WordRef;
  marker_refs: WordRef[];
  than_ref?: WordRef;
  standard_of_comparison?: WordRef[];

  semantic_relation:
    | "greater_degree"
    | "lower_degree"
    | "equal_degree"
    | "not_equal_degree"
    | "maximum_degree"
    | "unknown";

  confidence: Confidence;
}
```

### 18.9 Quantifier feature

```typescript
interface QuantifierFeature {
  ref: WordRef;
  text: string;
  quantifier_type:
    | "some"
    | "any"
    | "no"
    | "many"
    | "much"
    | "a_lot_of"
    | "few"
    | "little"
    | "enough"
    | "too_much"
    | "too_many"
    | "number"
    | "ordinal"
    | "unknown";

  compatible_number?: "singular" | "plural" | "uncountable" | "unknown";
  polarity_sensitivity?: "positive" | "negative_or_question" | "both" | "unknown";
}
```

### 18.10 Phrasal verb feature

```typescript
interface PhrasalVerbFeature {
  verb: WordRef;
  particle_ref: WordRef;
  particle: string;
  object_ref?: WordRef;
  separability:
    | "separated"
    | "adjacent"
    | "unknown";

  lemma_signature: string; // look_up, give_up, turn_on
  confidence: Confidence;
  sources: FeatureSource[];
}
```

### 18.11 Discourse marker feature

```typescript
interface DiscourseMarkerFeature {
  refs: WordRef[];
  marker: string;
  marker_type:
    | "contrast"
    | "addition"
    | "consequence"
    | "reason"
    | "condition"
    | "example"
    | "sequence"
    | "topic_shift"
    | "stance"
    | "unknown";

  clause_scope?: string;
  confidence: Confidence;
}
```

### 18.12 Contraction feature

```typescript
interface ContractionFeature {
  surface_ref: WordRef;
  surface: string;
  expansion:
    | "I am"
    | "he is"
    | "she is"
    | "it is"
    | "we are"
    | "they are"
    | "do not"
    | "does not"
    | "did not"
    | "will not"
    | "cannot"
    | "have"
    | "has"
    | "had"
    | "unknown";

  contraction_type:
    | "be_present"
    | "aux_negative"
    | "modal_negative"
    | "have_perfect"
    | "unknown";
}
```

## 19. Modality and semi-modal features

```typescript
interface ModalFeature {
  marker_refs: WordRef[];
  modal_type:
    | "can_ability"
    | "can_permission"
    | "could_ability"
    | "may_permission"
    | "must_obligation"
    | "must_deduction"
    | "should_advice"
    | "have_to_obligation"
    | "need_to_necessity"
    | "be_able_to_ability"
    | "be_supposed_to_expectation"
    | "used_to_past_habit"
    | "would_polite"
    | "will_prediction"
    | "unknown";

  complement_verb?: WordRef;
  polarity: "positive" | "negative";
  confidence: Confidence;
}
```

Rules:

- modal + base verb should produce high-confidence modal construction;
- semi-modal patterns require multi-token evidence;
- semantic distinction such as `must_obligation` vs `must_deduction` may be low/medium confidence unless context is explicit.

## 20. Special subject constructions

```typescript
interface SpecialSubjectConstructionFeature {
  type:
    | "existential_there"
    | "dummy_it_weather"
    | "dummy_it_extraposition"
    | "cleft_it"
    | "unknown";

  subject_ref: WordRef;
  predicate_ref: WordRef;
  notional_subject?: WordRef;
  agreement_controller?: WordRef;
  evidence_refs: WordRef[];
  confidence: Confidence;
}
```

## 21. Relative clause features

```typescript
interface RelativeClauseFeature {
  clause_id: string;
  head_noun: WordRef;
  relative_marker?: WordRef;
  marker_text?: "who" | "which" | "that" | "where" | "whose" | "whom";
  relative_type:
    | "subject_relative"
    | "object_relative"
    | "possessive_relative"
    | "place_relative"
    | "reduced_participle_relative"
    | "reduced_to_infinitive_relative"
    | "unknown";

  restrictive?: boolean;
  confidence: Confidence;
}
```

## 22. Conditional features

```typescript
interface ConditionalFeature {
  if_clause: string;
  main_clause: string;

  conditional_type:
    | "zero_conditional_candidate"
    | "first_conditional_candidate"
    | "second_conditional_candidate"
    | "third_conditional_candidate"
    | "mixed_conditional_candidate"
    | "unless_conditional"
    | "unknown";

  if_marker_ref?: WordRef;
  main_tavm: TAVMFeature;
  subordinate_tavm: TAVMFeature;

  confidence: Confidence;
}
```

## 23. Reported speech features

```typescript
interface ReportedSpeechFeature {
  reporting_verb: WordRef;
  reported_clause_head: WordRef;
  marker?: WordRef;

  report_type:
    | "that_clause"
    | "reported_question"
    | "reported_command"
    | "direct_quote"
    | "unknown";

  backshift_candidate: boolean;
  speaker_or_addressee_refs: WordRef[];
  confidence: Confidence;
}
```

## 24. Passive features

```typescript
interface PassiveFeature {
  predicate: WordRef;
  passive_type:
    | "be_passive"
    | "get_passive"
    | "modal_passive"
    | "perfect_passive"
    | "reduced_passive_participle"
    | "unknown";

  aux_refs: WordRef[];
  participle_ref: WordRef;
  agent_by_phrase?: WordRef[];
  patient_subject?: WordRef;

  confidence: Confidence;
}
```

## 25. Construction signatures

Construction signatures are the primary feature layer for `grammar_rule_matcher`.

They are **not** grammar rules. They are normalized, evidence-backed form signatures that make rule matching declarative.

```typescript
interface ConstructionFeature {
  key: string;
  family_hint?: string;

  type:
    | "tense_aspect"
    | "copular"
    | "existential"
    | "article_np"
    | "demonstrative_np"
    | "plural_noun"
    | "modal"
    | "passive"
    | "question"
    | "negation"
    | "comparison"
    | "subordination"
    | "relative_clause"
    | "conditional"
    | "gerund_infinitive"
    | "complement_pattern"
    | "reported_speech";

  signature: string;
  slots: Record<string, WordRef | WordRef[] | string | boolean | number>;
  evidence_refs: WordRef[];
  confidence: Confidence;
}
```

Example signatures:

```text
subject_be_present_complement
subject_be_present_not_complement
be_subject_complement_question
there_be_np
there_be_not_any_np
present_simple_lexical_affirmative
present_simple_do_negative
present_simple_do_question
present_progressive_affirmative
present_perfect_have_participle
present_perfect_ever_question
past_simple_regular
modal_must_base
semi_modal_be_able_to
passive_be_participle
to_infinitive_after_adjective
gerund_after_preposition
comparative_more_than
comparison_as_as
demonstrative_this_singular_np
article_indefinite_a_np
article_indefinite_an_np
article_definite_the_np
zero_article_plural_generic_candidate
```

Rules:

- construction signatures should be stable identifiers;
- signatures may be broader than individual `grammar_rule` atoms;
- signatures must include `slots` so matcher can verify role-specific constraints;
- signatures must never encode pedagogical level, learning objective, examples or contrastive decision.

## 26. Contrastive support features

Contrastive support features help `contrastive_rule_matcher`, but they do not make final pedagogical decisions.

```typescript
interface ContrastiveSupportFeature {
  contrastive_hint:
    | "present_simple_vs_present_progressive"
    | "present_perfect_vs_past_simple"
    | "a_vs_an"
    | "a_an_vs_the"
    | "article_vs_zero_article"
    | "singular_vs_plural"
    | "this_that_vs_these_those"
    | "comparative_vs_as_as"
    | "some_vs_any"
    | "much_vs_many"
    | "gerund_vs_infinitive"
    | "unknown";

  observed_choice: string;
  competing_choices: string[];

  local_cues: string[];
  missing_context: string[];

  confidence: Confidence;
}
```

Example:

```json
{
  "contrastive_hint": "present_simple_vs_present_progressive",
  "observed_choice": "present_progressive",
  "competing_choices": ["present_simple"],
  "local_cues": ["be + V-ing", "now"],
  "missing_context": ["intended meaning: habitual vs ongoing"],
  "confidence": "medium"
}
```

Rules:

- if intended meaning is required, `missing_context` must say so;
- contrastive support may propose candidates but must not output final `choose/reject`;
- high confidence is allowed only when the contrast is form-local and evidence is explicit, for example `a` vs `an` with a trusted phonology source.

## 27. Absence features

Absence features represent meaningful absence, which is needed for zero article, missing determiner candidates, imperatives, bare infinitives and ellipsis-like patterns.

```typescript
interface AbsenceFeature {
  scope:
    | "np"
    | "predicate"
    | "clause"
    | "sentence";

  target:
    | "determiner"
    | "article"
    | "auxiliary"
    | "subject"
    | "object"
    | "negation"
    | "preposition"
    | "relative_marker";

  expected_position?: "before_head" | "after_aux" | "before_clause" | "unknown";
  anchor_ref: WordRef;
  confidence: Confidence;
}
```

Rules:

- absence features must always have an anchor;
- absence must be derived from a bounded local structure;
- absence of discourse context is not an absence feature; it is diagnostic or `missing_context`.

## 28. Diagnostics

Diagnostics explain degraded extraction without failing the whole sentence.

```typescript
interface FeatureDiagnostic {
  severity: "info" | "warning" | "error";
  code:
    | "missing_word_evidence"
    | "ambiguous_pos"
    | "ambiguous_clause_boundary"
    | "ambiguous_participle"
    | "ambiguous_article_reference"
    | "requires_discourse_context"
    | "requires_intended_meaning"
    | "requires_phonology"
    | "requires_countability_lexicon"
    | "competing_rule_candidates"
    | "unsupported_feature"
    | "internal_feature_error"
    | string;
  message: string;
  refs: WordRef[];
  feature_path?: string;
}
```

Rules:

- extractor should prefer graceful degradation over failure for sentence-local feature issues;
- schema-level input violations remain expected data errors;
- diagnostics are deterministic and must not include sensitive raw payload beyond sentence-local evidence already present in input;
- `requires_discourse_context`, `requires_intended_meaning`, `requires_phonology`, `requires_countability_lexicon` should be emitted whenever matcher quality would otherwise be overstated.

## 29. Determinism and graceful degradation

Design principles:

1. deterministic-first: rule-based extraction where possible;
2. parser-aligned: features must not contradict dependency graph;
3. graceful degradation: failure to derive one feature should not fail the whole sentence;
4. traceability: every feature reference points to sentence-local `WordRef` evidence;
5. isolation: extractors for feature groups are independently testable;
6. no hidden state: no time, randomness, environment reads, global mutable caches in `core`;
7. matcher-readiness: every feature needed for rule matching should be represented as structured data, not only as prose;
8. uncertainty is explicit: heuristic features carry confidence and missing context.

Quality expectations:

| Feature group | Expected reliability |
| --- | ---: |
| evidence | 98–100% |
| morphology | 90–98% |
| syntax | 85–95% |
| predicate / clause / NP constructions | 80–95% |
| lexical closed-list features | 75–90% |
| lexical / semantic heuristics | 50–80% |
| contrastive support hints | 40–80% depending on context |

These numbers are non-formal expectations. Coq specification covers schema, determinism, reference integrity, paging and CLI contracts, not linguistic accuracy.

## 30. Matcher-oriented priority levels

### P0 — required for high-quality `grammar_rule_matcher`

- `evidence.words`;
- parsed morphology as object, not raw `feats`;
- normalized morphology aliases;
- predicate features with normalized TAVM;
- subject/object/complement roles;
- NP features with determiner/article/number;
- sentence type, polarity and inversion;
- construction signatures;
- confidence and evidence refs;
- diagnostics.

### P1 — strongly recommended

- article slot features;
- countability heuristic;
- plural formation patterns;
- time/aspect markers;
- modal/semi-modal features;
- complement pattern features;
- comparison features;
- absence features;
- contraction features.

### P2 — useful but heuristic

- reference status / first mention / known reference;
- generic vs specific NP;
- stative vs dynamic verb;
- intended meaning candidates;
- discourse-level heuristics.

P2 features must not be treated as strict truth. They are candidate signals for matchers and diagnostics.

## 31. Configuration

```typescript
interface ExtractorConfig {
  include_diagnostics: boolean;
  include_evidence: boolean;
  include_construction_signatures: boolean;
  include_contrastive_support: boolean;
  enable_heuristics: boolean;
  debug: boolean;
}

interface PagingConfig {
  page_number: number; // default = 1
  page_size: number;   // default = 300
}
```

Config resolution priority:

1. CLI args;
2. ENV, if explicitly documented by implementation;
3. defaults.

Defaults:

```json
{
  "include_diagnostics": true,
  "include_evidence": true,
  "include_construction_signatures": true,
  "include_contrastive_support": true,
  "enable_heuristics": true,
  "debug": false,
  "page_number": 1,
  "page_size": 300
}
```

Validation:

- `page_number >= 1`;
- `page_size >= 1`;
- disabling `include_evidence` is allowed only for compact output modes and must be documented as unsuitable for full matcher operation;
- if `enable_heuristics = false`, heuristic-only features should be omitted and diagnostics may explain omitted capabilities;
- unsupported config keys in strict CLI mode are expected configuration errors;
- config resolution must be deterministic.

## 32. Public Python API

Public API is exported only through `grammar_feature_extractor.__init__`.

```python
from grammar_feature_extractor import (
    AnnotatedDocument,
    ExtractorConfig,
    FeatureExtractionError,
    GrammarFeatureDocument,
    GrammarFeatureExtractor,
    GrammarFeaturePage,
    InputValidationError,
    PagingConfig,
)
```

Suggested API:

```python
class GrammarFeatureExtractor:
    def extract(
        self,
        document: AnnotatedDocument,
        config: ExtractorConfig | None = None,
    ) -> GrammarFeatureDocument:
        """Extract deterministic grammar features from an AnnotatedDocument."""

    def extract_page(
        self,
        document: AnnotatedDocument,
        paging: PagingConfig | None = None,
        config: ExtractorConfig | None = None,
    ) -> GrammarFeaturePage:
        """Extract features and return a deterministic paginated page."""
```

Python requirements:

- full public API typing;
- `mypy --strict`;
- no `Any` in public API;
- `black`, max line length `88`;
- `ruff` rules `E`, `F`, `I`, `B`;
- no wildcard imports;
- custom exceptions only;
- `logging` only, no `print`;
- IO separated from business logic;
- dependency injection for serializer/logger/runtime adapters;
- unit tests without external IO for `core`.

## 33. CLI contract

CLI should support:

```text
grammar-feature-extractor \
  --input annotated_document.json \
  --output features.page.json \
  --page 1 \
  --page-size 300 \
  --debug
```

Arguments:

| Argument | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--input` | no | `stdin` | JSON `AnnotatedDocument` input file |
| `--output` | no | `stdout` | JSON `GrammarFeaturePage` output file |
| `--page` | no | `1` | 1-based page number |
| `--page-size` | no | `300` | number of sentences per page |
| `--no-evidence` | no | false | compact mode, not suitable for full matcher |
| `--no-heuristics` | no | false | disable heuristic-only features |
| `--debug`, `-d` | no | false | debug observability only |

Output streams:

- `stdout` — only serialized `GrammarFeaturePage`, unless `--output` is set;
- `stderr` — only logs and errors;
- if `--output` is set, `stdout` remains empty;
- errors never create partial `stdout` or partial output file.

Exit codes:

| Code | Meaning |
| ---: | --- |
| `0` | success |
| `1` | expected data/configuration error |
| `2+` | system/runtime error |

## 34. Serialization contract

JSON serialization must be stable:

- UTF-8;
- object key order fixed by schema order;
- arrays preserve source sentence order;
- no nondeterministic metadata such as timestamps;
- no debug data in result payload;
- diagnostics are part of result payload only when enabled and deterministic;
- logs are never mixed with JSON result.

## 35. Logging and debug

Logging is mandatory and performed via `logging`.

Log to `stderr`:

- resolved non-sensitive parameters;
- pipeline step start/end;
- input validation result;
- extraction start/end;
- feature group start/end if debug is enabled;
- pagination start/end;
- output write success;
- expected errors;
- system errors without leaking sensitive internals.

Debug mode:

- enabled by `--debug` / `-d` or `ExtractorConfig.debug`;
- may log intermediate extraction traces;
- must not alter `GrammarFeatureDocument`;
- must not alter `GrammarFeaturePage`;
- must not affect exit-code mapping;
- must not write debug content to `stdout`.

## 36. Error model

Only custom exceptions are part of public API.

```python
class FeatureExtractionError(Exception):
    """Base exception for grammar_feature_extractor."""

class InputValidationError(FeatureExtractionError):
    """AnnotatedDocument input contract was violated."""

class ConfigurationError(FeatureExtractionError):
    """Extractor or paging configuration is invalid."""

class SerializationError(FeatureExtractionError):
    """Input or output JSON serialization failed."""
```

Mapping:

| Error | CLI exit code | Stream |
| --- | ---: | --- |
| `InputValidationError` | `1` | `stderr` |
| `ConfigurationError` | `1` | `stderr` |
| `SerializationError` for invalid input JSON | `1` | `stderr` |
| output write failure | `2+` | `stderr` |
| unexpected system error | `2+` | `stderr` |

## 37. Formal Coq Specification

The authoritative formal specification lives in `coq/GrammarFeatureExtractorSpec.v`.

For `v3` it should model at least:

- `schema_version = grammar_feature_extractor.v3`;
- `WordRef` validity;
- evidence references;
- parsed morphology object shape;
- clause-local roles/valency;
- predicate groups and TAVM;
- NP profiles and article slots;
- construction signatures;
- absence anchors;
- diagnostics refs;
- pagination;
- determinism;
- CLI exit-code behavior.

Linguistic accuracy of heuristic features is not a Coq obligation. Coq should specify structural safety and determinism, not semantic correctness of English grammar analysis.

## 38. Coq ↔ Python Mapping

| Coq symbol | Python responsibility |
| --- | --- |
| `schema_version` | `SCHEMA_VERSION = "grammar_feature_extractor.v3"` |
| `AnnotatedDocument` | parsed and validated input from `stanza_annotator` JSON |
| `WordRef`, `valid_ref` | sentence-local 1-based references derived from `Sentence.words` |
| `TokenEvidence` | normalized copy of word-level evidence |
| `MorphFeature`, `NormalizedMorph` | parsed and normalized word morphology |
| `ClauseFeature`, `Roles`, `Valency` | `syntax.clauses[*]` with local roles and valency |
| `PredicateFeature`, `TAVMFeature`, `AgreementFeature` | `syntax.predicates[*]` with predicate-local morphology |
| `NPFeature`, `ArticleSlotFeature` | `syntax.np_profiles[*]` with determiner/article/countability evidence |
| `ConstructionFeature` | matcher-oriented construction signatures |
| `AbsenceFeature` | local structural absence with valid anchor |
| `FeatureDiagnostic` | diagnostics with valid refs and optional `feature_path` |
| `extract_core` | pure Python core function, no IO and no environment access |
| `paginate_feature_document` | pure pagination / slicing function |
| `debug_does_not_change_result` | debug changes observability only |
| `cli_exit_code_mapping` | CLI exit-code contract |

## 39. Testing obligations

Unit tests:

- validate input schema from `stanza_annotator`;
- reject raw text input;
- derive `WordRef` from sentence word order;
- verify every feature reference is sentence-local;
- verify evidence layer mirrors source `words` deterministically;
- verify parsed morphology from `feats`;
- verify normalized morphology aliases;
- verify syntax feature mappings for `nsubj`, `obj`, `iobj`, `obl`, `aux`, `cop`, `neg`, `ccomp`, `xcomp`, `conj`, `mark`;
- verify predicate TAVM extraction;
- verify copular adjectival/nominal/prepositional predicates;
- verify existential `there` construction;
- verify NP profile extraction, determiner type and article slots;
- verify article spelling class and phonology-unknown behavior;
- verify countability heuristic confidence;
- verify plural formation patterns on fixed examples;
- verify sentence type, polarity and inversion;
- verify do-support;
- verify negation scope basics;
- verify time marker extraction on fixed examples;
- verify modal and semi-modal patterns;
- verify comparison features: `more`, `-er`, `as ... as`, `not as ... as`;
- verify phrasal verbs via `compound:prt`;
- verify discourse markers via deterministic whitelist;
- verify construction signatures on canonical examples;
- verify absence features with valid anchors;
- verify contrastive support emits `missing_context` when intended meaning is required;
- verify graceful degradation with diagnostics;
- verify `page_size = 300` default;
- verify configurable `--page-size`;
- verify empty page behavior for out-of-range pages;
- verify stable JSON serialization;
- verify debug mode does not change payload;
- verify stdout/stderr separation;
- verify exit-code mapping.

Property-based tests are recommended for:

- `WordRef` integrity;
- page slicing invariants;
- `features.length <= page_size`;
- deterministic extraction for the same input/config;
- stable serialization;
- debug/non-debug payload equivalence;
- every `evidence_refs` array containing only valid refs;
- every `AbsenceFeature.anchor_ref` being valid;
- construction signatures remaining stable for equivalent input.

Coq-related checks:

- maintain `GrammarFeatureExtractorSpec.v` as checked Coq/Rocq source;
- run `coqc GrammarFeatureExtractorSpec.v` in CI;
- fail CI if the specification no longer compiles;
- fail CI if a theorem is removed, weakened, or replaced by an unmarked assumption;
- require test coverage for every `Parameter` obligation in the Coq spec.

## 40. Evolution rules

A breaking change is any change that:

- changes input schema;
- changes output schema;
- changes paging semantics;
- changes default `page_size = 300`;
- changes public Python API;
- changes CLI contract;
- weakens `WordRef` integrity;
- weakens evidence traceability;
- weakens construction signature stability;
- weakens a proved Coq property;
- changes assumptions behind `extract_sentence_features_preserves_schema`.

Every breaking change requires:

- architecture update;
- test update;
- Coq specification update or explicit declaration that the previous proof no longer applies;
- changelog entry.

## 41. Definition of Done

The module is ready when:

- input is validated as `AnnotatedDocument` from `stanza_annotator`;
- raw text input is rejected;
- public API is minimal and exported only via `__init__.py`;
- public API is fully typed;
- `mypy --strict` passes;
- `ruff` and `black` pass;
- unit tests are deterministic and isolated from external IO;
- core contains no IO and no global state;
- feature extraction is deterministic;
- every feature reference is sentence-local;
- evidence layer is emitted by default;
- morphology is emitted as parsed object;
- predicate, clause and NP features are matcher-ready;
- construction signatures are emitted by default;
- contrastive support hints clearly mark missing context;
- absence features have valid anchors;
- diagnostics explain degraded extraction;
- CLI supports `--debug` / `-d`;
- CLI supports `--page`;
- CLI supports `--page-size` with default `300`;
- CLI keeps `stdout` and `stderr` separated;
- no partial result is emitted on error;
- debug mode does not change result payload;
- expected errors map to exit code `1`;
- system errors map to exit code `2+`;
- Coq specification compiles in CI;
- Coq theorem ↔ Python function mapping is maintained;
- implementation tests check all documented invariants.

## 42. Intended downstream usage

### 42.1 grammar_rule_matcher

Expected input:

```text
SentenceGrammarFeatures + grammar_rule.json -> RuleMatch[]
```

`grammar_rule_matcher` should primarily use:

- `evidence.words`;
- `morphology.normalized`;
- `syntax.predicates`;
- `syntax.clauses`;
- `syntax.np_profiles`;
- `lexical.sentence`;
- `lexical.word_order`;
- `constructions`;
- `absences`;
- `diagnostics`.

Minimal output shape:

```typescript
interface RuleMatch {
  rule_key: string;
  family_key: string;
  sentence_index: number;
  evidence_refs: WordRef[];
  confidence: Confidence;
  matched_features: string[];
  missing_features: string[];
  diagnostics: string[];
}
```

### 42.2 contrastive_rule_matcher

Expected input:

```text
SentenceGrammarFeatures
+ grammar_contrastive_rule.json
+ optional task/intended meaning/learner answer/target answer
-> ContrastiveRuleCandidate[] | ContrastiveDiagnosis[]
```

`contrastive_rule_matcher` should use `contrastive_support`, but final contrastive decisions require additional context for many rule families.

Suggested additional input:

```typescript
interface ContrastiveContext {
  exercise_prompt?: string;
  intended_meaning?: string;
  learner_answer?: string;
  target_answer?: string;
  previous_sentences?: string[];
}
```

Without this context, contrastive matcher should prefer candidates with `missing_context`, not final `choose/reject` claims.

---

## 43. Coq-proof surface for downstream matcher

This section strengthens the formal contract between `grammar_feature_extractor`, `grammar_rule_matcher`, `contrastive_rule_matcher`, and the Coq specification.

The extractor does not prove English grammar. It provides a deterministic, evidence-rich feature graph whose structural properties can be proved and then consumed by a proof-aware matcher.

### 43.1 Proof tiers

Every matcher-relevant feature belongs to exactly one proof tier:

| Tier | Meaning | Coq role |
| --- | --- | --- |
| `structural` | Directly derived from JSON shape, word order, refs, spans | Safe for strict soundness |
| `deterministic` | Derived by total deterministic functions from UPOS / morphology / dependencies | Safe for soundness relative to parser assumptions |
| `heuristic` | Deterministic but linguistically approximate | Usable only with explicit confidence / assumptions |
| `external_oracle` | Depends on lexicon, phonology, task context, world knowledge, discourse context | Requires explicit assumption boundary |

Only `structural` and `deterministic` tiers may be used for high-confidence Coq soundness theorems without extra assumptions. `heuristic` and `external_oracle` features must carry explicit provenance.

### 43.2 ProofProvenance

Every feature used by `grammar_rule_matcher` or `contrastive_rule_matcher` MUST expose provenance.

```typescript
interface ProofProvenance {
  tier: "structural" | "deterministic" | "heuristic" | "external_oracle";
  source:
    | "word_order"
    | "upos"
    | "xpos"
    | "morphology"
    | "dependency"
    | "surface"
    | "lemma"
    | "closed_list"
    | "lexicon"
    | "phonology"
    | "task_context"
    | "discourse_heuristic";
  evidence_refs: WordRef[];
  confidence: "high" | "medium" | "low";
}
```

Features without `ProofProvenance` MAY be serialized for debugging, but MUST NOT be used by proof-certified matching.

### 43.3 FeatureGraph invariants

For every `SentenceGrammarFeatures`:

1. all `WordRef` values are valid sentence-local refs;
2. every feature id is unique within its feature group;
3. every construction slot containing a `WordRef` points to an existing word;
4. every predicate subject/object/complement ref appears in the same sentence;
5. every NP head, determiner, modifier and quantifier ref is valid;
6. every clause head, marker and local token ref is valid;
7. every construction has non-empty `evidence_refs` unless it represents a documented absence feature;
8. `evidence_refs` are sorted, unique and valid;
9. all arrays are serialized in deterministic order;
10. unknown values are explicit enum values, not arbitrary strings;
11. missing optional evidence is represented by `null`, omitted field, or explicit `unknown`, never by invalid refs;
12. diagnostics refs are valid even when the diagnosed feature is degraded;
13. absence features have valid anchor refs;
14. contrastive support hints must list missing context when a final contrastive decision cannot be made.

These invariants are part of the proof surface and should be represented in Coq as `ValidFeatures` / `ValidSentenceFeatures`.

### 43.4 Closed enum discipline

Matcher-relevant fields MUST use closed enums or registry-backed identifiers.

Proof-relevant examples:

- `ConstructionSignature`;
- `PredicateType`;
- `SentenceType`;
- `Polarity`;
- `QuestionType`;
- `FeatureTier`;
- `Confidence`;
- `SourceKind`;
- `ComplementType`;
- `NPType`;
- `ArticleForm`;
- `CountabilityClass`.

Free-text fields such as `canonical_pattern`, `decision_condition`, `semantic_context`, `pragmatic_context` and examples are not part of the proof path.

### 43.5 Coq projection

The serialized JSON output has a deterministic projection into Coq/Rocq data:

```text
JSON GrammarFeaturePage
  -> Either DecodeError CoqGrammarFeaturePage
```

The projection must be total over schema-valid JSON, deterministic, rejecting unknown enum values, preserving `WordRef` validity, preserving deterministic ordering where ordering is semantically relevant, preserving schema version, preserving provenance, and preserving diagnostics without treating diagnostic wording as linguistic proof.

Suggested Coq-side shape:

```coq
Record ProofProvenance := {
  tier : FeatureTier;
  source : FeatureSource;
  evidence_refs : list WordRef;
  confidence : Confidence
}.

Record ConstructionFeature := {
  construction_id : string;
  signature : ConstructionSignature;
  slots : list SlotBinding;
  evidence_refs : list WordRef;
  provenance : ProofProvenance
}.

Record SentenceFeatures := {
  words : list WordEvidence;
  predicates : list PredicateFeature;
  np_profiles : list NPFeature;
  clauses : list ClauseFeature;
  constructions : list ConstructionFeature;
  absences : list AbsenceFeature;
  diagnostics : list FeatureDiagnostic
}.
```

### 43.6 Matcher-facing Coq obligations

The extractor specification SHOULD expose or support these theorems:

```coq
Theorem valid_word_refs_in_features :
  forall f ref,
    ValidFeatures f ->
    RefOccursInAnyFeature ref f ->
    ValidWordRef f ref.

Theorem construction_refs_are_valid :
  forall f c ref,
    ValidFeatures f ->
    In c f.(constructions) ->
    In ref c.(evidence_refs) ->
    ValidWordRef f ref.

Theorem predicate_refs_are_valid :
  forall f p ref,
    ValidFeatures f ->
    In p f.(predicates) ->
    PredicateMentionsRef p ref ->
    ValidWordRef f ref.

Theorem np_refs_are_valid :
  forall f np ref,
    ValidFeatures f ->
    In np f.(np_profiles) ->
    NPMentionsRef np ref ->
    ValidWordRef f ref.

Theorem evidence_refs_non_empty_for_positive_features :
  forall f feature,
    ValidFeatures f ->
    PositiveFeature feature ->
    In feature (all_features f) ->
    feature.(evidence_refs) <> [].

Theorem feature_ids_unique :
  forall f,
    ValidFeatures f ->
    FeatureIdsUniqueWithinGroups f.

Theorem extraction_is_deterministic :
  forall doc cfg,
    extract_core doc cfg = extract_core doc cfg.

Theorem pagination_preserves_sentence_features :
  forall doc cfg paging page,
    paginate (extract_core doc cfg) paging = page ->
    PageFeaturesAreStableSlice doc cfg paging page.

Theorem debug_does_not_change_features :
  forall doc cfg,
    extract_core doc cfg = extract_core doc (with_debug_toggled cfg).
```

### 43.7 Assumption boundary

Coq proofs over extractor output are relative to these assumptions:

- upstream parser annotations are accepted as input facts;
- external lexicons are trusted only through explicit provenance;
- phonology / sound class is an external oracle unless implemented as a deterministic closed list;
- discourse/coreference/intended meaning are not extractor responsibilities;
- CEFR and reference alignment are pedagogical metadata, not formal proof facts.

### 43.8 No free-text in proof path

Proof-certified matching may depend only on closed enums, stable construction signatures, valid `WordRef`s, normalized morphology, normalized dependency roles, machine-readable constraints from rule catalogs, and explicit provenance/confidence.

### 43.9 Catalog validation integration

Before matcher proofs are applied, rule catalogs must pass validation against extractor schema:

1. every feature path used by a rule exists;
2. every construction signature used by a rule is registered;
3. every enum value used by a rule is known;
4. every slot referenced by a rule can be bound from extractor output;
5. every required feature tier is available or explicitly assumed;
6. every rule declares whether heuristic / external features are allowed;
7. contrastive diagnosis rules declare task context requirements;
8. canonical JSON serialization is stable.

### 43.10 Generated Coq catalog

For strongest guarantees, validated JSON catalogs may be converted into checked Coq source:

```text
GeneratedGrammarRules.v
GeneratedContrastiveRules.v
GeneratedExtractorSchema.v
```

Each generated file SHOULD include source schema version, source catalog content hash, generated definitions using Coq ADTs rather than raw strings, theorem `all_rules_valid` or `all_contrastive_rules_valid`, and no timestamp inside proof-relevant definitions.

### 43.11 Target matcher theorems

The downstream matcher should target these theorems:

```coq
Theorem grammar_rule_match_sound :
  forall f r m,
    ValidFeatures f ->
    ValidGrammarRule r ->
    match_grammar_rule f r = Some m ->
    SatisfiesGrammarRule f r m.

Theorem grammar_rule_match_complete_for_hard_constraints :
  forall f r,
    ValidFeatures f ->
    ValidGrammarRule r ->
    SatisfiesHardConstraints f r ->
    exists m, match_grammar_rule f r = Some m.

Theorem contrastive_candidate_sound :
  forall f cr c,
    ValidFeatures f ->
    ValidContrastiveRule cr ->
    match_contrastive_candidate f cr = Some c ->
    SatisfiesObservedChoiceConstraints f cr c.

Theorem contrastive_diagnosis_requires_context :
  forall f task cr d,
    match_contrastive_diagnosis f task cr = Some d ->
    HasRequiredTaskContext task cr.

Theorem match_evidence_refs_valid :
  forall f result ref,
    AnyMatchResult result ->
    In ref result.(evidence_refs) ->
    ValidWordRef f ref.
```

### 43.12 Evolution rule for proof surface

A breaking proof-surface change includes changing a proof-relevant enum, removing or renaming a construction signature, weakening `WordRef` integrity, changing provenance semantics, allowing free text into proof-certified matching, changing ambiguity behavior, changing task-context requirements for contrastive diagnosis, or weakening a Coq theorem.

Every such change requires architecture update, rule catalog schema update, matcher spec update, Coq spec update, and migration note for existing JSON catalogs.

## 44. Production output-dir mode for grammar_extractor integration

The existing single-page CLI mode remains valid. For integration with `grammar_extractor` and `grammar_rule_detector`, the module SHOULD also support a production `--output-dir` mode that writes all `GrammarFeaturePage` files plus a manifest.

Recommended command:

```text
grammar-feature-extractor \
  --input filtered_annotated_document.json \
  --output-dir grammar_features \
  --page-size 300 \
  --debug
```

Output layout:

```text
grammar_features/
  grammar_features.manifest.json
  grammar_features.page_00001.json
  grammar_features.page_00002.json
  ...
```

Manifest schema:

```typescript
interface GrammarFeatureManifest {
  schema_version: "grammar_feature_extractor.v3";
  kind: "grammar_feature_manifest";
  page_size: number;
  page_count: number;
  total_sentences: number;
  pages: GrammarFeatureManifestPage[];
  diagnostics: FeatureDiagnostic[];
}

interface GrammarFeatureManifestPage {
  page_number: number;
  file_name: string;
  sentence_start: number;
  sentence_end_exclusive: number;
  sha256: string;
}
```

Rules:

- page numbers are 1-based;
- page filenames use zero padding width at least 5;
- lexical filename sorting must equal page order;
- pages are written atomically;
- manifest is written last;
- page ranges must be gap-free and non-overlapping;
- `page_size` default remains `300`;
- an empty input document must produce exactly one valid empty page;
- `--output-dir` is mutually exclusive with single-page `--output` unless explicitly documented otherwise;
- debug mode must not alter page contents or manifest hashes.

This addition lets `grammar_rule_detector` consume feature pages directly and lets `grammar_extractor` avoid reimplementing page materialization when using the CLI dependency mode.
