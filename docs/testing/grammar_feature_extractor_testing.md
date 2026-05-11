# Testing Guide for grammar_feature_extractor v5

**Document status:** updated testing guide generated from the uploaded v5 schemas, registries, and `grammar_feature_extractor_architecture_v5.md`.

**Module:** `grammar_feature_extractor`  
**Runtime/output schema version:** `grammar_feature_extractor.v5`  
**Input schema version:** `grammar_feature_extractor.annotated_document.input.v5`  
**Primary goal:** make test cases sufficiently self-contained for generating automated tests without re-reading the source documentation.

---

## 1. Scope and Non-Goals

### In scope

This guide covers:

- public API behavior for `GrammarFeatureExtractor.extract()` and `GrammarFeatureExtractor.extract_page()`;
- CLI behavior for single-page and output-dir modes;
- normalized `AnnotatedDocument` input validation;
- resolved config validation and config patch behavior;
- raw partial config schema validation for API/config-file style inputs;
- page output, full document output, standalone diagnostics, and manifest schema validation;
- diagnostic registry compliance;
- semantic validation registry compliance;
- construction signature registry compliance;
- predicate form signature registry compliance;
- feature path registry compliance;
- deterministic feature IDs and stable output ordering;
- canonical output serialization and SHA-256 manifest verification;
- filesystem security and output-dir atomicity;
- diagnostics truncation behavior;
- resource metadata and hash policy;
- regression tests for debug leakage, disabled feature groups, fatal diagnostics, and schema bundling drift.

### Out of scope

These tests do not validate:

- Stanza runtime quality;
- raw text tokenization or sentence splitting;
- external NLP model correctness;
- business/pedagogical ranking of grammar rules;
- downstream `grammar_rule_detector` behavior;
- downstream rule catalog generation.

---

## 2. Source Contracts and Required Artifacts

### 2.1 Required repository artifacts

Automation must fail during test collection if any required artifact is missing.

| Artifact | SHA-256 of hardened v5 contract |
|---|---|
| `docs/architecture/fixtures/grammar_feature_extractor/v5/cli_error_input_validation.json` | `1c98d3bfd18ca2d7c3f9f5afc766b63d4556de4d83bef85ed35f4443e3fbf5fa` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/cli_error_output_write.json` | `6dd796e1102f83f403f3699e5f42cf45f522b05b59ecd99a1e663969e309f7b8` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/cli_error_unexpected_system.json` | `3bf7b7d8a20f9d878af8d04a97cc2d7b79df74f8af529538bac9c3b15ec0cd7f` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/cli_error_usage.json` | `0d6f5fa2e01ac82f822eccfe68a105084a86520ca81d3fce75329c5fc74b72ec` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/default_resolved_config.json` | `c9865ffc904d540d20f51524e45a9ea1ff51dffdf0f5ac022eeb041b62f066ee` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/filtered_annotated_document.hashes.json` | `e38faaddcb5711aed5901b9390a892be589cf68fa760f15fd2ab7887b9a4f044` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/filtered_annotated_document.raw.json` | `d67b59a002ffa417532908d3d4ab23af4471cb88292cba3595780e0ae0f3385f` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/filtered_annotated_document.v5.json` | `4c8158d54197b78e599cf32db9a758aab343272eec417d9bddfd68077d7bab21` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/invalid_input_head_out_of_range.json` | `3042a86e9c19ecd278387d11f10cb687fdb7b3736b6ab6dac8460247a74344cf` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/invalid_output_unknown_construction_signature.json` | `d24c454524aca9fd0046ad1344c3ceb16d96a753163eab376ed03e7a3547dd08` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/invalid_output_unknown_diagnostic_code.json` | `503effd3fed53a409c1329f1a01147c1f26ed1db8a27d9b4300c2cb011167567` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/valid_empty_document.json` | `831734893436e02db0e0237a7e848c6591397a78ba666220c4b5c348db316571` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/valid_empty_document_manifest.json` | `a8d1a54525cc61a41719e392d6b2b5f1d6caad343a4ecda4b6c250ab8ecfc844` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/valid_empty_document_page.json` | `1fae1fdae56b918da8978263db625f81e7151a02e9a6736e1b914d2495ac57b9` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/valid_minimal_copular.json` | `49f0483f2c63ed076daf8091f1b63670a03ce00cd2c39c045c5cf5e4e471a0ba` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/valid_minimal_copular.page.golden.json` | `faf69b5dc6a09262284164dff7c2c8732c9650b7478032d1ea239953a2d2f62e` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/valid_minimal_input.json` | `71bcd96e6ee95ef641e6ce95ec274e6af200e41bf81ca1a03753be064a0a22de` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/valid_minimal_present_simple.input.json` | `dd03fa4a349b983cc99c9cc66e381a303c55b97a6c5ffde9f2f596074c261c42` |
| `docs/architecture/fixtures/grammar_feature_extractor/v5/valid_minimal_present_simple.page.golden.json` | `95df649a6550e1b964780123b3b6e66a721322b75e5df9a83d2580dd6b60c06f` |
| `docs/architecture/grammar_feature_extractor_architecture_v5.md` | `e0f17caa2a971fc64e5a1e78616a8a2efb57315e92c8ab84bd70eeb7f0d46366` |
| `docs/architecture/schema/annotated_document.input.v5.schema.json` | `f4b8d23b79c86027771ca3b3f18280184998679d15db2f5b64b225cc79cd3ed5` |
| `docs/architecture/schema/cli_error.v5.schema.json` | `8ebf2829c2739fa93a9eda7c6f5c5f9f21fc2c5c960aca58840f30cd974f7d7c` |
| `docs/architecture/schema/construction_signature_registry.v5.json` | `22885d9dff57f02e03d0f362823d2e949596b6d5a108975268df125c13d9b111` |
| `docs/architecture/schema/construction_signature_registry.v5.schema.json` | `e83780c755210263cf40ae765faad9e18a0975ed56e5df29bbfd9375085da360` |
| `docs/architecture/schema/diagnostic_registry.v5.json` | `d5d1f48811f42ae5b90633624e2f11ad1bbd3df9c2d4ddf5e177d7174e15c906` |
| `docs/architecture/schema/diagnostic_registry.v5.schema.json` | `963fe5d1f3be612c4ec20281ec57b4f0edf05863326db17cb26922a9dc2dee3f` |
| `docs/architecture/schema/feature_path_registry.v5.json` | `835b0aa845e835a05f2a0347fc08cb855dcbd391b1bc0534c3e3c109d29fbffc` |
| `docs/architecture/schema/feature_path_registry.v5.schema.json` | `1ddd136b11ce4930959e4df632625c2ca6e4373f370be83968b3249d42586f29` |
| `docs/architecture/schema/grammar_feature_common.v5.schema.json` | `93cb6c3a7665bbb87cbffc40ebd1c792685acb506340c78fe0ab8ac3d21658c5` |
| `docs/architecture/schema/grammar_feature_config.input.v5.schema.json` | `b3ea0abf9a80ceb980255efa6f6870df7feafed22681c0cc13cbf15c8ff55881` |
| `docs/architecture/schema/grammar_feature_config.v5.schema.json` | `497901c9e5cd51ca68d8d3fffba2a56fe9de0a113f20dd44af71cbb34115a785` |
| `docs/architecture/schema/grammar_feature_diagnostics.v5.schema.json` | `bf35a061e191cd27f169d9b63e10d3c2057a189fdbeb084488a354c5b28af9d2` |
| `docs/architecture/schema/grammar_feature_document.v5.schema.json` | `9d899f9325e4708193a2e95f94b75adf492cf8a87e96753cef12f69c21d7c93c` |
| `docs/architecture/schema/grammar_feature_manifest.v5.schema.json` | `1961530a76274e9ce0f9abf7ed35d9a5187ef5a8e6f6b668f7e88c39d5dc7434` |
| `docs/architecture/schema/grammar_feature_page.v5.schema.json` | `3e158f0bfb977ef95114e03510db9383c304fed91b71a6cfe3d28be2972e6cfe` |
| `docs/architecture/schema/predicate_form_signature_registry.v5.json` | `84bae9e82cacd911941c8ce8bbb4df95bfba7e311a352c69f22cdd1514e22fea` |
| `docs/architecture/schema/predicate_form_signature_registry.v5.schema.json` | `dd812f8cae0f0240b3447daa7c004dd3c6dc747936e2335c7b53d723d52377ea` |
| `docs/architecture/schema/semantic_validation_registry.v5.json` | `f90987f91035567abe92fdaca58e304391144cfdce0bdbfddf29eebd54eda7b2` |
| `docs/architecture/schema/semantic_validation_registry.v5.schema.json` | `8f24e08b4d42a058c5438b98af911e9ec188b57a5b3430ee601bf880c8eda2ea` |
| `fixtures/inputs/filtered_annotated_document.hashes.json` | `e38faaddcb5711aed5901b9390a892be589cf68fa760f15fd2ab7887b9a4f044` |
| `fixtures/inputs/filtered_annotated_document.raw.json` | `d67b59a002ffa417532908d3d4ab23af4471cb88292cba3595780e0ae0f3385f` |
| `fixtures/inputs/filtered_annotated_document.v5.json` | `4c8158d54197b78e599cf32db9a758aab343272eec417d9bddfd68077d7bab21` |
| `fixtures/inputs/valid_empty_document.json` | `831734893436e02db0e0237a7e848c6591397a78ba666220c4b5c348db316571` |
| `fixtures/inputs/valid_minimal_copular.json` | `49f0483f2c63ed076daf8091f1b63670a03ce00cd2c39c045c5cf5e4e471a0ba` |
| `fixtures/inputs/valid_minimal_present_simple.input.json` | `dd03fa4a349b983cc99c9cc66e381a303c55b97a6c5ffde9f2f596074c261c42` |
| `fixtures/outputs/valid_minimal_copular.page.golden.json` | `faf69b5dc6a09262284164dff7c2c8732c9650b7478032d1ea239953a2d2f62e` |
| `fixtures/outputs/valid_minimal_present_simple.page.golden.json` | `95df649a6550e1b964780123b3b6e66a721322b75e5df9a83d2580dd6b60c06f` |

**Missing artifact behavior:**

- pytest collection error: `MissingContractArtifact`;
- error message includes the missing relative path;
- tests that require schemas/registries must not silently skip unless marked platform-dependent.

### 2.2 Confirmed contract points from uploaded files

| Contract point | Status | Source artifact |
|---|---|---|
| Accepted input envelope requires `schema_version`, `sentences`, and `entities`; unknown fields are rejected. | Confirmed | `annotated_document.input.v5.schema.json` |
| `feats` in input is optional, but if present it must be a non-empty string; `null` is not accepted. | Confirmed | `annotated_document.input.v5.schema.json` |
| CLI errors use `schema_version`, `kind = cli_error`, `error_code`, `message`, optional scalar `details`; unknown fields are rejected. | Confirmed | `cli_error.v5.schema.json` |
| Resolved config requires all defaulted fields and `limits`; `page_number >= 1`, `page_size >= 1`; default `page_size = 300`. | Confirmed | `grammar_feature_config.v5.schema.json` |
| Raw partial config is separate from resolved config; v5 CLI must not expose `--config`. | Confirmed | `grammar_feature_config.input.v5.schema.json`, architecture |
| `FeatureId` pattern is `^s[0-9]+\.[a-z_]+\.[1-9][0-9]*$`. | Confirmed | `grammar_feature_common.v5.schema.json` |
| Feature group keys remain present in `GrammarFeatureSet`: `evidence`, `morphology`, `syntax`, `lexical`, `constructions`, `contrastive_support`, `absences`, `diagnostics`. | Confirmed | `grammar_feature_common.v5.schema.json`, `grammar_feature_page.v5.schema.json` |
| `AgreementFeature.subject_person` and `predicate_person` are JSON integers `1 | 2 | 3`; `MorphFeature.features.Person` remains string `"1" | "2" | "3"`. | Confirmed | `grammar_feature_common.v5.schema.json`, architecture |
| `FeatureDiagnostic.code` is a closed enum matching the diagnostic registry. | Confirmed | `grammar_feature_common.v5.schema.json`, `diagnostic_registry.v5.json` |
| Manifest page files use `grammar_features.page_00001.json` style names. | Confirmed | `grammar_feature_manifest.v5.schema.json` |
| Semantic validation codes map to exception, CLI error code, and exit code. | Confirmed | `semantic_validation_registry.v5.json` |
| Construction slots are registry-typed and signature-specific. | Confirmed | `construction_signature_registry.v5.json`, architecture |
| Feature paths are registry-backed and include value type/operator constraints. | Confirmed | `feature_path_registry.v5.json` |

### 2.3 Remaining assumptions / gaps

| Area | Gap | Risk | Required clarification |
|---|---|---|---|
| API import path | Resolved. | Tests MUST import public API classes and exceptions from `grammar_feature_extractor`. | `from grammar_feature_extractor import GrammarFeatureExtractor, ExtractorConfig, ExtractorLimits, PagingConfig, ConfigurationError, InputValidationError, SerializationError, FeatureExtractionError`. |
| Exact implementation exception classes | Resolved. | Public exception classes are exported from `grammar_feature_extractor`. | Do not import exceptions from private submodules. |
| Golden outputs | Resolved for mandatory minimal positives. | Full canonical comparison is required for committed golden fixtures. | Use `valid_minimal_copular.page.golden.json` and `valid_minimal_present_simple.page.golden.json`. |
| Large fixture normalization | Resolved. | F003 and F004 are committed synthetic fixtures and are generated by an executable script in this guide. | Test collection MUST fail with `MissingContractArtifact` if either file is absent. |

---

### 2.2 Fixture materialization release gate

Every fixture referenced by this testing guide MUST exist as a committed file under `fixtures/inputs/`, `fixtures/outputs/`, or `fixtures/grammar_feature_extractor/v5/`. Inline JSON examples are explanatory only and MUST NOT be the only source of a required fixture. CI MUST validate `fixtures/fixture_manifest.v5.json` before running test cases and MUST fail fast with `MissingContractArtifact` if any listed fixture is missing, hash-mismatched, or unexpectedly unparsable.

## 3. Test Environment

### 3.1 Runtime

- Python: `3.11+`.
- Test runner: `pytest`.
- JSON Schema validator: must support draft 2020-12.
- All filesystem tests must use isolated temporary directories.
- Network access must not be required.

### 3.2 Canonical CLI command

Use the architecture-confirmed console command:

```bash
grammar-feature-extractor
```

Single-page example:

```bash
grammar-feature-extractor --input annotated_document.json --output features.page.json --page 1 --page-size 300 --debug
```

Output-dir example:

```bash
grammar-feature-extractor --input filtered_annotated_document.json --output-dir grammar_features --page-size 300 --debug
```

Supported v5 arguments:

- `--input <path>`; default: stdin;
- `--output <path>`; default: stdout;
- `--output-dir <path>`;
- `--page <positive-int>`; default: `1`;
- `--page-size <positive-int>`; default: `300`;
- `--no-evidence`;
- `--no-heuristics`;
- `--debug`, `-d`;
- `--overwrite`.

Unsupported in v5:

- `--config`.

### 3.3 CLI exit code contract

| Exit code | Meaning |
|---:|---|
| `0` | success |
| `1` | input data, schema, semantic validation, serialization, or configuration error after valid CLI parsing |
| `2` | CLI usage error |
| `3` | output write failure |
| `4` | unexpected runtime/system error |

### 3.4 CLI stream contract

- Success without `--output` and without `--output-dir`: stdout contains exactly one serialized `GrammarFeaturePage`.
- Success with `--output` or `--output-dir`: stdout is empty.
- Failure: stdout is empty.
- Failure: stderr contains exactly one structured `CliError` JSON object followed by one newline. No logs, stack traces, debug messages, or human-readable prefixes may appear on stderr. Logs are allowed only through a separate sink such as `--log-file PATH` or injected library logging.

---

## 4. Shared Configs and Config Patch Rule

### Fixture CFG-001: default resolved config

`fixtures/grammar_feature_extractor/v5/default_resolved_config.json`

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

This config must validate against `schema/grammar_feature_config.v5.schema.json`.

### Config patch rule

Some test cases specify config patches. A patch is not standalone.

Automation must:

1. Load CFG-001.
2. Deep-merge the patch into CFG-001.
3. Validate the merged config against `grammar_feature_config.v5.schema.json`.
4. Use the merged config for API tests.
5. Translate equivalent fields into CLI flags for CLI tests when applicable.

Example patch:

```json
{
  "page_number": 2,
  "page_size": 1
}
```


### 4.1 Resolved config to public API mapping

API tests MUST NOT pass CFG-001 as a positional argument to `extract_page`. CFG-001 is a resolved JSON config fixture and MUST be converted into the split Python models before calling the public API.

Canonical conversion:

```python
def split_resolved_config(cfg):
    limits = ExtractorLimits(**cfg["limits"])
    extractor_config = ExtractorConfig(
        include_diagnostics=cfg["include_diagnostics"],
        include_evidence=cfg["include_evidence"],
        include_construction_signatures=cfg["include_construction_signatures"],
        include_contrastive_support=cfg["include_contrastive_support"],
        enable_heuristics=cfg["enable_heuristics"],
        debug=cfg["debug"],
        limits=limits,
    )
    paging_config = PagingConfig(
        page_number=cfg["page_number"],
        page_size=cfg["page_size"],
    )
    return extractor_config, paging_config
