# grammar_feature_extractor architecture v5 committed contract

> Document revision: `v5`  
> Runtime/output schema version: `grammar_feature_extractor.v5`  
> Status: corrected implementation contract for code generation and tests.

This revision is the normalized v5 documentation contract and supersedes earlier grammar_feature_extractor architecture documents where conflicts exist.

## v5 contract repair summary

1. **Grammatical person fields are JSON integers.** `AgreementFeature.subject_person`, `AgreementFeature.predicate_person`, `NPFeature.person`, and `PronounFeature.person` serialize as `1 | 2 | 3`. UD morphology `MorphFeature.features.Person` remains a string enum `"1" | "2" | "3"` because it mirrors UD `feats`.
2. **Construction slots are registry-typed.** `ConstructionFeature.slots` still has a broad JSON Schema shape, but `construction_signature_registry.v5.json` now defines `slots[]` with `name`, `required`, `value_type`, and optional `allowed_values`. Signature-specific validation is mandatory semantic validation.
3. **Registry files have meta-schemas.** The following are committed and normative: `diagnostic_registry.v5.schema.json`, `construction_signature_registry.v5.schema.json`, `predicate_form_signature_registry.v5.schema.json`, `feature_path_registry.v5.schema.json`, and `semantic_validation_registry.v5.schema.json`.
4. **Feature path registry is upgraded.** Each path defines `value_type`, optional `enum_values`, `cardinality`, `proof_relevant`, `allowed_operators`, `stable_since`, and `deprecated_since`.
5. **Raw and resolved config are separated.** `grammar_feature_config.v5.schema.json` validates only resolved config. `grammar_feature_config.input.v5.schema.json` exists for explicit future raw config input, but v5 CLI still MUST NOT expose `--config` until that behavior is enabled by a versioned contract update.
6. **Default resolved config is a fixture.** `fixtures/grammar_feature_extractor/v5/default_resolved_config.json` is the canonical source of default values. It MUST validate against `grammar_feature_config.v5.schema.json`.
7. **Semantic validation is part of the contract.** JSON Schema validation is necessary but not sufficient. The implementation MUST perform semantic validation for input dependency graphs, feature graph refs, construction slots, diagnostics, config relationships, and manifest page ranges/hashes.
8. **Fatal diagnostics are not serialized as successful output.** Diagnostics whose registry entry has `result_impact = "extraction_failed"` MUST be converted to exceptions before serialization.
9. **Schema bundling drift is forbidden.** `grammar_feature_common.v5.schema.json` is the source of shared definitions. Bundled page/document/manifest/diagnostics schemas MUST be generated from, or byte-compared against, the common `$defs`.
10. **TypeScript-like snippets are not normative unless marked.** All older interface snippets below are explanatory excerpts unless explicitly marked `normative projection`. For implementation, generate models from JSON Schemas or prove model/schema conformance.

## v5 schema inventory

Additional files introduced by v5:

- `schema/diagnostic_registry.v5.schema.json`
- `schema/construction_signature_registry.v5.schema.json`
- `schema/predicate_form_signature_registry.v5.schema.json`
- `schema/feature_path_registry.v5.schema.json`
- `schema/grammar_feature_config.input.v5.schema.json`
- `schema/semantic_validation_registry.v5.json`
- `schema/semantic_validation_registry.v5.schema.json`
- `fixtures/grammar_feature_extractor/v5/default_resolved_config.json`


### Semantic validation registry detail contract

`schema/semantic_validation_registry.v5.json` is a machine-testable fatal/recoverable semantic validation contract. Every code entry MUST declare `when_emitted`, `affected_entity`, `message_template`, `required_details`, and `test_case`. Tests MUST assert the declared `required_details` fields instead of relying on message text alone.

## Applicable standards and precedence

For `grammar_feature_extractor.v5`, implementation agents and test generators MUST resolve conflicts in this order:

1. committed JSON Schemas, registries, and required fixtures under `docs/architecture/schema/` and `docs/architecture/fixtures/grammar_feature_extractor/v5/`;
2. this architecture document;
3. `docs/testing/grammar_feature_extractor_testing.md`;
4. generic guidelines under `docs/guidelines/`.

When a generic guideline conflicts with this module-specific v5 contract, the module-specific contract wins. In particular:

- v5 MUST NOT read environment variables for configuration;
- v5 CLI exit codes are exactly the module-specific exit codes in section `33.1`;
- serialized page/document/manifest `runtime_metadata` follows the compact schema projection, while `get_runtime_metadata()` follows the stage/orchestrator projection defined below;
- generic guidance is non-normative for this module when it would cause schema-invalid output.

## Grammatical person representation

All grammar feature person fields MUST use JSON integers:

```typescript
type GrammaticalPerson = 1 | 2 | 3;
```

Affected fields:

- `AgreementFeature.subject_person`
- `AgreementFeature.predicate_person`
- `NPFeature.person`
- `PronounFeature.person`

Required JSON Schema pattern:

```json
{
  "type": "integer",
  "enum": [1, 2, 3]
}
```

The UD morphology mirror field `MorphFeature.features.Person` intentionally remains:

```json
{
  "type": "string",
  "enum": ["1", "2", "3"]
}
```

## Construction slot validation

`ConstructionFeature.slots` validation is two-stage:

1. JSON Schema validates broad value shape and globally known slot names.
2. `construction_signature_registry.v5.json` validates selected-signature slot names, requiredness, value types, and allowed string values.

Normative slot spec:

```typescript
interface ConstructionSlotSpec {
  name: string;
  required: boolean;
  value_type:
    | "word_ref"
    | "word_ref_array"
    | "string"
    | "boolean"
    | "number";
  allowed_values?: string[];
}
```

Rules:

- all required slots for the selected `signature` MUST be present;
- slots not listed by the selected signature are invalid;
- `word_ref` and `word_ref_array` slots MUST be sentence-local and valid;
- string slots with `allowed_values` MUST use one of those values;
- invalid construction slot binding is a fatal output semantic validation error.

## Raw config vs resolved config

`schema/grammar_feature_config.v5.schema.json` validates only fully resolved config after defaults and explicit overrides.

`schema/grammar_feature_config.input.v5.schema.json` is a partial raw config schema for future explicit config-file/API config. v5 CLI still follows this restriction:

- MUST NOT read environment variables for configuration;
- MUST NOT read implicit config files;
- MUST NOT expose `--config` until a versioned contract enables it;
- unknown `--config` in v5 is a CLI usage error, exit `2`.

Canonical defaults live in:

```text
fixtures/grammar_feature_extractor/v5/default_resolved_config.json
```

## Public model implementation strategy

Committed decision for code generation:

