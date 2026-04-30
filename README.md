# grammar_feature_extractor

Pure transform module that converts a validated `AnnotatedDocument` JSON payload
from `stanza_annotator` into deterministic grammar feature pages.

The CLI reads JSON from `stdin` or `--input`, writes only result JSON to
`stdout` or `--output`, and sends logs/errors to `stderr`.

```powershell
grammar-feature-extractor --input annotated_document.json --page 1 --page-size 300
```
