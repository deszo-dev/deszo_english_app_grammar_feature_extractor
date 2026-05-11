# grammar_feature_extractor

Pure transform module that converts a validated `AnnotatedDocument` JSON payload
from `stanza_annotator` into deterministic grammar feature pages. The
authoritative output contract is `grammar_feature_extractor.v5`
(see `docs/architecture/grammar_feature_extractor_architecture_v5.md`).

The CLI reads JSON from `stdin` or `--input`, writes only result JSON to
`stdout` or `--output`, and sends a single-line `CliError` JSON to `stderr` on
failure. Logs are isolated from the JSON channels.

```powershell
grammar-feature-extractor --input annotated_document.json --page 1 --page-size 300
```

Input documents MUST declare
`schema_version = "grammar_feature_extractor.annotated_document.input.v5"`.

CLI exit codes:

- `0` success
- `1` input/schema/config validation error
- `2` CLI usage error
- `3` output write failure
- `4` unexpected runtime/system error