- public data objects are immutable `dataclass(frozen=True, slots=True)` models or generated equivalents checked against JSON Schemas;
- raw JSON adapters MAY accept `dict[str, object]`;
- `core` accepts only validated model instances;
- public `extract()` and `extract_page()` accept validated `AnnotatedDocument` model instances, not arbitrary raw text or unvalidated dictionaries;
- helper adapters MAY be exposed for `load_annotated_document_json()` and `dump_feature_page_json()`.

## Semantic validation contracts

JSON Schema validation MUST be followed by semantic validation.

Required validator contracts:

```python
def validate_annotated_document_semantics(document: AnnotatedDocument) -> None: ...
def validate_resolved_config_semantics(config: ExtractorConfig) -> None: ...
def validate_feature_document_semantics(document: GrammarFeatureDocument) -> None: ...
def validate_feature_page_semantics(page: GrammarFeaturePage) -> None: ...
def validate_manifest_semantics(manifest: GrammarFeatureManifest, output_dir: Path) -> None: ...
def validate_diagnostic_against_registry(diagnostic: FeatureDiagnostic) -> None: ...
def validate_construction_against_registry(feature: ConstructionFeature) -> None: ...
```

These validators are test-contract APIs. They MAY be private implementation functions, but CI MUST exercise them.

### Input semantic validation codes

Stable validation codes are registry-backed in `semantic_validation_registry.v5.json`.

Required input codes include:

- `head_out_of_range`
- `missing_dependency_root`
- `dependency_cycle`
- `invalid_word_span`
- `invalid_entity_span`
- `token_words_mismatch`
- `sentence_text_empty`
- `sentence_words_empty`
- `unknown_input_field`

All input semantic validation failures map to `InputValidationError`, CLI `error_code = "input_validation_error"`, exit `1`.

### Output semantic validation

A schema-valid output is not necessarily proof-valid. Validators MUST check:

- every `WordRef` is valid within the sentence;
- every `evidence_refs` array is sorted, unique, and non-empty for positive matcher-facing features;
- every feature id is unique within its feature group;
- construction slots match the selected construction registry entry;
- every diagnostic ref is valid;
- every absence anchor is valid;
- page ranges are consistent with `features.length`;
- manifest ranges are sorted, gap-free, non-overlapping, and hash-verified.

## Diagnostic registry validation

Every emitted diagnostic MUST pass registry validation:

- `severity` MUST equal registry severity;
- `feature_path` MUST be present when `feature_path_required = true`;
- `refs` MUST be non-empty when `refs_required = true`;
- `result_impact` is obtained by registry lookup, not repeated ad hoc;
- diagnostics with `result_impact = "extraction_failed"` MUST be converted to exceptions before output serialization.

Fatal mapping:

| Diagnostic code | Exception | CLI error code | Exit |
|---|---|---|---:|
| `invalid_word_ref` semantic validation code | `FeatureExtractionError` | `unexpected_system_error` | 4 |
| `duplicate_feature_id` | `FeatureExtractionError` | `unexpected_system_error` | 4 |
| `output_page_too_large` | `SerializationError` | `output_serialization_error` | 1 |
| `required_resource_missing` | `ConfigurationError` | `configuration_error` | 1 |


### Semantic validation codes vs feature diagnostic codes

Output semantic validation failures are fatal implementation errors and are not serialized as successful `FeatureDiagnostic` objects. The canonical semantic validation code for an invalid generated `WordRef` is `invalid_word_ref` from `semantic_validation_registry.v5.json`.

Mapping:

- semantic validation code: `invalid_word_ref`;
- exception: `FeatureExtractionError`;
- CLI error code: `unexpected_system_error`;
- exit code: `4`;
- successful output: no page/document/manifest is serialized.

The diagnostic registry code `invalid_word_ref_generated` is retained only as a deprecated compatibility diagnostic identifier. It MUST NOT be emitted in successful output in v5 hardened implementations. Tests MUST assert the semantic validation code `invalid_word_ref` for fatal invalid-WordRef cases.

## Diagnostics limit policy

`max_diagnostics_per_sentence` behavior:

- `0` means diagnostics are suppressed and `features.diagnostics = []`;
- if positive and diagnostics exceed the limit, diagnostics are first sorted by deterministic diagnostic ordering;
- if limit is `1`, emit only `diagnostics_truncated`;
- if limit is `N > 1`, keep the first `N - 1` diagnostics and append `diagnostics_truncated`;
- `diagnostics_truncated` has no refs requirement and does not change CLI exit behavior.

Final ordering rule:

1. sort all original diagnostics by the standard diagnostic ordering;
2. if the limit is `0`, return `[]`;
3. if the limit is `1`, return exactly one synthetic `diagnostics_truncated` diagnostic;
4. if the limit is `N > 1`, keep the first `N - 1` original diagnostics and append one synthetic `diagnostics_truncated` diagnostic as the final item.

The synthetic `diagnostics_truncated` diagnostic is exempt from the normal diagnostic sort order and MUST remain the last diagnostic for the sentence.

## Manifest semantic validation

A manifest is valid only if:

- `page_count == len(pages)`;
- pages are sorted by `page_number` ascending;
- first page has `sentence_start = 0`;
- page ranges are gap-free and non-overlapping;
- last page `sentence_end_exclusive == total_sentences`;
- empty document has exactly one page with `sentence_start = sentence_end_exclusive = 0`;
- each page file exists and its SHA-256 matches canonical UTF-8 JSON bytes including the final newline.

## Feature path registry contract

Every feature path registry entry MUST define:

```typescript
interface FeaturePathRegistryEntry {
  path: string;
  value_type: "boolean" | "integer" | "number" | "string" | "enum" | "word_ref" | "word_ref_array" | "object" | "array";
  enum_values?: string[];
  cardinality: "one" | "optional" | "many";
  proof_relevant: boolean;
  allowed_operators: string[];
  stable_since: string;
  deprecated_since?: string | null;
}
```

Catalog validation MUST reject a rule that uses an unregistered feature path, an incompatible operator, or an unknown enum value.

## Resource hash policy

`RuntimeResource.sha256` may be `null` only for built-in resources whose bytes are embedded in the installed package and whose package version is reported by `version`.

For user-supplied or file-backed resources, `sha256` MUST be a lowercase 64-character SHA-256 hex digest.

`ExtractorRuntimeMetadata.resources` MUST be semantically unique by `(kind, name)`.


## Runtime metadata projection policy

For `grammar_feature_extractor.v5`, there are two metadata projections. They are related but not the same serialized object.

### Serialized output metadata

`GrammarFeaturePage.runtime_metadata`, `GrammarFeatureDocument.runtime_metadata`, and `GrammarFeatureManifest.runtime_metadata` MUST conform exactly to `schema/grammar_feature_common.v5.schema.json#/$defs/ExtractorRuntimeMetadata`. The serialized object contains only:

- `schema_version`;
- `extractor_version`;
- `resources`.

