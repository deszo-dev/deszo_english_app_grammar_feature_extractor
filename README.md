# grammar_feature_extractor

Pure transform module that converts a validated `stanza_annotator_document` handoff payload into deterministic grammar feature pages.

Canonical documentation now lives in the repository root:

- docs package: `docs/docs/`
- handoff contract: `docs/docs/stanza-document-handoff.md`
- schemas: `docs/docs/schemas/`

## CLI

The CLI reads JSON from `stdin` or `--input`, writes result JSON to `stdout` or `--output`, and sends logs/errors to `stderr`.

```powershell
python -m grammar_feature_extractor --input stanza_document.json --page 1 --page-size 300
```

To emit a paginated output directory:

```powershell
python -m grammar_feature_extractor --input stanza_document.json --output-dir out --overwrite
```

To process a directory of stanza documents in one CLI run:

```powershell
python -m grammar_feature_extractor --input-dir stanza_documents --output-dir out --overwrite
```

Batch mode reads non-recursive `*.json` files from `--input-dir`, writes one
feature package per input under `--output-dir`, and writes
`grammar_features.batch_manifest.json` at the output root.

The only supported input is `stanza_annotator_document` output. AQF and historical flat annotated-document envelopes are intentionally rejected.

Outputs are emitted as `grammar_feature_extractor.v5` artifacts:

- `grammar_features.page_*.json`
- `grammar_features.manifest.json`
- `grammar_features.batch_manifest.json` in batch mode

## Validation

```powershell
pytest grammar_feature_extractor/tests -q
python docs/tools/validate_static_docs_package.py
```
