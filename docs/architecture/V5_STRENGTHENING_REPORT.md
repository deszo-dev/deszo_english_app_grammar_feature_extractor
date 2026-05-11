# v5 strengthening report

Applied hardening changes:

- Materialized Markdown-only test fixtures into `fixtures/inputs/` and `fixtures/outputs/`.
- Added `fixtures/fixture_manifest.v5.json` with SHA-256 hashes.
- Added `fixtures/grammar_feature_extractor/v5/default_resolved_config.json`.
- Extended `semantic_validation_registry.v5.schema.json` and `semantic_validation_registry.v5.json` with machine-testable `when_emitted`, `affected_entity`, `message_template`, `required_details`, and `test_case`.
- Added architecture/testing prose gates forbidding Markdown scraping as a fixture source of truth.