Additional stage-fingerprinting fields such as `stage_name`, `stage_contract_version`, `output_schema_version`, `config_contract_version`, `module_version`, `source_fingerprint`, `dependencies`, or `assets` MUST NOT be serialized into page/document/manifest outputs, because the output schemas use `additionalProperties: false`.

### Stage/orchestrator metadata

`GrammarFeatureExtractor.get_runtime_metadata()` MUST return a stage-metadata object compatible with `docs/guidelines/runtime_metadata_guideline.md`. It MUST include at least:

- `stage_name = "grammar_feature_extractor"`;
- `stage_contract_version = "grammar_feature_extractor.stage.v5"`;
- `output_schema_version = "grammar_feature_extractor.v5"`;
- `config_contract_version = "grammar_feature_extractor.config.v5"`;
- `module_version`;
- `source_fingerprint`;
- `dependencies`;
- `assets`.

The stage metadata object is for orchestration, reuse, provenance, and fingerprinting. It is not embedded directly in successful extractor output.

### Projection mapping

Every schema, registry, closed list, lexicon, phonology adapter, heuristic table, or other resource that affects extraction MUST appear in stage metadata `assets`. The serialized `runtime_metadata.resources` array is the stable public projection of those assets/resources and MUST include `name`, `kind`, `version`, `sha256` when file-backed, and `required`.

Determinism requirements:

- neither projection may contain absolute local paths;
- `source_fingerprint` and resource `sha256` values are computed from canonical bytes or package metadata, not current working directory;
- resource arrays are sorted by `(kind, name, version)` before serialization;
- no timestamps, random IDs, hostnames, usernames, or environment-derived values are allowed.

## Lowercase normalization

`TokenEvidence.lower` MUST be generated with Python `str.casefold()` rather than locale-dependent lowercasing. This field is for matcher normalization, not a display field.

## Schema bundling policy

`schema/grammar_feature_common.v5.schema.json` is the source of truth for shared `$defs`.

If document/page/manifest/diagnostics schemas inline `$defs`, they are generated artifacts. CI MUST verify that their `$defs` are byte-equivalent to the common source definitions after canonical JSON serialization.

Manual edits to bundled `$defs` are forbidden.

## Fixture release gate

Implementation is not production-ready until fixtures under `fixtures/grammar_feature_extractor/v5/` are committed and validated in CI.

Minimum committed fixtures in this v5 package:

- `default_resolved_config.json`
- `valid_minimal_input.json`
- `valid_empty_document_page.json`
- `valid_empty_document_manifest.json`
- CLI error examples for usage, input validation, output write, and unexpected system error
- selected invalid input/output examples

Full production implementation MUST include schema-valid, semantically valid positive golden output fixtures before production code generation. This package includes mandatory minimal golden fixtures for present-simple lexical and copular construction behavior; additional production fixtures are listed in section `49`.

---

# Full normative v5 contract body

The content below is the full v5 implementation contract after the 2026-05 documentation-readiness hardening pass. Earlier drafts called this section a retained previous body; that wording is now removed. All duplicate or explanatory snippets in this body are normative only when they match the precedence order below and the committed schemas/registries.

# grammar_feature_extractor architecture v5 committed contract

> Document revision: `v5`  
> Runtime/output schema version: `grammar_feature_extractor.v5`  
> Status: implementation contract for code generation and tests.

This revision hardens the original `grammar_feature_extractor_architecture.md` into a stricter implementation contract. It resolves the review blockers around authoritative JSON Schemas, public Python API, config gating, proof provenance, diagnostics, undefined feature types, CLI errors, canonical serialization, filesystem safety, limits, and registry-backed identifiers.

## 0. Normative status

The normative implementation contract consists of this Markdown document plus the committed schema and registry files under `schema/`.

The original TypeScript-like interfaces remain explanatory where they do not conflict with the committed JSON Schemas. In any conflict, the JSON Schema and registry files are authoritative for validation, code generation, fixtures, and downstream matcher compatibility.

Normative schema and registry files:

| File | Purpose |
|---|---|
| `schema/annotated_document.input.v5.schema.json` | accepted normalized `AnnotatedDocument` input envelope |
| `schema/grammar_feature_document.v5.schema.json` | full unpaged core output |
| `schema/grammar_feature_page.v5.schema.json` | paginated CLI/API output |
| `schema/grammar_feature_config.v5.schema.json` | resolved extractor and paging config |
| `schema/grammar_feature_manifest.v5.schema.json` | production output-dir manifest |
| `schema/grammar_feature_diagnostics.v5.schema.json` | standalone diagnostic collection |
| `schema/cli_error.v5.schema.json` | structured CLI stderr error object |
| `schema/diagnostic_registry.v5.json` | closed diagnostic code registry |
| `schema/construction_signature_registry.v5.json` | closed construction signature registry |
| `schema/predicate_form_signature_registry.v5.json` | closed predicate `form_signature` registry |
| `schema/feature_path_registry.v5.json` | stable matcher-facing feature paths |
| `schema/grammar_feature_common.v5.schema.json` | shared `$defs` used by generated models/tests |

All schemas use JSON Schema draft 2020-12. All object schemas MUST explicitly set `additionalProperties: false` unless the schema documents an intentional typed map. Intentional typed maps are limited to:

- `TokenEvidence.feats`, because parsed UD morphology is a string map;
- `ConstructionFeature.slots`, because slot names are constrained by `construction_signature_registry.v5.json` while values are typed.

## 0.1 Final decisions from documentation review

| Area | Committed decision |
|---|---|
| Schema authority | JSON Schemas and registries are normative. |
| Public API | `GrammarFeatureExtractor` API is normative, not suggested. |
| Config gating | Feature-group keys remain present; disabled groups are emitted empty and recorded in `output_completeness.omitted_feature_groups`. |
| Matcher completeness | Disabling evidence or matcher-critical groups sets `output_completeness.matcher_complete = false`. |
| Proof provenance | Every matcher-relevant positive feature includes `provenance: ProofProvenance`. |
| Diagnostics | Diagnostic codes are closed and registry-backed. |
| Construction signatures | Construction signatures are closed registry-backed identifiers. |
| Undefined output types | `Coordination`, feature IDs, form signatures, diagnostic schema, CLI errors and manifest pages are defined. |
| Free text | Proof-relevant fields use closed enums or registry-backed identifiers; surface strings are separated into `surface` fields. |
| CLI errors | CLI usage errors exit `2`; output write failures exit `3`; unexpected runtime/system errors exit `4`. |
| CLI stderr | Failure writes exactly one JSON `CliError` object to stderr; stdout remains empty. |
| Canonical JSON | UTF-8, no BOM, 2-space indentation, schema-order keys, final newline, `ensure_ascii=false`. |
| Output-dir mode | Production `--output-dir` is normative and atomic. |
| Limits | Input/output limits are explicit and configurable through resolved config. |
| Security | Output symlinks are rejected by default; manifest is written last; temp files are used for atomic writes. |