```

Canonical `extract_page` call:

```python
extractor_config, paging_config = split_resolved_config(CFG_001)
page = extractor.extract_page(
    document,
    paging=paging_config,
    config=extractor_config,
)
```

---

## 5. Output Comparison Rules

Unless a test states otherwise:

1. All successful outputs must validate against the corresponding JSON Schema.
2. All successful outputs must pass semantic output validation when the implementation exposes such validator.
3. Exact full linguistic feature arrays MUST be asserted for committed golden outputs. For non-golden fixtures, assert schema, semantic validity, deterministic ordering, and explicitly listed feature/diagnostic invariants only.
4. Invariant tests may assert:
   - `schema_version`;
   - `kind`;
   - page metadata;
   - `source_sentence_count` for full document output;
   - sentence order and `sentence_index` values;
   - presence of required feature-group keys;
   - WordRef validity;
   - diagnostic presence/absence by code;
   - manifest file hashes and page ranges.
5. Canonical byte comparison is required only for deterministic serialization tests.
6. Timestamps, random IDs, absolute local paths, and environment-dependent values are forbidden unless explicitly schema-defined.
7. No fields are ignored by default.

---

## 6. Error and Diagnostic Assertion Rules

### 6.1 API failures

For API failures assert:

- exception class or semantic registry exception name;
- stable validation or diagnostic code when exposed;
- no partial successful output object is returned;
- no output file is created by core API.

### 6.2 CLI failures

For CLI failures assert:

- exit code;
- stdout is empty;
- stderr is exactly one JSON object followed by one newline;
- stderr validates against `schema/cli_error.v5.schema.json`;
- `cli_error.schema_version == "grammar_feature_extractor.v5"`;
- `cli_error.kind == "cli_error"`;
- `cli_error.error_code` is one of the closed enum values.

### 6.3 Diagnostics

For every emitted `FeatureDiagnostic` assert:

- `code` exists in `diagnostic_registry.v5.json`;
- `severity` equals registry severity;
- `message` is non-empty;
- `refs` is present and contains only valid sentence-local WordRefs;
- if registry `refs_required == true`, `refs` is non-empty;
- if registry `feature_path_required == true`, `feature_path` is present and non-empty;
- no undocumented diagnostic code is emitted.

---

## 7. Test Fixtures

### Fixture F001: valid minimal copular sentence

**Purpose:** happy path, evidence refs, morphology, construction candidate `subject_be_present_complement`.

`fixtures/inputs/valid_minimal_copular.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": [
    {
      "text": "She is happy.",
      "tokens": [
        {
          "text": "She",
          "words": [
            {
              "text": "She",
              "lemma": "she",
              "upos": "PRON",
              "xpos": "PRP",
              "feats": "Case=Nom|Gender=Fem|Number=Sing|Person=3|PronType=Prs",
              "head": 3,
              "deprel": "nsubj",
              "start_char": 0,
              "end_char": 3
            }
          ]
        },
        {
          "text": "is",
          "words": [
            {
              "text": "is",
              "lemma": "be",
              "upos": "AUX",
              "xpos": "VBZ",
              "feats": "Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin",
              "head": 3,
              "deprel": "cop",
              "start_char": 4,
              "end_char": 6
            }
          ]
        },
        {
          "text": "happy",
          "words": [
            {
              "text": "happy",
              "lemma": "happy",
              "upos": "ADJ",
              "xpos": "JJ",
              "feats": "Degree=Pos",
              "head": 0,
              "deprel": "root",
              "start_char": 7,
              "end_char": 12
            }
          ]
        },
        {
          "text": ".",
          "words": [
            {
              "text": ".",
              "lemma": ".",
              "upos": "PUNCT",
              "xpos": ".",
              "head": 3,
              "deprel": "punct",
              "start_char": 12,
              "end_char": 13
            }
          ]
        }
      ],
      "words": [
        {
          "text": "She",
          "lemma": "she",
          "upos": "PRON",
          "xpos": "PRP",
          "feats": "Case=Nom|Gender=Fem|Number=Sing|Person=3|PronType=Prs",
          "head": 3,
          "deprel": "nsubj",
          "start_char": 0,
          "end_char": 3
        },
        {
          "text": "is",
          "lemma": "be",
          "upos": "AUX",
          "xpos": "VBZ",
          "feats": "Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin",
          "head": 3,
          "deprel": "cop",
          "start_char": 4,
          "end_char": 6
        },
        {
          "text": "happy",
          "lemma": "happy",
          "upos": "ADJ",
          "xpos": "JJ",
          "feats": "Degree=Pos",
          "head": 0,
          "deprel": "root",
          "start_char": 7,
          "end_char": 12
        },
        {
          "text": ".",
          "lemma": ".",
          "upos": "PUNCT",
          "xpos": ".",
          "head": 3,
          "deprel": "punct",
          "start_char": 12,
          "end_char": 13
        }
      ]
    }
  ]
}
```

Expected reusable assertions:

- validates against `annotated_document.input.v5.schema.json`;
- semantic input validation passes;
- output page validates against `grammar_feature_page.v5.schema.json`;
- `page.total_sentences == 1`;
- required feature-group keys are present;
- all emitted FeatureIds match `^s[0-9]+\.[a-z_]+\.[1-9][0-9]*$`;
- `TokenEvidence.lower` for `She` equals `she`.

Committed golden output: `fixtures/outputs/valid_minimal_copular.page.golden.json`. TC-001 MUST compare the full canonical payload against this golden file.

Additional committed golden output: `fixtures/outputs/valid_minimal_present_simple.page.golden.json` for `docs/architecture/fixtures/grammar_feature_extractor/v5/valid_minimal_input.json`.

### Fixture F002: valid empty document

`fixtures/inputs/valid_empty_document.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": []
}
```

Expected reusable assertions:

- schema validation passes;
- output page has `features: []`;
- output-dir mode creates exactly one page and manifest;
- empty manifest page range is `0..0`.

### Fixture F003: committed raw large synthetic fixture without schema version

`fixtures/inputs/filtered_annotated_document.raw.json`

This fixture is intentionally schema-invalid because it lacks `schema_version`. It replaces any dependency on conversation-uploaded or external Alice files. The raw fixture is generated and committed as deterministic JSON with top-level keys `entities` and `sentences`.

Required metadata for the committed fixture is recorded in `fixtures/inputs/filtered_annotated_document.hashes.json`. Test collection MUST fail with `MissingContractArtifact` if this file or F004 is absent.

Expected reusable assertions:

- strict v5 input schema validation fails;
- direct CLI input fails with `input_validation_error`;
- this fixture must not be silently normalized by strict CLI tests.

### Fixture F004: committed normalized large synthetic fixture

`fixtures/inputs/filtered_annotated_document.v5.json`

Build rule:

```python
import json
from pathlib import Path

