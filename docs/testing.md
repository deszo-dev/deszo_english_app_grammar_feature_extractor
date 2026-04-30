# grammar_feature_extractor testing plan

## Test layers

- Unit tests cover validation, core extraction, pagination, and serialization with
  no external IO.
- CLI integration tests run the installed module entrypoint via subprocess and
  verify stream separation and exit codes.
- Property-based tests cover deterministic invariants where examples alone are
  too narrow.
- Coq checks compile `coq/GrammarFeatureExtractorSpec.v` in CI when `coqc` is
  available.

## Required unit coverage

- Validate `AnnotatedDocument` shape, required fields, strict primitive types,
  sentence/token word consistency, character spans, and dependency head range.
- Reject raw text and malformed JSON as expected errors.
- Derive `WordRef` from sentence word order and verify sentence-local feature refs.
- Extract documented syntax mappings: phrases, clause-local roles and valency,
  predicate groups, complements, coordination, subordination, and NP profiles.
- Extract predicate-local TAVM and agreement from UD `feats`, auxiliaries,
  passive signals, modals, copulas, and finite subject/predicate morphology.
- Extract lexical heuristics for question type, comparatives, phrasal verbs,
  discourse markers, and complexity.
- Emit deterministic diagnostics for graceful degradation.
- Preserve stable JSON field order and omit optional `None` fields.
- Keep diagnostics as an always-present field, using `[]` when disabled.
- Verify default paging, custom paging, max page-size rejection, and out-of-range
  empty pages.

## Required CLI coverage

- `stdout` contains only JSON on success when `--output` is absent.
- `stderr` contains logs/errors only.
- `--output` leaves `stdout` empty and writes a complete JSON file atomically.
- Expected input/configuration errors exit with code `1` and no JSON payload.
- System output-write failures exit with code `2`.
- `--debug` changes logs but not the JSON payload.

## Property-based candidates

- `features.length <= page_size`.
- Pagination preserves `total_sentences`.
- Repeated extraction with the same input/config produces identical JSON.
- Debug and non-debug extraction produce equivalent payloads.
- Every emitted `WordRef` is within the source sentence.