---

`grammar_feature_extractor` — модуль чистого извлечения грамматических признаков из уже готовых синтаксико-морфологических аннотаций.

Модуль преобразует `AnnotatedDocument`, полученный от `stanza_annotator`, в стабильный набор `GrammarFeatureSet` по каждому предложению. Он **не выполняет парсинг**, **не вызывает Stanza**, **не принимает raw text** и **не делает preprocessing**.

Начиная с версии `grammar_feature_extractor.v5`, output ориентирован не только на человекочитаемый feature dump, но и на последующий matcher:

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
| - write CliError to stderr on failure |
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

The accepted input is the normalized object validated by `schema/annotated_document.input.v5.schema.json`.

Required structural invariants:

- `schema_version` MUST equal `grammar_feature_extractor.annotated_document.input.v5`;
- `sentences` MUST be present and an array;
- `entities` MUST be present and an array;
- empty document is valid only as `sentences = []`, `entities = []`;
- each existing `AnnotatedSentence.text` MUST be non-empty;
- each existing `AnnotatedSentence.tokens` MUST be non-empty;
- each existing `AnnotatedSentence.words` MUST be non-empty;
- each `Token.words` MUST be non-empty;
- `Token.words` MUST be consistent with `AnnotatedSentence.words` by text/span order; implementations MUST validate this relation outside JSON Schema;
- `Word.text`, `Word.lemma`, `Word.upos`, and `Word.deprel` MUST be non-empty;
- `Word.head` MUST be an integer in range `0..len(sentence.words)`;
- `head = 0` means UD root and MUST NOT be used as `WordRef`;
- every non-empty sentence MUST contain at least one `head = 0` root;
- dependency cycles among non-root heads are invalid;
- character spans are 0-based half-open offsets `[start_char, end_char)`;
- `Word.start_char < Word.end_char` is required by validator even if JSON Schema cannot express cross-field comparison;
- entity spans MUST use the same half-open convention;
- unknown input fields are invalid;
- malformed optional `feats` values SHOULD degrade morphology extraction and emit diagnostic `malformed_morphology_feats` instead of failing the whole document.

Violations are expected data errors and map to `InputValidationError` / CLI exit code `1`.

## 5. Output contract

### 5.1 Schema version

```typescript
type GrammarFeatureSchemaVersion = "grammar_feature_extractor.v5";
```

`v5` is the first committed matcher-oriented schema version for this module revision.

All serialized extractor outputs MUST contain:

```json
"schema_version": "grammar_feature_extractor.v5"
```

All page/document/manifest outputs MUST also contain `kind`, `runtime_metadata`, and, where applicable, `output_completeness`.

### 5.1.1 Authoritative schemas

The authoritative machine-readable contracts are the committed files under `schema/` listed in Section `0`.

Schema files MUST be used by:

- input validation;
- output validation in tests;
- fixture validation;
- generated Python models or model conformance tests;
- downstream matcher contract tests;
- Coq projection tests.

A schema or registry change is breaking if it changes accepted input, serialized output, default config behavior, proof-relevant enums, construction signatures, paging semantics, diagnostic codes, or manifest layout.

### 5.2 Core output

`core` возвращает полный результат без paging.

```typescript
interface GrammarFeatureDocument {
  schema_version: "grammar_feature_extractor.v5";
  kind: "grammar_feature_document";
  runtime_metadata: ExtractorRuntimeMetadata;
  output_completeness: OutputCompleteness;
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

interface OutputCompleteness {
  matcher_complete: boolean;
  omitted_feature_groups: string[];
}

interface ExtractorRuntimeMetadata {
  schema_version: "grammar_feature_extractor.v5";
  extractor_version: string;
  resources: RuntimeResource[];
}

interface RuntimeResource {
  name: string;
  kind: "closed_list" | "lexicon" | "phonology" | "heuristic_table" | "registry" | "schema";
  version: string;
  sha256?: string | null;
  required: boolean;
}
```

### 5.3 Paginated CLI/API output

CLI выводит одну страницу features.

```typescript
interface GrammarFeaturePage {
  schema_version: "grammar_feature_extractor.v5";
  kind: "grammar_feature_page";
  runtime_metadata: ExtractorRuntimeMetadata;
  output_completeness: OutputCompleteness;
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

### 6.4 Proof provenance

Every matcher-relevant positive feature MUST expose explicit provenance.

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
  confidence: Confidence;
}
```

`confidence`, `sources`, and `evidence_refs` alone are not sufficient for proof-certified matching.

Required on all top-level feature objects in matcher-facing groups:

- morphology features;
- phrase, clause, predicate, complement, coordination, NP, pronoun and other syntax features;
- lexical features;
- construction features;
- contrastive support features;
- absence features.

Nested helper records such as `Roles`, `Valency`, and `TAVMFeature` do not need independent provenance if their parent feature has provenance and evidence refs.

### 6.5 Feature IDs

Every matcher-facing feature object MUST have deterministic sentence-local `id`.

Format:

```text
s{sentence_index}.{feature_group}.{ordinal}
```

Examples:

```text
s0.predicate.1
s0.clause.2
s0.np.3
s0.construction.4
```

Rules:

- `sentence_index` is 0-based;
- ordinals are 1-based within feature group;
- ordinals are assigned after deterministic sorting;
- IDs MUST be unique within a feature group;
- duplicate IDs are fatal internal errors and emit/raise `duplicate_feature_id`.

### 6.6 Output ordering

Arrays MUST be deterministic:

1. sentences: source sentence order;
2. word evidence: source word order;
3. dependencies: `(dependent, governor, deprel)` order;
4. morphology: source word order;
5. syntax and lexical feature arrays: primary evidence start position, then feature id;
6. construction features: signature registry order, then evidence start position, then feature id;
7. diagnostics: severity order `error`, `warning`, `info`, then feature path, then code.

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

### 9.1 Coordination

`SyntaxFeatures.coordination` is defined and schema-backed.

