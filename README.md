# grammar_feature_extractor

Pure transform module that converts a validated `AnnotatedDocument` payload into deterministic grammar feature pages.

Canonical documentation now lives in the repository root:

- architecture: `docs/architecture/grammar_feature_extractor_architecture_v5.md`
- testing: `docs/testing/grammar_feature_extractor_testing.md`
- shared schemas and registries: `docs/architecture/schemas/`
- shared guidelines: `docs/guidelines/`

## CLI

The CLI reads JSON from `stdin` or `--input`, writes result JSON to `stdout` or `--output`, and sends logs/errors to `stderr`.

```powershell
python -m grammar_feature_extractor --input annotated_document.json --page 1 --page-size 300
```

To emit a paginated output directory:

```powershell
python -m grammar_feature_extractor --input annotated_document.json --output-dir out --overwrite
```

Current production input is a successful `annotation_quality_filter.v2.0` envelope. Legacy flat `grammar_feature_extractor.annotated_document.input.v3` fixtures are still accepted as a compatibility path.

Outputs are emitted as `grammar_feature_extractor.v5` artifacts:

- `grammar_features.page_*.json`
- `grammar_features.manifest.json`

## Validation

```powershell
pytest grammar_feature_extractor/tests -q
python docs/testing/scripts/validate_doc_contracts.py
```

Module-local `docs/` content is transitional and should not be treated as the primary source of truth when it duplicates root `docs/`.
