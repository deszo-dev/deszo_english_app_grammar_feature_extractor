# Migration v3 → v5

This document records the implementation policy for the v5 migration. The
authoritative public contract is
`docs/architecture/grammar_feature_extractor_architecture_v5.md`; this file
captures the decisions that guide migration work.

## Fixed Decisions

1. `grammar_feature_extractor.v5` is a breaking output contract. There is no
   compatibility shim for `grammar_feature_extractor.v3` or `.v4` payloads.
2. Input documents MUST declare
   `schema_version = "grammar_feature_extractor.annotated_document.input.v5"`.
3. Public v5 feature-group fields are always present. Disabled feature groups
   serialize as empty arrays or empty objects, never as omitted fields.
4. `features.evidence` remains present when evidence is disabled:

   ```json
   {
     "words": [],
     "dependencies": []
   }
   ```

5. `features.diagnostics` remains present when diagnostics are disabled:

   ```json
   []
   ```

6. `syntax.predicate_groups` (removed in v3) is not reintroduced. v5 uses only
   `syntax.predicates`.

## Public Python API changes (v3 → v5)

- Added `ExtractorLimits` (immutable dataclass) with eight hard limits
  (`max_input_bytes`, `max_sentences`, `max_words_per_sentence`,
  `max_total_words`, `max_page_size`, `max_output_page_bytes`,
  `max_output_pages`, `max_diagnostics_per_sentence`).
- `ExtractorConfig` now embeds `limits: ExtractorLimits`.
- Added `GrammarFeatureExtractor.extract_pages(document, paging, config)` as an
  all-pages API; `paging.page_number` MUST be `1`.
- Added `GrammarFeatureExtractor.get_runtime_metadata() -> StageRuntimeMetadata`.
- Added public exports `ExtractorLimits`, `StageRuntimeAsset`,
  `StageRuntimeMetadata`.
- `StageRuntimeMetadata` is now the v5 shape:
  `stage_name`, `stage_contract_version`, `output_schema_version`,
  `config_contract_version`, `module_version`, `source_fingerprint: str`,
  `dependencies: tuple[str, ...]`, `assets: tuple[StageRuntimeAsset, ...]`.
- `StageRuntimeAsset` fields: `name`, `kind`, `version`, `sha256: str | None`,
  `required: bool`.

## Runtime metadata projections

- The **serialized output projection** (embedded in
  `GrammarFeaturePage`/`Document`/`Manifest`) is compact:
  `{schema_version, extractor_version, resources}`. Resources are sorted by
  `(kind, name, version)` and SHA-256 hashed.
- The **stage/orchestrator projection** returned by
  `get_runtime_metadata()` is the richer `StageRuntimeMetadata` shape above.

Stage constants:

- `stage_name = "grammar_feature_extractor"` (renamed from
  `grammar_feature_extraction`).
- `stage_contract_version = "grammar_feature_extractor.stage.v5"`.
- `output_schema_version = "grammar_feature_extractor.v5"`.
- `config_contract_version = "grammar_feature_extractor.config.v5"`.

## CLI contract

- `stderr` on failure contains exactly one `CliError` JSON object plus a
  trailing newline; `stdout` is empty.
- Exit codes:
  - `0`: success.
  - `1`: input/schema/config validation errors.
  - `2`: CLI usage errors (unknown flags, mutually exclusive arguments).
  - `3`: output write failures.
  - `4`: unexpected runtime/system errors (including `FeatureExtractionError`).
- `CliError.schema_version = "grammar_feature_extractor.v5"` and
  `kind = "cli_error"`.

## Diagnostics and semantic validation

- Semantic code `invalid_word_ref` raises `FeatureExtractionError` (exit 4).
- Deprecated diagnostic code `invalid_word_ref_generated` is no longer emitted
  in v5.
- Truncation of per-sentence diagnostics follows
  `config.limits.max_diagnostics_per_sentence`:
  - `0`: suppressed entirely.
  - `1`: only the `diagnostics_truncated` marker.
  - `N > 1`: first `N-1` diagnostics plus `diagnostics_truncated` as the final
    entry.

## Feature support status

- `not_supported_in_v4_scope` is replaced by `out_of_scope`.

## Schemas and registries

All authoritative artifacts live under `docs/architecture/schema/` and use the
`*.v5.*` naming convention. The pre-v5 `*.v3.*` and `*.v4.*` artifacts are
removed.