```typescript
interface Coordination {
  id: string;
  coordinator_ref?: WordRef;
  coordinator_text?: "and" | "or" | "but" | "nor" | "yet" | "so" | "unknown";
  conjunct_refs: WordRef[];
  head_ref: WordRef;
  coordination_type:
    | "np_coordination"
    | "vp_coordination"
    | "clause_coordination"
    | "adjective_coordination"
    | "adverb_coordination"
    | "unknown";
  evidence_refs: WordRef[];
  confidence: Confidence;
  provenance: ProofProvenance;
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

Diagnostic codes are closed for `grammar_feature_extractor.v5` and defined in `schema/diagnostic_registry.v5.json`.

```typescript
interface FeatureDiagnostic {
  severity: "info" | "warning" | "error";
  code: DiagnosticCode;
  message: string;
  refs: WordRef[];
  feature_path?: string;
}
```

Registry entry contract:

```typescript
interface DiagnosticRegistryEntry {
  code: string;
  severity: "info" | "warning" | "error";
  when_emitted: string;
  affected_entity: "document" | "sentence" | "word" | "feature" | "config" | "output";
  refs_required: boolean;
  feature_path_required: boolean;
  message_template: string;
  result_impact:
    | "none"
    | "feature_omitted"
    | "confidence_lowered"
    | "group_omitted"
    | "extraction_failed";
  cli_exit_code: 0 | 1 | 2 | 3 | 4;
  stable_since: string;
}
```

Rules:

- arbitrary diagnostic code strings are invalid;
- diagnostic wording is human-readable and SHOULD NOT be used as a stable test oracle;
- tests SHOULD assert `code`, `severity`, `refs`, `feature_path`, and `result_impact`, not full prose wording;
- feature diagnostics with severity `error` do not automatically fail CLI execution unless registry `result_impact = "extraction_failed"`;
- `requires_discourse_context`, `requires_intended_meaning`, `requires_phonology`, and `requires_countability_lexicon` MUST be emitted whenever matcher quality would otherwise be overstated.

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

The authoritative resolved config schema is `schema/grammar_feature_config.v5.schema.json`.

Unknown config keys are invalid in CLI and library mode.

Environment variables are not part of the v5 contract. Implementations MUST NOT read environment configuration in `core`. CLI MAY read only CLI arguments and an explicit config file if such option is later added by a versioned contract update.

```typescript
interface ExtractorConfig {
  schema_version: "grammar_feature_extractor.v5";
  include_diagnostics: boolean;
  include_evidence: boolean;
  include_construction_signatures: boolean;
  include_contrastive_support: boolean;
  enable_heuristics: boolean;
  debug: boolean;
  page_number: number;
  page_size: number;
  limits: ExtractorLimits;
}

interface ExtractorLimits {
  max_input_bytes: number;
  max_sentences: number;
  max_words_per_sentence: number;
  max_total_words: number;
  max_page_size: number;
  max_output_page_bytes: number;
  max_output_pages: number;
  max_diagnostics_per_sentence: number;
}
```

Defaults:

```json
{
  "schema_version": "grammar_feature_extractor.v5",
  "include_diagnostics": true,
  "include_evidence": true,
  "include_construction_signatures": true,
  "include_contrastive_support": true,
  "enable_heuristics": true,
  "debug": false,
  "page_number": 1,
  "page_size": 300,
  "limits": {
    "max_input_bytes": 104857600,
    "max_sentences": 200000,
    "max_words_per_sentence": 512,
    "max_total_words": 5000000,
    "max_page_size": 5000,
    "max_output_page_bytes": 104857600,
    "max_output_pages": 100000,
    "max_diagnostics_per_sentence": 100
  }
}
```

### 31.1 Feature group gating semantics

Config flags control emitted content, not schema shape.

`GrammarFeatureSet` MUST always contain these keys:

- `evidence`
- `morphology`
- `syntax`
- `lexical`
- `constructions`
- `contrastive_support`
- `absences`
- `diagnostics`

When a feature group is disabled:

- object-valued groups remain present with empty arrays inside;
- array-valued groups remain present as `[]`;
- disabled diagnostics are represented as `diagnostics: []`;
- disabled evidence is represented as:

```json
"evidence": {
  "words": [],
  "dependencies": []
}
```

The page/document MUST include disabled groups in `output_completeness.omitted_feature_groups`.

`include_evidence = false` is valid only for compact inspection output and MUST set `output_completeness.matcher_complete = false`.

`include_diagnostics = false` MAY suppress diagnostic payload but MUST NOT suppress fatal exceptions or CLI errors.

`enable_heuristics = false` MUST omit heuristic-only features. If diagnostics are enabled, omitted heuristic capabilities SHOULD emit `disabled_feature_group` or a more specific diagnostic.


## 32. Public Python API

The public Python API is normative.

The package MUST export exactly these public names from `grammar_feature_extractor.__init__`:

```python
from grammar_feature_extractor import (
    AnnotatedDocument,
    AnnotatedSentence,
    Token,
    Word,
    Entity,
    StageRuntimeAsset,
    StageRuntimeMetadata,
    ExtractorLimits,
    ExtractorConfig,
    PagingConfig,
    GrammarFeatureDocument,
    GrammarFeaturePage,
    GrammarFeatureManifest,
    GrammarFeatureExtractor,
    FeatureExtractionError,
    InputValidationError,
    ConfigurationError,
    SerializationError,
)
```

`ExtractorLimits`, `ExtractorConfig`, and `PagingConfig` MUST be immutable typed models. The resolved JSON config schema is the machine-readable persistence/normalization form of `ExtractorConfig + PagingConfig`; the Python constructor does not contain `schema_version`.

```python
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class StageRuntimeAsset:
    name: str
    kind: str
    version: str
    sha256: str | None
    required: bool

@dataclass(frozen=True, slots=True)
class StageRuntimeMetadata:
    stage_name: str
    stage_contract_version: str
    output_schema_version: str
    config_contract_version: str
    module_version: str
    source_fingerprint: str
    dependencies: tuple[str, ...]
    assets: tuple[StageRuntimeAsset, ...]

@dataclass(frozen=True, slots=True)
class ExtractorLimits:
    max_input_bytes: int = 104857600
    max_sentences: int = 200000
    max_words_per_sentence: int = 512
    max_total_words: int = 5000000
    max_page_size: int = 5000
    max_output_page_bytes: int = 104857600
    max_output_pages: int = 100000
    max_diagnostics_per_sentence: int = 100

@dataclass(frozen=True, slots=True)
class ExtractorConfig:
    include_diagnostics: bool = True
    include_evidence: bool = True
    include_construction_signatures: bool = True
    include_contrastive_support: bool = True
    enable_heuristics: bool = True
    debug: bool = False
    limits: ExtractorLimits = field(default_factory=ExtractorLimits)

@dataclass(frozen=True, slots=True)
class PagingConfig:
    page_number: int = 1
    page_size: int = 300
```

Canonical conversion from a resolved JSON config object:

```python
def config_from_resolved_json(raw: Mapping[str, object]) -> tuple[ExtractorConfig, PagingConfig]:
    # `raw` MUST already validate against grammar_feature_config.v5.schema.json.
    limits = ExtractorLimits(**raw["limits"])
    config = ExtractorConfig(
        include_diagnostics=raw["include_diagnostics"],
        include_evidence=raw["include_evidence"],
        include_construction_signatures=raw["include_construction_signatures"],
        include_contrastive_support=raw["include_contrastive_support"],
        enable_heuristics=raw["enable_heuristics"],
        debug=raw["debug"],
        limits=limits,
    )
    paging = PagingConfig(
        page_number=raw["page_number"],
        page_size=raw["page_size"],
    )
    return config, paging