raw_path = Path("fixtures/inputs/filtered_annotated_document.raw.json")
out_path = Path("fixtures/inputs/filtered_annotated_document.v5.json")
raw = json.loads(raw_path.read_text(encoding="utf-8"))
normalized = {
    "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
    "entities": raw["entities"],
    "sentences": raw["sentences"],
}
out_path.write_text(
    json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
```

Expected metadata:

- normalized fixture validates against `annotated_document.input.v5.schema.json`;
- raw fixture SHA-256, normalized fixture SHA-256, sentence count, entity count, and total word count MUST match `fixtures/inputs/filtered_annotated_document.hashes.json`;
- generation script output bytes MUST match the committed normalized fixture exactly.

### Fixture F005: invalid head out of range

`fixtures/inputs/invalid_head_out_of_range.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": [
    {
      "text": "Run.",
      "tokens": [
        {
          "text": "Run",
          "words": [
            {
              "text": "Run",
              "lemma": "run",
              "upos": "VERB",
              "xpos": "VB",
              "feats": "Mood=Imp|VerbForm=Fin",
              "head": 99,
              "deprel": "root",
              "start_char": 0,
              "end_char": 3
            }
          ]
        },
        {
          "text": ".",
          "words": [
            {
              "text": ".",
              "lemma": ".",
              "upos": "PUNCT",
              "xpos": ".",
              "head": 1,
              "deprel": "punct",
              "start_char": 3,
              "end_char": 4
            }
          ]
        }
      ],
      "words": [
        {
          "text": "Run",
          "lemma": "run",
          "upos": "VERB",
          "xpos": "VB",
          "feats": "Mood=Imp|VerbForm=Fin",
          "head": 99,
          "deprel": "root",
          "start_char": 0,
          "end_char": 3
        },
        {
          "text": ".",
          "lemma": ".",
          "upos": "PUNCT",
          "xpos": ".",
          "head": 1,
          "deprel": "punct",
          "start_char": 3,
          "end_char": 4
        }
      ]
    }
  ]
}
```

Expected semantic validation code: `head_out_of_range`.

### Fixture F006: invalid dependency cycle with root present

`fixtures/inputs/invalid_dependency_cycle.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": [
    {
      "text": "Root A B.",
      "tokens": [
        {
          "text": "Root",
          "words": [
            {
              "text": "Root",
              "lemma": "root",
              "upos": "NOUN",
              "xpos": "NN",
              "feats": "Number=Sing",
              "head": 0,
              "deprel": "root",
              "start_char": 0,
              "end_char": 4
            }
          ]
        },
        {
          "text": "A",
          "words": [
            {
              "text": "A",
              "lemma": "a",
              "upos": "NOUN",
              "xpos": "NN",
              "feats": "Number=Sing",
              "head": 3,
              "deprel": "dep",
              "start_char": 5,
              "end_char": 6
            }
          ]
        },
        {
          "text": "B",
          "words": [
            {
              "text": "B",
              "lemma": "b",
              "upos": "NOUN",
              "xpos": "NN",
              "feats": "Number=Sing",
              "head": 2,
              "deprel": "dep",
              "start_char": 7,
              "end_char": 8
            }
          ]
        },
        {
          "text": ".",
          "words": [
            {
              "text": ".",
              "lemma": ".",
              "upos": "PUNCT",
              "xpos": ".",
              "head": 1,
              "deprel": "punct",
              "start_char": 8,
              "end_char": 9
            }
          ]
        }
      ],
      "words": [
        {
          "text": "Root",
          "lemma": "root",
          "upos": "NOUN",
          "xpos": "NN",
          "feats": "Number=Sing",
          "head": 0,
          "deprel": "root",
          "start_char": 0,
          "end_char": 4
        },
        {
          "text": "A",
          "lemma": "a",
          "upos": "NOUN",
          "xpos": "NN",
          "feats": "Number=Sing",
          "head": 3,
          "deprel": "dep",
          "start_char": 5,
          "end_char": 6
        },
        {
          "text": "B",
          "lemma": "b",
          "upos": "NOUN",
          "xpos": "NN",
          "feats": "Number=Sing",
          "head": 2,
          "deprel": "dep",
          "start_char": 7,
          "end_char": 8
        },
        {
          "text": ".",
          "lemma": ".",
          "upos": "PUNCT",
          "xpos": ".",
          "head": 1,
          "deprel": "punct",
          "start_char": 8,
          "end_char": 9
        }
      ]
    }
  ]
}
```

Expected semantic validation code: `dependency_cycle`.

### Fixture F007: invalid token/words mismatch

`fixtures/inputs/invalid_token_words_mismatch.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": [
    {
      "text": "Run!",
      "tokens": [
        {
          "text": "Run",
          "words": [
            {
              "text": "Go",
              "lemma": "go",
              "upos": "VERB",
              "xpos": "VB",
              "feats": "Mood=Imp|VerbForm=Fin",
              "head": 0,
              "deprel": "root",
              "start_char": 0,
              "end_char": 3
            }
          ]
        }
      ],
      "words": [
        {
          "text": "Run",
          "lemma": "run",
          "upos": "VERB",
          "xpos": "VB",
          "feats": "Mood=Imp|VerbForm=Fin",
          "head": 0,
          "deprel": "root",
          "start_char": 0,
          "end_char": 3
        }
      ]
    }
  ]
}
```

Expected semantic validation code: `token_words_mismatch`.

### Fixture F008: invalid unknown top-level input field

`fixtures/inputs/invalid_unknown_top_level_field.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": [],
  "unexpected": true
}
```

Expected schema/semantic validation code: `unknown_input_field` when normalized from schema additional-property failure.

### Fixture F009: malformed UD feats string

`fixtures/inputs/malformed_morphology_feats.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": [
    {
      "text": "Alice runs.",
      "tokens": [
        {
          "text": "Alice",
          "words": [
            {
              "text": "Alice",
              "lemma": "Alice",
              "upos": "PROPN",
              "xpos": "NNP",
              "feats": "Number=Sing",
              "head": 2,
              "deprel": "nsubj",
              "start_char": 0,
              "end_char": 5
            }
          ]
        },
        {
          "text": "runs",
          "words": [
            {
              "text": "runs",
              "lemma": "run",
              "upos": "VERB",
              "xpos": "VBZ",
              "feats": "Mood=Ind|Person",
              "head": 0,
              "deprel": "root",
              "start_char": 6,
              "end_char": 10
            }
          ]
        },
        {
          "text": ".",
          "words": [
            {
              "text": ".",
              "lemma": ".",
              "upos": "PUNCT",
              "xpos": ".",
              "head": 2,
              "deprel": "punct",
              "start_char": 10,
              "end_char": 11
            }
          ]
        }
      ],
      "words": [
        {
          "text": "Alice",
          "lemma": "Alice",
          "upos": "PROPN",
          "xpos": "NNP",
          "feats": "Number=Sing",
          "head": 2,
          "deprel": "nsubj",
          "start_char": 0,
          "end_char": 5
        },
        {
          "text": "runs",
          "lemma": "run",
          "upos": "VERB",
          "xpos": "VBZ",
          "feats": "Mood=Ind|Person",
          "head": 0,
          "deprel": "root",
          "start_char": 6,
          "end_char": 10
        },
        {
          "text": ".",
          "lemma": ".",
          "upos": "PUNCT",
          "xpos": ".",
          "head": 2,
          "deprel": "punct",
          "start_char": 10,
          "end_char": 11
        }
      ]
    }
  ]
}
```

Expected diagnostic if extraction degrades non-fatally: `malformed_morphology_feats`.

### Fixture F010: valid two-sentence document for paging

`fixtures/inputs/valid_two_sentences.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": [
    {
      "text": "Run!",
      "tokens": [
        {
          "text": "Run",
          "words": [
            {
              "text": "Run",
              "lemma": "run",
              "upos": "VERB",
              "xpos": "VB",
              "feats": "Mood=Imp|VerbForm=Fin",
              "head": 0,
              "deprel": "root",
              "start_char": 0,
              "end_char": 3
            }
          ]
        },
        {
          "text": "!",
          "words": [
            {
              "text": "!",
              "lemma": "!",
              "upos": "PUNCT",
              "xpos": ".",
              "head": 1,
              "deprel": "punct",
              "start_char": 3,
              "end_char": 4
            }
          ]
        }
      ],
      "words": [
        {
          "text": "Run",
          "lemma": "run",
          "upos": "VERB",
          "xpos": "VB",
          "feats": "Mood=Imp|VerbForm=Fin",
          "head": 0,
          "deprel": "root",
          "start_char": 0,
          "end_char": 3
        },
        {
          "text": "!",
          "lemma": "!",
          "upos": "PUNCT",
          "xpos": ".",
          "head": 1,
          "deprel": "punct",
          "start_char": 3,
          "end_char": 4
        }
      ]
    },
    {
      "text": "Stop!",
      "tokens": [
        {
          "text": "Stop",
          "words": [
            {
              "text": "Stop",
              "lemma": "stop",
              "upos": "VERB",
              "xpos": "VB",
              "feats": "Mood=Imp|VerbForm=Fin",
              "head": 0,
              "deprel": "root",
              "start_char": 5,
              "end_char": 9
            }
          ]
        },
        {
          "text": "!",
          "words": [
            {
              "text": "!",
              "lemma": "!",
              "upos": "PUNCT",
              "xpos": ".",
              "head": 1,
              "deprel": "punct",
              "start_char": 9,
              "end_char": 10
            }
          ]
        }
      ],
      "words": [
        {
          "text": "Stop",
          "lemma": "stop",
          "upos": "VERB",
          "xpos": "VB",
          "feats": "Mood=Imp|VerbForm=Fin",
          "head": 0,
          "deprel": "root",
          "start_char": 5,
          "end_char": 9
        },
        {
          "text": "!",
          "lemma": "!",
          "upos": "PUNCT",
          "xpos": ".",
          "head": 1,
          "deprel": "punct",
          "start_char": 9,
          "end_char": 10
        }
      ]
    }
  ]
}
```

### Fixture F011: Unicode casefold fixture

`fixtures/inputs/valid_unicode_casefold.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": [
    {
      "text": "Straße.",
      "tokens": [
        {
          "text": "Straße",
          "words": [
            {
              "text": "Straße",
              "lemma": "Straße",
              "upos": "NOUN",
              "xpos": "NN",
              "feats": "Number=Sing",
              "head": 0,
              "deprel": "root",
              "start_char": 0,
              "end_char": 6
            }
          ]
        },
        {
          "text": ".",
          "words": [
            {
              "text": ".",
              "lemma": ".",
              "upos": "PUNCT",
              "xpos": ".",
              "head": 1,
              "deprel": "punct",
              "start_char": 6,
              "end_char": 7
            }
          ]
        }
      ],
      "words": [
        {
          "text": "Straße",
          "lemma": "Straße",
          "upos": "NOUN",
          "xpos": "NN",
          "feats": "Number=Sing",
          "head": 0,
          "deprel": "root",
          "start_char": 0,
          "end_char": 6
        },
        {
          "text": ".",
          "lemma": ".",
          "upos": "PUNCT",
          "xpos": ".",
          "head": 1,
          "deprel": "punct",
          "start_char": 6,
          "end_char": 7
        }
      ]
    }
  ]
}
```

Expected output invariant: `TokenEvidence.lower == "strasse"` for surface `Straße`.

### Fixture F012: invalid entity span

`fixtures/inputs/invalid_entity_span.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [
    {
      "text": "Alice",
      "type": "PERSON",
      "start_char": 5,
      "end_char": 0
    }
  ],
  "sentences": [
    {
      "text": "She is happy.",
      "tokens": [
        {
          "text": "She",
          "words": [
            {
              "text": "She",
              "lemma": "she",
              "upos": "PRON",
              "xpos": "PRP",
              "feats": "Case=Nom|Gender=Fem|Number=Sing|Person=3|PronType=Prs",
              "head": 3,
              "deprel": "nsubj",
              "start_char": 0,
              "end_char": 3
            }
          ]
        },
        {
          "text": "is",
          "words": [
            {
              "text": "is",
              "lemma": "be",
              "upos": "AUX",
              "xpos": "VBZ",
              "feats": "Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin",
              "head": 3,
              "deprel": "cop",
              "start_char": 4,
              "end_char": 6
            }
          ]
        },
        {
          "text": "happy",
          "words": [
            {
              "text": "happy",
              "lemma": "happy",
              "upos": "ADJ",
              "xpos": "JJ",
              "feats": "Degree=Pos",
              "head": 0,
              "deprel": "root",
              "start_char": 7,
              "end_char": 12
            }
          ]
        },
        {
          "text": ".",
          "words": [
            {
              "text": ".",
              "lemma": ".",
              "upos": "PUNCT",
              "xpos": ".",
              "head": 3,
              "deprel": "punct",
              "start_char": 12,
              "end_char": 13
            }
          ]
        }
      ],
      "words": [
        {
          "text": "She",
          "lemma": "she",
          "upos": "PRON",
          "xpos": "PRP",
          "feats": "Case=Nom|Gender=Fem|Number=Sing|Person=3|PronType=Prs",
          "head": 3,
          "deprel": "nsubj",
          "start_char": 0,
          "end_char": 3
        },
        {
          "text": "is",
          "lemma": "be",
          "upos": "AUX",
          "xpos": "VBZ",
          "feats": "Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin",
          "head": 3,
          "deprel": "cop",
          "start_char": 4,
          "end_char": 6
        },
        {
          "text": "happy",
          "lemma": "happy",
          "upos": "ADJ",
          "xpos": "JJ",
          "feats": "Degree=Pos",
          "head": 0,
          "deprel": "root",
          "start_char": 7,
          "end_char": 12
        },
        {
          "text": ".",
          "lemma": ".",
          "upos": "PUNCT",
          "xpos": ".",
          "head": 3,
          "deprel": "punct",
          "start_char": 12,
          "end_char": 13
        }
      ]
    }
  ]
}
```

Expected semantic validation code: `invalid_entity_span`.

### Fixture F013: invalid missing dependency root

`fixtures/inputs/invalid_missing_dependency_root.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": [
    {
      "text": "A B.",
      "tokens": [
        {
          "text": "A",
          "words": [
            {
              "text": "A",
              "lemma": "a",
              "upos": "NOUN",
              "xpos": "NN",
              "feats": "Number=Sing",
              "head": 2,
              "deprel": "dep",
              "start_char": 0,
              "end_char": 1
            }
          ]
        },
        {
          "text": "B",
          "words": [
            {
              "text": "B",
              "lemma": "b",
              "upos": "NOUN",
              "xpos": "NN",
              "feats": "Number=Sing",
              "head": 1,
              "deprel": "dep",
              "start_char": 2,
              "end_char": 3
            }
          ]
        }
      ],
      "words": [
        {
          "text": "A",
          "lemma": "a",
          "upos": "NOUN",
          "xpos": "NN",
          "feats": "Number=Sing",
          "head": 2,
          "deprel": "dep",
          "start_char": 0,
          "end_char": 1
        },
        {
          "text": "B",
          "lemma": "b",
          "upos": "NOUN",
          "xpos": "NN",
          "feats": "Number=Sing",
          "head": 1,
          "deprel": "dep",
          "start_char": 2,
          "end_char": 3
        }
      ]
    }
  ]
}
```

Expected semantic validation code: `missing_dependency_root`.

### Fixture F014: invalid word span

`fixtures/inputs/invalid_word_span.json`

```json
{
  "schema_version": "grammar_feature_extractor.annotated_document.input.v5",
  "entities": [],
  "sentences": [
    {
      "text": "Run.",
      "tokens": [
        {
          "text": "Run",
          "words": [
            {
              "text": "Run",
              "lemma": "run",
              "upos": "VERB",
              "xpos": "VB",
              "feats": "Mood=Imp|VerbForm=Fin",
              "head": 0,
              "deprel": "root",
              "start_char": 3,
              "end_char": 0
            }
          ]
        }
      ],
      "words": [
        {
          "text": "Run",
          "lemma": "run",
          "upos": "VERB",
          "xpos": "VB",
          "feats": "Mood=Imp|VerbForm=Fin",
          "head": 0,
          "deprel": "root",
          "start_char": 3,
          "end_char": 0
        }
      ]
    }
  ]
}
```

Expected semantic validation code: `invalid_word_span`.

---

## 8. Test Case Matrix

| ID | Category | Purpose | Fixture | Expected result | Priority |
|---|---|---|---|---|---|
| TC-001 | Valid API page | Minimal page extraction | F001 + CFG-001 | success page schema valid | P0 |
| TC-002 | Empty input | Empty page and manifest | F002 + CFG-001 | success empty page/manifest | P0 |
| TC-003 | Strict input schema | Reject raw uploaded fixture | F003 | `input_validation_error` | P0 |
| TC-004 | Large input | Process normalized Alice fixture | F004 | success, paginated, deterministic | P1 |
| TC-005 | Semantic input | Head out of range | F005 | `head_out_of_range` | P0 |
| TC-006 | Semantic input | Dependency cycle | F006 | `dependency_cycle` | P0 |
| TC-007 | Semantic input | Token/words mismatch | F007 | `token_words_mismatch` | P0 |
| TC-008 | Schema/input field | Unknown top-level field | F008 | `unknown_input_field` or schema additional-property failure | P0 |
| TC-009 | Config gating | `--no-evidence` keeps group shape | F001 + patch | evidence empty, matcher incomplete | P0 |
| TC-010 | CLI usage | `--config` unsupported | F001 | exit `2`, `cli_usage_error` | P0 |
| TC-011 | Paging | page 2/page size 1 | F010 + patch | only second sentence | P0 |
| TC-012 | Paging boundary | page beyond end | F001 + patch | valid empty page | P1 |
| TC-013 | Diagnostics | malformed feats warning | F009 | diagnostic `malformed_morphology_feats` | P1 |
| TC-014 | Fatal serialization | output page too large public trigger | F001 + patch | `output_serialization_error`, exit `1` | P0 |
| TC-015 | Manifest | output-dir pages and manifest | F004 | file names, ranges, hashes valid | P0 |
| TC-016 | Filesystem security | reject output symlink | F001 | exit `3`, no target mutation | P0 |
| TC-017 | Canonical serialization | stable bytes | F001 | UTF-8 final newline, deterministic bytes | P0 |
| TC-018 | Determinism | stable IDs/order | F001/F004 | repeated bytes equal | P0 |
| TC-019 | Person typing | integer grammar person vs string UD morphology | F001 | schema-valid typed fields | P0 |
| TC-020 | Schema bundling | common `$defs` drift | schemas | byte-equivalent defs | P1 |
| TC-021 | Resource hash | invalid file-backed sha256 | synthetic metadata | validation failure | P1 |
| TC-022 | CLI stderr | invalid JSON syntax | invalid file | one CliError on stderr | P0 |
| TC-023 | Output schemas | page/document/manifest validation | F001/F002/F004 | schemas pass | P0 |
| TC-024 | Diagnostic registry | emitted diagnostics registry-compliant | F009 | code/severity/path/refs valid | P0 |
| TC-025 | Debug leakage | `--debug` does not alter payload | F001 | schema valid, no debug-only fields | P1 |
| TC-026 | Full document API | `extract()` returns full document | F001 | document schema valid | P0 |
| TC-027 | CLI stdin/stdout | success without paths | F001 | stdout page, stderr empty | P0 |
| TC-028 | Output-dir overwrite | non-empty dir behavior | F001 | fail without overwrite, succeed with overwrite | P1 |
| TC-029 | Unicode normalization | casefold, not locale lower | F011 | `Straße` -> `strasse` | P1 |
| TC-030 | Limit validation | page size exceeds max | F001 + patch | `page_size_exceeds_max_page_size` | P0 |

---

## 9. Detailed Test Cases

### TC-001: Minimal valid page extraction

**Category:** Valid / API / Contract  
**Priority:** P0  
**Contract status:** Confirmed by input, page, common, config schemas.

**Purpose:** Verify minimal valid extraction produces a valid `GrammarFeaturePage`.

**Preconditions:** F001 and CFG-001 exist.

**Input data:** F001.

**Config:** CFG-001.

**Execution steps:**

1. Validate F001 against `annotated_document.input.v5.schema.json`.
2. Convert CFG-001 into `ExtractorConfig` and `PagingConfig` with the section `4.1` mapping.
3. Run:

```python
page = extractor.extract_page(
    document,
    paging=paging_config,
    config=extractor_config,
)
```

4. Validate output against `grammar_feature_page.v5.schema.json`.
5. Run semantic output validation if available.
6. Compare canonical JSON bytes to `fixtures/outputs/valid_minimal_copular.page.golden.json`.

**Expected result:**

- success;
- `schema_version == "grammar_feature_extractor.v5"`;
- `kind == "grammar_feature_page"`;
- `page.page_number == 1`;
- `page.page_size == 300`;
- `page.total_sentences == 1`;
- `page.sentence_start == 0`;
- `page.sentence_end_exclusive == 1`;
- `features.length == 1`;
- first feature has `sentence_index == 0` and `text == "She is happy."`;
- feature group keys are present exactly as schema requires;
- all WordRefs point to words in the current sentence.

**Expected assertions:**

- `assert output["schema_version"] == "grammar_feature_extractor.v5"`
- `assert output["kind"] == "grammar_feature_page"`
- `assert output["page"]["total_sentences"] == 1`
- `assert len(output["features"]) == 1`
- `assert output validates against grammar_feature_page.v5.schema.json`
- `assert no diagnostic has result_impact == "extraction_failed"`

**Automation notes:** This test has a committed golden output; assert the full canonical payload.

**Contract resolution:** Finalized.

---

### TC-002: Empty document returns valid empty page and manifest

**Category:** Valid / Boundary / Manifest  
**Priority:** P0  
**Contract status:** Confirmed by input schema, page schema, manifest schema, architecture manifest policy.

**Input data:** F002.  
**Config:** CFG-001.

**Execution steps:**

1. Validate F002.
2. Run API `extract_page`.
3. Run CLI output-dir mode into an empty temp directory.
4. Validate page and manifest.

**Expected result:**

- page output has `features == []`;
- `page.total_sentences == 0`;
- `page.sentence_start == 0`;
- `page.sentence_end_exclusive == 0`;
- output-dir contains `grammar_features.manifest.json` and exactly one page file;
- manifest `page_count == 1`;
- manifest first page range is `0..0`;
- manifest page file name matches `^grammar_features\.page_[0-9]{5,}\.json$`.

**Expected assertions:**

- `assert output["features"] == []`
- `assert manifest["page_count"] == 1`
- `assert manifest["pages"][0]["sentence_start"] == 0`
- `assert manifest["pages"][0]["sentence_end_exclusive"] == 0`
- `assert page sha256 matches canonical file bytes`

**Automation notes:** Use temp directory.

**Contract resolution:** Finalized.

---

### TC-003: Raw uploaded Alice fixture without schema_version is rejected

**Category:** Invalid / Schema / Regression  
**Priority:** P0  
**Contract status:** Confirmed by input schema.

**Input data:** F003.

**Execution steps:**

1. Run schema validation against F003.
2. Run CLI with `--input fixtures/inputs/filtered_annotated_document.raw.json`.

**Expected result:**

- schema validation fails because `schema_version` is required;
- CLI exits `1`;
- stdout is empty;
- stderr validates as `CliError`;
- `error_code == "input_validation_error"`.

**Expected assertions:**

- `assert schema validation fails`
- `assert exit_code == 1`
- `assert cli_error["error_code"] == "input_validation_error"`
- `assert no output artifact exists`

**Automation notes:** If a separate adapter normalizes raw upstream files, test it separately; strict CLI must still reject F003 unless contract changes.

**Contract resolution:** Finalized.

---

### TC-004: Normalized large Alice fixture is processed deterministically

**Category:** Valid / Large input / Determinism  
**Priority:** P1  
**Contract status:** Confirmed by input schema and deterministic output contract.

**Input data:** F004.

**Config:** CFG-001.

**Execution steps:**

1. Build F004 from F003 using the documented build rule.
2. Validate F004 against input schema.
3. Run CLI page 1 with page size 300 twice.
4. Validate both outputs against page schema.
5. Compare canonical stdout bytes.

**Expected result:**

- F004 metadata matches expected counts and checksum;
- both runs exit `0`;
- both outputs are byte-identical;
- `page.page_size == 300`;
- `page.total_sentences == 25`;
- `features.length <= 300`;
- sentence indices are ascending.

**Expected assertions:**

- `assert normalized_sha256 == "4c8158d54197b78e599cf32db9a758aab343272eec417d9bddfd68077d7bab21"`
- `assert output["page"]["total_sentences"] == 25`
- `assert run1.stdout == run2.stdout`

**Automation notes:** This is not a golden feature-content test.

**Contract resolution:** Finalized.

---

### TC-005: Head out of range fails semantic validation

**Category:** Invalid / Semantic validation  
**Priority:** P0  
**Contract status:** Confirmed by semantic validation registry.

**Input data:** F005.

**Execution steps:**

1. Validate F005 structurally.
2. Run semantic input validation.
3. Run CLI with F005.

**Expected result:**

- semantic validation fails with `head_out_of_range`;
- API exception name: `InputValidationError`;
- CLI error code: `input_validation_error`;
- exit code: `1`.

**Expected assertions:**

- `assert validation_code == "head_out_of_range"`
- `assert cli_error["details"]["validation_code"] == "head_out_of_range"` when details are exposed
- `assert exit_code == 1`

**Automation notes:** If schema catches this first, public failure still must map to input validation.

**Contract resolution:** Finalized. `CliError.details` MUST include scalar `validation_code`; `json_path` is required when the validator can identify a stable JSON Pointer.

---

### TC-006: Dependency cycle fails semantic validation

**Category:** Invalid / Semantic validation  
**Priority:** P0  
**Contract status:** Confirmed by semantic validation registry.

**Input data:** F006.

**Expected result:**

- validation code: `dependency_cycle`;
- API exception: `InputValidationError`;
- CLI error code: `input_validation_error`;
- exit code: `1`;
- no output page/document is produced.

**Expected assertions:**

- `assert validation_code == "dependency_cycle"`
- `assert stdout == ""`
- `assert no output file exists`

**Contract resolution:** Finalized; F006 includes a root to avoid missing-root precedence.

---

### TC-007: Token/words mismatch fails semantic validation

**Category:** Invalid / Semantic validation  
**Priority:** P0  
**Contract status:** Confirmed by semantic validation registry.

**Input data:** F007.

**Expected result:**

- validation code: `token_words_mismatch`;
- no extraction output.

**Expected assertions:**

- `assert validation_code == "token_words_mismatch"`
- `assert raises InputValidationError`

**Automation notes:** Comparison rule should check ordered token word list against `sentence.words` by text and span.

**Contract resolution:** Finalized. The required comparison is the ordered flattened `tokens[*].words` list against `sentence.words` by `(text, lemma, upos, start_char, end_char)`; stricter validators may add diagnostics but MUST still emit `token_words_mismatch` for this fixture.

---

### TC-008: Unknown top-level field is rejected

**Category:** Invalid / Schema validation  
**Priority:** P0  
**Contract status:** Confirmed by `additionalProperties: false` and semantic code `unknown_input_field`.

**Input data:** F008.

**Expected result:**

- schema validation fails due to `unexpected`;
- public error maps to `input_validation_error`;
- details contain `validation_code == "unknown_input_field"` and `json_path == "/unexpected"` for this fixture.

**Expected assertions:**

- `assert schema validation fails`
- `assert cli_error["error_code"] == "input_validation_error"`
- `assert cli_error["details"]["validation_code"] == "unknown_input_field"`
- `assert cli_error["details"]["json_path"] == "/unexpected"`

**Contract resolution:** Finalized. Unknown top-level fields are normalized into `details.validation_code == "unknown_input_field"`.

---

### TC-009: Disabled evidence preserves group shape and marks matcher incomplete

**Category:** Config / Output contract  
**Priority:** P0  
**Contract status:** Confirmed by architecture final decisions and schema required feature-group keys.

**Input data:** F001.

**Config patch:**

```json
{
  "include_evidence": false
}
```

**CLI command:**

```bash
grammar-feature-extractor --input fixtures/inputs/valid_minimal_copular.json --no-evidence
```

**Expected result:**

- extraction succeeds;
- `features[0].features.evidence.words == []`;
- `features[0].features.evidence.dependencies == []`;
- `output_completeness.matcher_complete == false`;
- `output_completeness.omitted_feature_groups` contains `"evidence"`;
- page still validates against schema.

**Expected assertions:**

- `assert "evidence" in output["features"][0]["features"]`
- `assert output["features"][0]["features"]["evidence"] == {"words": [], "dependencies": []}`
- `assert output["output_completeness"]["matcher_complete"] is False`

**Contract resolution:** Finalized.

---

### TC-010: Unsupported CLI --config is a usage error

**Category:** CLI / Usage  
**Priority:** P0  
**Contract status:** Confirmed by v5 raw/resolved config decision.

**Input data:** F001.

**Command:**

```bash
grammar-feature-extractor --input fixtures/inputs/valid_minimal_copular.json --config config.json
```

**Expected result:**

- exit code `2`;
- stdout empty;
- stderr validates as `CliError`;
- `error_code == "cli_usage_error"`.

**Expected assertions:**

- `assert exit_code == 2`
- `assert cli_error["error_code"] == "cli_usage_error"`

**Contract resolution:** Finalized.

---

### TC-011: Page 2 with page size 1 returns only second sentence

**Category:** Paging / CLI / API  
**Priority:** P0  
**Input data:** F010.

**Config patch:**

```json
{
  "page_number": 2,
  "page_size": 1
}
```

**Command:**

```bash
grammar-feature-extractor --input fixtures/inputs/valid_two_sentences.json --page 2 --page-size 1
```

**Expected result:**

- `page.page_number == 2`;
- `page.page_size == 1`;
- `page.total_sentences == 2`;
- `page.sentence_start == 1`;
- `page.sentence_end_exclusive == 2`;
- `features.length == 1`;
- emitted sentence has `sentence_index == 1` and `text == "Stop!"`.

**Expected assertions:**

- `assert output["features"][0]["sentence_index"] == 1`
- `assert output["features"][0]["text"] == "Stop!"`

**Contract resolution:** Finalized.

---

### TC-012: Page beyond document returns valid empty page

**Category:** Boundary / Paging  
**Priority:** P1  
**Input data:** F001.

**Config patch:**

```json
{
  "page_number": 2,
  "page_size": 1
}
```

**Expected result:**

- extraction succeeds;
- `features == []`;
- `page.total_sentences == 1`;
- `page.sentence_start == 1`;
- `page.sentence_end_exclusive == 1`;
- `page.has_next_page == false`.

**Expected assertions:**

- `assert output["features"] == []`
- `assert output validates against grammar_feature_page.v5.schema.json`

**Contract resolution:** Finalized.

---

### TC-013: Malformed morphology feats emits registry diagnostic

**Category:** Diagnostics  
**Priority:** P1  
**Contract status:** Confirmed diagnostic code exists; exact emission depends on extractor behavior for malformed optional feats.

**Input data:** F009.

**Expected result if non-fatal degradation is implemented:**

- extraction succeeds;
- `features[*].features.diagnostics` contains code `malformed_morphology_feats`;
- diagnostic severity is `warning`;
- diagnostic has non-empty `refs`;
- diagnostic has non-empty `feature_path` because registry requires it.

**Expected assertions:**

- `assert "malformed_morphology_feats" in diagnostic_codes`
- `assert diagnostic["severity"] == "warning"`
- `assert diagnostic validates against FeatureDiagnostic schema`
- `assert diagnostic registry validation passes`

**Contract resolution:** Finalized. A non-empty but unparsable `feats` string is recoverable and MUST emit `malformed_morphology_feats`; `feats: null` remains a schema/input validation failure.

---

### TC-014: Output page too large is fatal before successful serialization

**Category:** Fatal / Serialization / Regression  
**Priority:** P0  
**Contract status:** Confirmed fatal mapping.

**Input data:** F001.

**Config patch:**

```json
{
  "limits": {
    "max_output_page_bytes": 1
  }
}
```

**Expected result:**

- API raises `SerializationError` or documented equivalent;
- CLI exits `1`;
- `cli_error.error_code == "output_serialization_error"`;
- stdout is empty;
- no successful output file exists.

**Expected assertions:**

- `assert exit_code == 1`
- `assert cli_error["error_code"] == "output_serialization_error"`
- `assert no output file exists`

**Automation notes:** This replaces brittle monkeypatch-only duplicate-ID tests with a public trigger.

**Contract resolution:** Finalized. TC-014 is an API/library serialization-limit test because v5 CLI intentionally has no `--config`; CLI coverage for this condition is allowed only through an implementation-owned test seam and is not required for black-box CLI automation.

---

### TC-015: Output-dir manifest pages and hashes are valid

**Category:** Manifest / Filesystem / Integration  
**Priority:** P0  
**Input data:** F004.

**Command:**

```bash
grammar-feature-extractor --input fixtures/inputs/filtered_annotated_document.v5.json --output-dir tmp/grammar_features --page-size 300
```

**Expected result:**

- exit `0`;
- stdout empty;
- output dir contains `grammar_features.manifest.json`;
- page files are named `grammar_features.page_00001.json`, `grammar_features.page_00002.json`, etc.;
- manifest validates against schema;
- `page_count == len(pages)`;
- page ranges are sorted, gap-free, non-overlapping;
- last `sentence_end_exclusive == total_sentences`;
- every page file exists;
- every page `sha256` matches canonical UTF-8 JSON bytes including final newline.

**Expected assertions:**

- `assert manifest["kind"] == "grammar_feature_manifest"`
- `assert manifest["page_count"] == len(manifest["pages"])`
- `assert ranges are gap-free`
- `assert sha256(file_bytes) == page["sha256"]`

**Contract resolution:** Finalized.

---

### TC-016: Output symlink target is rejected

**Category:** Security / Filesystem  
**Priority:** P0  
**Input data:** F001.

**Preconditions:** Platform supports symlinks. If symlink creation is unavailable, mark test skipped with reason `platform does not support symlink creation in test environment`.

**Execution steps:**

1. Create temp directory.
2. Create symlink `tmp/out.json` pointing to `tmp/target.json`.
3. Run CLI `--input F001 --output tmp/out.json`.

**Expected result:**

- exit code `3`;
- stdout empty;
- stderr `CliError.error_code == "output_write_error"`;
- symlink target is not modified;
- no completed output is written.

**Expected assertions:**

- `assert exit_code == 3`
- `assert cli_error["error_code"] == "output_write_error"`
- `assert target bytes unchanged`

**Contract resolution:** Symlink behavior is normative. If the OS/test runner cannot create symlinks, run the same assertions through mocked path metadata and mark only the OS fixture setup as skipped.

---

### TC-017: Canonical serialization is stable

**Category:** Serialization / Determinism  
**Priority:** P0  
**Input data:** F001.

**Execution steps:**

1. Run CLI with `--output tmp/page.json` twice.
2. Read raw bytes.
3. Compare bytes.
4. Validate parsed JSON.

**Expected result:**

- output bytes are valid UTF-8;
- no BOM;
- exactly one final newline;
- repeated bytes are identical;
- output validates against page schema;
- no timestamps/random IDs/absolute local paths appear.

**Expected assertions:**

- `assert not bytes.startswith(b"\xef\xbb\xbf")`
- `assert bytes.endswith(b"\n")`
- `assert run1_bytes == run2_bytes`

**Contract resolution:** Finalized. Canonical serializer order is schema order; byte comparison is required for serializer/golden tests, while structural tests may compare parsed objects.

---

### TC-018: Feature IDs and output ordering are deterministic

**Category:** Determinism / Regression  
**Priority:** P0  
**Input data:** F001 and F004.

**Expected result:**

- every emitted `id` matching FeatureId paths matches `^s[0-9]+\.[a-z_]+\.[1-9][0-9]*$`;
- IDs are unique within a sentence feature object;
- repeated runs produce identical canonical bytes;
- sentence indices are ascending.

**Expected assertions:**

- `assert all ids match FeatureId pattern`
- `assert no duplicate ids within sentence`
- `assert run1_bytes == run2_bytes`

**Automation notes:** Discover matcher-facing paths from schema/feature-path registry where possible.

**Contract resolution:** Finalized. The traversal list for ID-bearing fields MUST be generated from the committed schemas and checked into test helpers.

---

### TC-019: Grammar person fields are integers, UD morphology Person is string

**Category:** Schema / Typing / Regression  
**Priority:** P0  
**Input data:** F001.

**Expected result:**

- any emitted `AgreementFeature.subject_person` or `predicate_person` is JSON integer `1`, `2`, or `3`;
- any emitted `MorphFeature.features.Person` is string `"1"`, `"2"`, or `"3"`;
- output schema validation catches violations.

**Expected assertions:**

- `assert isinstance(agreement["subject_person"], int)` when field is present
- `assert morph["features"]["Person"] in ["1", "2", "3"]` when field is present
- `assert output validates against schema`

**Contract resolution:** Finalized. Non-golden fixture assertions are conditional on presence; committed golden fixtures define exact required feature presence.

---

### TC-020: Bundled schema defs match common defs

**Category:** Schema drift / CI  
**Priority:** P1

**Input artifacts:**

- `grammar_feature_common.v5.schema.json`;
- `grammar_feature_page.v5.schema.json`;
- `grammar_feature_document.v5.schema.json`;
- `grammar_feature_manifest.v5.schema.json`;
- `grammar_feature_diagnostics.v5.schema.json`.

**Execution steps:**

1. Load common schema `$defs`.
2. Load bundled schema `$defs` from page/document/manifest/diagnostics.
3. Canonically serialize each shared definition.
4. Compare common definition bytes to bundled definition bytes.

**Expected result:**

- all shared `$defs` are byte-equivalent;
- no manual drift is detected.

**Expected assertions:**

- `assert canonical(common["$defs"][name]) == canonical(bundle["$defs"][name])`

**Contract resolution:** Finalized. Bundled schemas MUST contain byte-equivalent shared `$defs`; compare all shared definitions from `grammar_feature_common.v5.schema.json`.

---

### TC-021: File-backed runtime resource must have valid SHA-256

**Category:** Runtime metadata / Resource hash policy  
**Priority:** P1

**Input object:** synthetic `runtime_metadata`.

```json
{
  "schema_version": "grammar_feature_extractor.v5",
  "extractor_version": "0.1.0",
  "resources": [
    {
      "kind": "registry",
      "name": "diagnostic_registry",
      "version": "v5",
      "sha256": "not-a-sha256",
      "required": true
    }
  ]
}
```

**Execution steps:**

1. Validate object against `ExtractorRuntimeMetadata` schema definition.
2. Run runtime metadata semantic validator.

**Expected result:**

- schema validation fails because `sha256` does not match `^[a-f0-9]{64}$`;
- if schema validation is not directly exposed for defs, semantic validator fails;
- error path points to `/resources/0/sha256` or equivalent.

**Expected assertions:**

- `assert validation fails`
- `assert message mentions "sha256"`

**Contract resolution:** Finalized. This is a test-helper concern; validate generated `$defs` objects directly with JSON Schema and do not require a public runtime helper.

---

### TC-022: Invalid JSON syntax emits exactly one CliError to stderr

**Category:** CLI / Error handling  
**Priority:** P0

**Input file:** `fixtures/inputs/invalid_json_syntax.json`

File content:

```json
{
  "schema_version":
```

**Command:**

```bash
grammar-feature-extractor --input fixtures/inputs/invalid_json_syntax.json
```

**Expected result:**

- exit code `1`;
- stdout empty;
- stderr is exactly one JSON object followed by one newline;
- stderr validates against `cli_error.v5.schema.json`;
- `schema_version == "grammar_feature_extractor.v5"`;
- `kind == "cli_error"`;
- `error_code == "input_json_serialization_error"`.

**Expected assertions:**

- `assert exit_code == 1`
- `assert stdout == ""`
- `assert stderr.endswith("\n")`
- `assert parsed_stderr validates against cli_error.v5.schema.json`

**Contract resolution:** Finalized. Malformed JSON syntax maps to `input_json_serialization_error`.

---

### TC-023: Every successful output validates against its committed schema

**Category:** Schema / Contract  
**Priority:** P0

**Input fixtures:** F001, F002, F004.

**Execution steps:**

1. Run API `extract(F001)` and validate result against `grammar_feature_document.v5.schema.json`.
2. Run API `extract_page(F001)` and validate against `grammar_feature_page.v5.schema.json`.
3. Run CLI output-dir for F002 and validate manifest against `grammar_feature_manifest.v5.schema.json`.
4. Run diagnostic collection tests and validate against `grammar_feature_diagnostics.v5.schema.json` when standalone diagnostics are emitted.

**Expected result:**

- all successful outputs validate;
- unknown output fields are rejected;
- schema version is always `grammar_feature_extractor.v5`.

**Expected assertions:**

- `assert document_output validates against grammar_feature_document.v5.schema.json`
- `assert page_output validates against grammar_feature_page.v5.schema.json`
- `assert manifest validates against grammar_feature_manifest.v5.schema.json`

**Contract resolution:** Finalized. Standalone diagnostics are validated as schema/registry fixtures; no public diagnostics CLI/API is required.

---

### TC-024: Every emitted diagnostic is registry-compliant

**Category:** Diagnostic registry  
**Priority:** P0

**Input data:** F009 or any fixture that emits diagnostics.

**Expected result:**

- every emitted diagnostic code exists in `diagnostic_registry.v5.json`;
- severity matches registry;
- refs and feature_path obey registry requirements;
- no undocumented diagnostic code is emitted.

**Expected assertions:**

- `assert diagnostic["code"] in registry_codes`
- `assert diagnostic["severity"] == registry[code]["severity"]`
- `if registry[code]["refs_required"]: assert diagnostic["refs"]`
- `if registry[code]["feature_path_required"]: assert diagnostic.get("feature_path")`

**Contract resolution:** Finalized. Registry compliance is tested with synthetic diagnostic objects plus all diagnostics emitted by runtime fixtures; a runtime trigger is not required for every registry code.

---

### TC-025: Debug mode does not leak debug data into output payload

**Category:** Debug / Regression  
**Priority:** P1

**Input data:** F001.

**Command:**

```bash
grammar-feature-extractor --input fixtures/inputs/valid_minimal_copular.json --debug
```

**Expected result:**

- exit `0`;
- stdout parses as `GrammarFeaturePage`;
- output validates against page schema;
- no unknown top-level `debug` key exists;
- no schema-unknown debug-only nested fields exist;
- debug mode does not alter canonical page contents compared with non-debug mode.

**Expected assertions:**

- `assert output validates against grammar_feature_page.v5.schema.json`
- `assert "debug" not in output`
- `assert debug_stdout == normal_stdout`

**Contract resolution:** Finalized. Default CLI debug mode must not emit logs to stdout/stderr; any logs require a separate sink such as `--log-file`.

---

### TC-026: Full document API returns GrammarFeatureDocument

**Category:** API / Document output  
**Priority:** P0

**Input data:** F001.

**Execution steps:**

1. Run `GrammarFeatureExtractor.extract(F001, CFG-001)`.
2. Validate against `grammar_feature_document.v5.schema.json`.

**Expected result:**

- `kind == "grammar_feature_document"`;
- `source_sentence_count == 1`;
- `sentences.length == 1`;
- first sentence has `sentence_index == 0`.

**Expected assertions:**

- `assert output["kind"] == "grammar_feature_document"`
- `assert output["source_sentence_count"] == 1`
- `assert output validates against grammar_feature_document.v5.schema.json`

**Contract resolution:** Finalized. Import public API classes from `grammar_feature_extractor`.

---

### TC-027: CLI stdin/stdout success path

**Category:** CLI / Success  
**Priority:** P0

**Input data:** F001 passed on stdin.

**Command:**

```bash
cat fixtures/inputs/valid_minimal_copular.json | grammar-feature-extractor
```

**Expected result:**

- exit `0`;
- stdout contains exactly one `GrammarFeaturePage` JSON object;
- stdout validates against page schema;
- stderr is empty.

**Expected assertions:**

- `assert exit_code == 0`
- `assert stdout parses as JSON`
- `assert parsed_stdout["kind"] == "grammar_feature_page"`

**Contract resolution:** Finalized.

---

### TC-028: Output-dir overwrite policy

**Category:** Filesystem / Output-dir  
**Priority:** P1

**Input data:** F001.

**Execution steps:**

1. Create temp output dir with unrelated file `existing.txt`.
2. Run CLI with `--output-dir tempdir` without `--overwrite`.
3. Run CLI with same dir and `--overwrite`.

**Expected result:**

- without `--overwrite`: failure, exit `3`, `CliError.error_code == "output_write_error"`, no manifest written;
- unrelated `existing.txt` remains unchanged;
- with `--overwrite`: success only if the directory contains no unrelated files, or if unrelated files can be preserved while replacing only owned `grammar_features.page_*.json` and `grammar_features.manifest.json` files;
- completed manifest is valid.

**Expected assertions:**

- `assert exit_code == 3`
- `assert cli_error["error_code"] == "output_write_error"`
- `assert no completed manifest after failed run`
- `assert existing_unrelated_file_bytes_unchanged`
- `assert success_manifest validates after safe overwrite run`

**Contract resolution:** Finalized.

---

### TC-029: TokenEvidence.lower uses casefold

**Category:** Normalization / Regression  
**Priority:** P1

**Input data:** F011.

**Expected result:**

- output evidence contains word with `text == "Straße"`;
- same evidence item has `lower == "strasse"`;
- lowercasing must not be locale-dependent.

**Expected assertions:**

- `assert evidence_word["text"] == "Straße"`
- `assert evidence_word["lower"] == "strasse"`

**Contract resolution:** Finalized.

---

### TC-030: page_size greater than max_page_size fails config validation

**Category:** Config / Boundary  
**Priority:** P0

**Input data:** F001.

**Config patch:**

```json
{
  "page_size": 5001,
  "limits": {
    "max_page_size": 5000
  }
}
```

**CLI command:**

```bash
grammar-feature-extractor --input fixtures/inputs/valid_minimal_copular.json --page-size 5001
```

**Expected result:**

- API config validation fails with semantic code `page_size_exceeds_max_page_size`;
- exception: `ConfigurationError`;
- CLI error code: `configuration_error`;
- CLI exit code: `1`;
- `CliError.details.validation_code == "page_size_exceeds_max_page_size"`.

**Expected assertions:**

- `assert validation_code == "page_size_exceeds_max_page_size"` for API config validation
- `assert cli_error["error_code"] == "configuration_error"`
- `assert exit_code == 1`
- `assert cli_error["details"]["validation_code"] == "page_size_exceeds_max_page_size"`

**Contract resolution:** Finalized.

---

## 10. Negative and Edge Coverage Map

| Area | Fixture / TC | Expected code / result |
|---|---|---|
| Missing `schema_version` | F003 / TC-003 | `input_validation_error` |
| Wrong input schema version | Add fixture with `schema_version: "legacy_wrong_schema_version"` | schema const failure |
| Missing `sentences` | Add schema-only fixture | required field failure |
| Missing `entities` | Add schema-only fixture | required field failure |
| Unknown top-level field | F008 / TC-008 | `unknown_input_field` or schema failure |
| Unknown nested word field | Add fixture | schema additional-property failure |
| Head out of range | F005 / TC-005 | `head_out_of_range` |
| Missing dependency root | F013 | `missing_dependency_root` |
| Dependency cycle | F006 / TC-006 | `dependency_cycle` |
| Invalid word span | F014 | `invalid_word_span` |
| Invalid entity span | F012 | `invalid_entity_span` |
| Token/words mismatch | F007 / TC-007 | `token_words_mismatch` |
| Malformed feats | F009 / TC-013 | `malformed_morphology_feats` or documented input error |
| Invalid config type | Add raw/resolved config fixture | schema failure |
| Unknown config field | Add config fixture | schema failure |
| page_size > max_page_size | TC-030 | `page_size_exceeds_max_page_size` |
| output page too large | TC-014 | `output_page_too_large` / serialization error |
| output symlink | TC-016 | `output_write_error` |
| non-empty output-dir | TC-028 | no manifest on failure |
| debug mode | TC-025 | no payload mutation |

---

## 11. Schema and Registry Validation Tests

### SCHEMA-001: every schema is valid Draft 2020-12

Validate every `*.schema.json` file as a JSON Schema document.

### SCHEMA-002: schema `$id` uniqueness

Assert all schema `$id` values are unique.

### SCHEMA-003: registry meta-schema validation

Validate:

- `diagnostic_registry.v5.json` against `diagnostic_registry.v5.schema.json`;
- `construction_signature_registry.v5.json` against `construction_signature_registry.v5.schema.json`;
- `predicate_form_signature_registry.v5.json` against `predicate_form_signature_registry.v5.schema.json`;
- `feature_path_registry.v5.json` against `feature_path_registry.v5.schema.json`;
- `semantic_validation_registry.v5.json` against `semantic_validation_registry.v5.schema.json`.

### SCHEMA-004: registry uniqueness

Assert:

- diagnostic codes are unique;
- semantic validation codes are unique;
- construction signatures are unique;
- predicate form signatures are unique;
- feature paths are unique.

Uploaded registry counts:

- diagnostic codes: `21`;
- semantic validation codes: `21`;
- construction signatures: `24`;
- predicate form signatures: `21`;
- feature paths: `21`.

### SCHEMA-005: feature path enum compatibility

For every `feature_path_registry` entry with `value_type == "enum"`, assert `enum_values` is present and non-empty.

---

## 12. Regression Tests

| Regression risk | Required test |
|---|---|
| Raw upstream fixture accepted silently | TC-003 |
| Disabled evidence removes required group key | TC-009 |
| Fatal diagnostic serialized as success | TC-014 |
| Manifest written before page files | TC-015 with forced page write failure |
| Debug mode mutates payload | TC-025 |
| Feature IDs unstable | TC-018 |
| Schema `$defs` drift | TC-020 |
| Person fields serialized as strings outside morphology | TC-019 |
| Diagnostics code outside registry | TC-024 |
| Unicode normalization uses `.lower()` instead of `.casefold()` | TC-029 |
| CLI writes partial stdout on failure | TC-022 |

---

## 13. Test Automation Recommendations

1. **Generate models from schemas** rather than handwritten interfaces.
2. **Run schema tests first** so broken contracts fail before behavioral tests.
3. **Keep fixture generation deterministic** and record checksums for large fixtures.
4. **Prefer public triggers** over monkeypatching for fatal behavior.
5. **Use semantic registries as source of expected error mapping**.
6. **Treat exact linguistic feature output as golden-only**, not as general invariant.
7. **Run CLI tests in isolated temp directories** and assert no unexpected files remain.
8. **Make platform-dependent filesystem tests explicit** with skip reasons.
9. **Fail collection on missing schemas/registries** instead of silently weakening coverage.

---

## 14. Test Case Self-Containment Checklist

| Check | Pass/Fail | Notes |
|---|---|---|
| Every P0 test case has fixture/config/steps/expected result | Pass | TC-001 through TC-030 include fixture references defined inside this guide and required committed fixtures/goldens. |
| Matrix-only TC entries are expanded | Pass | TC-021 through TC-025 now have detailed sections. |
| CLI command is defined | Pass | Canonical command is `grammar-feature-extractor`. |
| Required artifacts are listed | Pass | Section 2 plus fixture hash manifests list schemas, registries, large fixtures, and positive goldens. |
| Config patches are unambiguous | Pass | Section 4 defines deep-merge into CFG-001. |
| Output comparison rules are centralized | Pass | Section 5. |
| Diagnostic assertions are centralized | Pass | Section 6. |
| Large fixture is reproducible | Pass | F003/F004 include source checksum, build rule, counts, normalized checksum. |
| Unsupported assumptions are marked | Partial Pass | Remaining API import path and CLI/config precedence are explicitly marked as ambiguities. |
| All schema contracts are covered | Pass | Section 11 covers schemas, registries, uniqueness, drift. |
| All diagnostic codes are covered | Partial Pass | Registry compliance is covered; forcing every diagnostic code requires additional implementation-specific fixtures. |
| Negative cases are executable | Partial Pass | Core P0 negative cases are executable; extra schema-only variants are listed in Section 10. |

---

## 15. Definition of Done for Automation Readiness

The guide is considered automation-ready when:

1. Canonical Python API import paths are fixed to `grammar_feature_extractor`.
2. Exception class import paths are fixed to `grammar_feature_extractor`.
3. Required P0 fixtures and positive goldens are committed under `fixtures/inputs/`, `fixtures/outputs/`, and mirrored under `docs/architecture/fixtures/grammar_feature_extractor/v5/`.
4. CFG-001 is committed as `docs/architecture/fixtures/grammar_feature_extractor/v5/default_resolved_config.json`.
5. F003 raw fixture is committed with sha256 `d67b59a002ffa417532908d3d4ab23af4471cb88292cba3595780e0ae0f3385f`.
6. F004 normalized fixture is generated and committed with sha256 `4c8158d54197b78e599cf32db9a758aab343272eec417d9bddfd68077d7bab21`.
7. CLI tests can invoke `grammar-feature-extractor` from the test environment.
8. The implementation exposes public validators or CI/test helpers for semantic output, manifest, registry, and construction validation.
9. CLI precedence is finalized: `page_size > max_page_size` is `configuration_error`, exit `1`.
10. Failure stderr is finalized: exactly one `CliError` JSON object plus newline, with logs isolated to a separate sink.
