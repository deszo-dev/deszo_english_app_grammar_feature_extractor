# grammar_feature_extractor v5 hardening changelog

This changelog records documentation-only hardening changes made after the readiness review. The runtime/output schema version remains `grammar_feature_extractor.v5`.

## Resolved P0 blockers

- Added module-specific precedence over generic guidelines.
- Split compact serialized `runtime_metadata` from richer stage/orchestrator metadata returned by `get_runtime_metadata()`.
- Aligned public Python config models with the resolved config schema via `ExtractorLimits`, `ExtractorConfig`, and `PagingConfig`.
- Finalized `extract_pages()` as an all-pages API from page 1.
- Made CLI failure `stderr` exactly one `CliError` JSON object plus newline; logs are isolated from stdout/stderr JSON channels.
- Finalized CLI validation precedence and exit-code mapping.
- Replaced missing external large fixtures with committed deterministic synthetic raw/normalized fixtures and hashes.
- Added committed positive golden page fixtures for minimal copular and present-simple lexical cases.
- Added limit enforcement and filesystem safety matrices.
- Documented semantic validation code `invalid_word_ref` vs deprecated diagnostic compatibility code `invalid_word_ref_generated`.
- Fixed deterministic diagnostic truncation ordering.

## Remaining v5 scope

The package is still v5. No output schema version bump was introduced. Any future breaking schema or serialized-output change must use a new versioned contract.