```

Canonical API call:

```python
extractor.extract_page(
    document,
    paging=PagingConfig(page_number=1, page_size=300),
    config=ExtractorConfig(),
)
```

Normative extractor API:

```python
class GrammarFeatureExtractor:
    def extract(
        self,
        document: AnnotatedDocument,
        config: ExtractorConfig | None = None,
    ) -> GrammarFeatureDocument: ...

    def extract_page(
        self,
        document: AnnotatedDocument,
        paging: PagingConfig | None = None,
        config: ExtractorConfig | None = None,
    ) -> GrammarFeaturePage: ...

    def extract_pages(
        self,
        document: AnnotatedDocument,
        paging: PagingConfig | None = None,
        config: ExtractorConfig | None = None,
    ) -> list[GrammarFeaturePage]: ...

    def get_runtime_metadata(self) -> StageRuntimeMetadata: ...
```


### 32.1 `extract_pages()` semantics

`extract_pages(document, paging=None, config=None)` returns the complete deterministic page sequence for the whole document.

- `paging.page_size` controls page size.
- `paging.page_number` MUST be `1`; values greater than `1` are invalid and raise `ConfigurationError` because `extract_pages()` is an all-pages API.
- Empty input returns a list with exactly one empty `GrammarFeaturePage`.
- The number of returned pages MUST be `<= config.limits.max_output_pages`.
- `max_output_pages` is checked after page count is known and before any CLI output-dir writes.
- Page files generated by CLI `--output-dir` MUST be byte-identical to serializing these returned pages in order.

### 32.2 Adapter and exception import paths

The canonical public import path for all documented public classes and exceptions is `grammar_feature_extractor`. Helper adapters MAY be public only if exported from this package root; otherwise tests MUST treat them as implementation-private and use the CLI for JSON loading/dumping behavior.

Required public exception imports:

```python
from grammar_feature_extractor import (
    FeatureExtractionError,
    InputValidationError,
    ConfigurationError,
    SerializationError,
)
```

Library behavior:

- invalid input raises `InputValidationError`;
- invalid config or paging raises `ConfigurationError`;
- JSON encode/decode failures in helper adapters raise `SerializationError`;
- sentence-local feature degradation is represented as diagnostics, not failed result objects;
- unexpected implementation failures raise `FeatureExtractionError` or a subclass;
- methods perform no filesystem IO;
- methods are deterministic for the same input and config;
- methods do not mutate the input document;
- instances are stateless and safe to reuse across calls if no injected adapter has mutable state.

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

CLI MUST support single-page output and production output-dir mode.

Single-page command:

```text
grammar-feature-extractor   --input annotated_document.json   --output features.page.json   --page 1   --page-size 300   --debug
```

Arguments:

| Argument | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--input` | no | `stdin` | JSON `AnnotatedDocument` input file |
| `--output` | no | `stdout` | JSON `GrammarFeaturePage` output file |
| `--output-dir` | no | none | write all pages plus manifest |
| `--page` | no | `1` | 1-based page number |
| `--page-size` | no | `300` | number of sentences per page |
| `--no-evidence` | no | false | compact mode, not matcher-complete |
| `--no-heuristics` | no | false | disable heuristic-only features |
| `--debug`, `-d` | no | false | debug observability only |
| `--overwrite` | no | false | allow replacing existing output/output-dir contents according to filesystem policy |

### 33.1 CLI exit codes

| Code | Meaning |
|---:|---|
| `0` | success |
| `1` | input data, schema, or configuration error after valid CLI parsing |
| `2` | CLI usage error |
| `3` | output write failure |
| `4` | unexpected runtime/system error |

CLI argument parsing errors MUST exit with code `2`.

Validation order is strictly:

1. parse arguments and validate CLI syntax;
2. resolve CLI flags into the resolved config object;
3. validate resolved config schema and semantics;
4. read and validate input bytes/JSON/model;
5. extract features;
6. canonicalize, serialize, and write output.

Exit-code mapping for common CLI boundary cases:

- unknown CLI flag, missing option value, non-integer `--page`, non-integer `--page-size`, `--page < 1`, or `--page-size < 1`: `cli_usage_error`, exit `2`;
- `--output` used together with `--output-dir`: `cli_usage_error`, exit `2`;
- integer `--page-size > limits.max_page_size`: `configuration_error`, exit `1`, details `validation_code = "page_size_exceeds_max_page_size"`;
- `--input` path does not exist or is not a regular file: `input_validation_error`, exit `1`, details `validation_code = "input_file_not_found"` or `"input_not_regular_file"`;
- `--output` target is an existing directory: `output_write_error`, exit `3`;
- existing single-file `--output` without `--overwrite`: `output_write_error`, exit `3`;
- existing non-empty `--output-dir` without `--overwrite`: `output_write_error`, exit `3`.

### 33.2 Output streams

- success without `--output` and without `--output-dir`: `stdout` contains exactly one serialized `GrammarFeaturePage` JSON object followed by one newline;
- success with `--output` or `--output-dir`: `stdout` is empty;
- default success: `stderr` is empty unless `--log-file` is provided;
- failure: `stdout` is empty;
- failure: `stderr` contains exactly one serialized `CliError` JSON object followed by one newline;
- failure `stderr` MUST NOT contain log lines, stack traces, warnings, debug messages, or human-readable prefixes;
- failure MUST NOT leave a completed manifest.

### 33.3 CLI error serialization

On failure, CLI MUST write exactly one JSON error object to `stderr`, followed by exactly one newline, and leave `stdout` empty. The object MUST validate against `schema/cli_error.v5.schema.json`.

```typescript
interface CliError {
  schema_version: "grammar_feature_extractor.v5";
  kind: "cli_error";
  error_code:
    | "input_validation_error"
    | "configuration_error"
    | "input_json_serialization_error"
    | "output_serialization_error"
    | "output_write_error"
    | "cli_usage_error"
    | "unexpected_system_error";
  message: string;
  details?: Record<string, string | number | boolean | null>;
}
```

The machine-readable schema is `schema/cli_error.v5.schema.json`.

### 33.4 `CliError.details` minimum fields

`CliError.details` is optional only when no machine-actionable detail exists. When present, it MUST contain scalar values only, as enforced by `schema/cli_error.v5.schema.json`. Arrays and objects are forbidden in `details`.

Minimum detail fields by error family:

| CLI `error_code` | Required `details` fields when applicable | Notes |
|---|---|---|
| `input_json_serialization_error` | `reason`, optional `path` | `reason` is `malformed_json`, `non_utf8_input`, or `json_encode_failed`. |
| `input_validation_error` | `validation_code`, optional `json_path`, optional `path` | `validation_code` MUST be a semantic validation code or `schema_validation_failed`. Unknown fields use `unknown_input_field`. |
| `configuration_error` | `validation_code`, optional `config_path`, optional `argument` | `--page-size > limits.max_page_size` uses `page_size_exceeds_max_page_size` and `argument = "--page-size"`. |
| `output_serialization_error` | `validation_code`, optional `output_kind` | `max_output_page_bytes` uses `output_page_too_large`. |
| `output_write_error` | `reason`, optional `path`, optional `path_kind` | `reason` is one of `target_exists`, `target_is_directory`, `missing_parent`, `non_empty_output_dir`, `symlink_rejected`, `not_regular_file`, `write_failed`. |
| `cli_usage_error` | `argument`, optional `reason` | Syntax and mutually-exclusive argument failures only. |
| `unexpected_system_error` | `reason` | No stack traces or implementation internals by default. |

Path values, when emitted, MUST be the user-supplied CLI path or a repository-relative fixture path. Absolute local paths MUST NOT appear in golden fixtures or deterministic tests.


## 34. Serialization contract

All output JSON files MUST be serialized as canonical UTF-8 bytes:

- encoding: UTF-8;
- no BOM;
- final newline: yes;
- indentation: 2 spaces;
- object key order: schema order;
- array order: deterministic order defined by each feature group;
- `ensure_ascii = false`;
- no trailing whitespace;
- no timestamps;
- no environment-dependent values;
- no debug data in result payload.

Manifest `sha256` is computed over the exact canonical bytes of each final page file.

Logs are never mixed with JSON result.


## 35. Logging and debug

Logging is mandatory in the library implementation and performed via Python `logging`, but logs MUST NOT share the CLI JSON channels.

CLI logging policy:

- by default, the CLI emits no log lines to `stdout` or `stderr`;
- on failure, `stderr` is reserved exclusively for the single `CliError` JSON object;
- optional logs MAY be enabled only through a separate sink such as `--log-file PATH` or an injected library logger;
- log files may include resolved non-sensitive parameters, pipeline step start/end, input validation result, extraction start/end, feature group start/end when debug is enabled, pagination start/end, output write success, expected errors, and system errors without leaking sensitive internals;
- logs MUST NOT include full input payloads, generated full output payloads, absolute paths unless explicitly required for debugging, stack traces by default, usernames, hostnames, or environment variable values.

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
| `InputValidationError` | `1` | structured JSON `CliError` on `stderr` |
| `ConfigurationError` | `1` | structured JSON `CliError` on `stderr` |
| `SerializationError` for invalid input JSON | `1` | structured JSON `CliError` on `stderr` |
| CLI usage error | `2` | structured JSON `CliError` on `stderr` |
| output write failure | `3` | structured JSON `CliError` on `stderr` |
| unexpected system error | `4` | structured JSON `CliError` on `stderr` |

Feature diagnostics explain degraded extraction. They are not a substitute for fatal exceptions.

Fatal failures:

- invalid input schema;
- invalid config;
- invalid paging config;
- invalid `WordRef` generated by core;
- duplicate feature IDs after deterministic generation;
- output serialization failure;
- output write failure;
- internal exception outside feature-group boundary.

Recoverable failures:

- ambiguous POS;
- ambiguous clause boundary;
- ambiguous participle;
- missing optional morphology;
- unsupported feature pattern;
- unavailable optional external oracle;
- malformed optional `feats` value.

Recoverable failures produce `FeatureDiagnostic` and omit or lower confidence for the affected feature.


## 37. Formal Coq Specification

The authoritative formal specification lives in `coq/GrammarFeatureExtractorSpec.v`.

For `v5` it should model at least:

- `schema_version = grammar_feature_extractor.v5`;
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
| `schema_version` | `SCHEMA_VERSION = "grammar_feature_extractor.v5"` |
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
- output write failures map to exit code `3`;
- unexpected runtime/system errors map to exit code `4`;
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

The existing single-page CLI mode remains valid. Production `--output-dir` mode is normative for integration with `grammar_extractor` and `grammar_rule_detector`.

Command:

```text
grammar-feature-extractor   --input filtered_annotated_document.json   --output-dir grammar_features   --page-size 300   --debug
```

Output layout:

```text
grammar_features/
  grammar_features.manifest.json
  grammar_features.page_00001.json
  grammar_features.page_00002.json
  ...
```

Manifest schema is `schema/grammar_feature_manifest.v5.schema.json`.

Rules:

- page numbers are 1-based;
- page filenames use zero padding width at least 5;
- lexical filename sorting MUST equal page order;
- page ranges MUST be gap-free and non-overlapping;
- `page_size` default remains `300`;
- empty input document MUST produce exactly one valid empty page and manifest;
- `--output-dir` is mutually exclusive with single-page `--output`;
- debug mode MUST NOT alter page contents or manifest hashes.

### 44.1 Output-dir atomicity

- `--output-dir` MUST be created if missing;
- if `--output-dir` exists, it MUST be empty unless `--overwrite` is provided;
- symlink output targets MUST be rejected by default;
- page files MUST be written before manifest;
- every page file MUST be written to a temporary file in the same directory;
- every page file MUST be atomically renamed after successful write and hash verification;
- manifest MUST be written last using the same temp-file-and-rename policy;
- if any page write fails, manifest MUST NOT be written;
- on failure, temporary files SHOULD be removed;
- `sha256` is computed over canonical UTF-8 JSON bytes of the final page file.

## 45. Limits

| Limit | Default | Unit | Inclusive | Configurable | On exceed |
|---|---:|---|---|---|---|
| `max_input_bytes` | `104857600` | bytes | inclusive | yes | `InputValidationError` |
| `max_sentences` | `200000` | sentences | inclusive | yes | `InputValidationError` |
| `max_words_per_sentence` | `512` | words | inclusive | yes | `InputValidationError` |
| `max_total_words` | `5000000` | words | inclusive | yes | `InputValidationError` |
| `max_page_size` | `5000` | sentences | inclusive | yes | `ConfigurationError` |
| `max_output_page_bytes` | `104857600` | bytes | inclusive | yes | `SerializationError` |
| `max_output_pages` | `100000` | pages | inclusive | yes | `ConfigurationError` |
| `max_diagnostics_per_sentence` | `100` | diagnostics | inclusive | yes | diagnostic truncation + warning |

All limits MUST be checked deterministically before or during extraction.

Exactly equal to the limit succeeds. Greater than the limit fails or truncates according to the `On exceed` column.
### 45.1 Limit enforcement phase matrix

| Limit | Enforced by | Library core behavior | CLI/helper behavior | Error mapping on exceed |
|---|---|---|---|---|
| `max_input_bytes` | byte/file/JSON-loading adapters before UTF-8 decode | Not enforced by `extract()`, `extract_page()`, or `extract_pages()` when they receive an already validated `AnnotatedDocument` model | Enforced before JSON parse | `InputValidationError`; CLI `input_validation_error`, exit `1`, `validation_code = "input_too_large"` |
| `max_sentences` | semantic input validator | Enforced | Enforced after JSON model load | `InputValidationError`; CLI `input_validation_error`, exit `1`, `validation_code = "too_many_sentences"` |
| `max_words_per_sentence` | semantic input validator | Enforced | Enforced after JSON model load | `InputValidationError`; CLI `input_validation_error`, exit `1`, `validation_code = "too_many_words_per_sentence"` |
| `max_total_words` | semantic input validator | Enforced | Enforced after JSON model load | `InputValidationError`; CLI `input_validation_error`, exit `1`, `validation_code = "too_many_total_words"` |
| `max_page_size` | resolved config semantic validator | Enforced before extraction | Enforced after CLI flag resolution | `ConfigurationError`; CLI `configuration_error`, exit `1`, `validation_code = "page_size_exceeds_max_page_size"` |
| `max_output_page_bytes` | canonical serialization layer | Enforced after canonical bytes are produced and before returning/writing final page | Enforced before final write/rename | `SerializationError`; CLI `output_serialization_error`, exit `1`, `validation_code = "output_page_too_large"` |
| `max_output_pages` | pagination planner | Enforced by `extract_pages()` before returning | Enforced before any output-dir page write | `ConfigurationError`; CLI `configuration_error`, exit `1`, `validation_code = "max_output_pages_exceeded"` |
| `max_diagnostics_per_sentence` | diagnostics post-processor | Truncates as specified; fatal exceptions are never suppressed | Same as library | success unless another fatal error occurs |

Exactly equal to a configured limit succeeds. Greater than a configured limit fails or truncates according to this table.


## 46. Filesystem security


### 46.1 Overwrite and filesystem safety matrix

Single-file `--output`:

- parent directories are not created; missing parent directory is `output_write_error`, exit `3`;
- if the target exists and `--overwrite` is false, fail with `output_write_error`, exit `3`;
- if the target exists and `--overwrite` is true, replace it via same-directory temp file and atomic rename;
- if the target is a directory, fail with `output_write_error`, exit `3`;
- output symlinks are rejected without following the link and without mutating the target.

Directory `--output-dir`:

- if the directory does not exist, create it;
- parent directories for `--output-dir` are not created unless the immediate target parent already exists; missing parent is `output_write_error`, exit `3`;
- if the path exists and is not a directory, fail with `output_write_error`, exit `3`;
- if the directory exists and is non-empty and `--overwrite` is false, fail with `output_write_error`, exit `3`;
- if the directory exists and `--overwrite` is true, replace only files whose names match `grammar_features.page_*.json` or `grammar_features.manifest.json`;
- unrelated files MUST NOT be deleted; if unrelated files make safe output impossible, fail with `output_write_error`, exit `3`;
- manifest is written last; if any page write or hash verification fails, no completed manifest may remain.

Input path policy:

- `--input` must resolve to a regular file; stdin is allowed;
- missing input path maps to `input_validation_error`, exit `1`;
- input symlinks are allowed only if they resolve to a regular file inside the caller-provided path context; implementations that cannot make this check safely MUST reject them with `input_validation_error`, exit `1`;
- non-UTF-8 input bytes map to `input_json_serialization_error`, exit `1`;
- malformed JSON maps to `input_json_serialization_error`, exit `1`.

Hardlink/race policy:

- final writes use same-directory temporary files and atomic rename;
- implementations MUST open output paths with no-follow or equivalent symlink-race protection where the platform supports it;
- if platform safety cannot be guaranteed, fail closed with `output_write_error`, exit `3`.

CLI filesystem behavior:

- `--input` MUST be a regular file or `stdin`;
- `--output` MUST NOT be a directory;
- output symlink targets MUST be rejected by default;
- parent directories are not created for `--output` unless explicitly documented in a future version;
- `--output-dir` is created if missing;
- existing non-empty `--output-dir` is invalid unless `--overwrite` is provided;
- temporary files MUST be created in the same directory as final output;
- logs MUST NOT include full input payloads;
- network access is forbidden;
- `core` MUST NOT perform filesystem IO.

## 47. External and closed-list resources

Any closed list, lexicon, phonology adapter, whitelist, registry, or heuristic table used by extraction MUST be declared in stage metadata `assets` and projected into serialized `ExtractorRuntimeMetadata.resources`.

```typescript
interface RuntimeResource {
  name: string;
  kind: "closed_list" | "lexicon" | "phonology" | "heuristic_table" | "registry" | "schema";
  version: string;
  sha256?: string | null;
  required: boolean;
}
```

If a required resource is missing, extraction MUST raise `ConfigurationError`.

If an optional resource is missing, extraction MUST degrade gracefully and emit the corresponding diagnostic when diagnostics are enabled.

## 48. Registry-backed identifiers

Proof-relevant string identifiers MUST be closed enums or registry-backed identifiers.

Registry-backed fields:

| Field | Registry |
|---|---|
| `ConstructionFeature.signature` | `schema/construction_signature_registry.v5.json` |
| `PredicateFeature.form_signature` | `schema/predicate_form_signature_registry.v5.json` |
| `TAVMFeature.form_signature` | `schema/predicate_form_signature_registry.v5.json` |
| `FeatureDiagnostic.code` | `schema/diagnostic_registry.v5.json` |
| matcher feature paths | `schema/feature_path_registry.v5.json` |

Free surface text MUST be separated from proof identifiers. Examples:

- `NegationFeature.negator_kind` is enum; `surface` stores observed token text;
- `TimeMarkerFeature.marker_kind` is enum; `surface` stores observed marker text;
- `DiscourseMarkerFeature.marker_kind` is enum; `surface` stores observed marker text.

## 49. Canonical fixtures required before implementation freeze

Before final production code generation, the repository MUST include adjacent fixtures:

- one valid minimal input document;
- one valid full `GrammarFeaturePage` for `valid_minimal_present_simple.input.json`;
- one valid full `GrammarFeaturePage` for `valid_minimal_copular.input.json`;
- one valid full positive fixture for present-simple negative do-support;
- one valid full positive fixture for `a/an/the/zero` article behavior;
- one valid full positive fixture for passive `be + participle`;
- one compact `--no-evidence` page;
- one valid empty document page and manifest;
- one invalid input example for each fatal validation family;
- one invalid output example for missing provenance;
- one invalid diagnostic code example;
- one invalid construction signature example;
- one CLI error example for each exit code family.

All fixtures MUST validate or fail against committed schemas exactly as named.
