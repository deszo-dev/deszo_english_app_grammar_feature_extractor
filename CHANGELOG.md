# Changelog

## Unreleased

- Added typed dataclasses for SyntaxFeatures placeholder fields:
  `PronounFeature`, `SpecialSubjectConstructionFeature`,
  `RelativeClauseFeature`, `ConditionalFeature`, `ReportedSpeechFeature`,
  `PassiveFeature`. The corresponding `SyntaxFeatures` fields are now strongly
  typed instead of `tuple[object, ...]`. Output JSON now contains structured
  objects in `syntax.pronouns`, `syntax.special_subject_constructions`,
  `syntax.relative_clauses`, `syntax.conditionals`, `syntax.reported_speech`,
  `syntax.passive`.
- Added new feature builders: `pronoun_builder`, `special_subject_builder`,
  `passive_builder`, `relative_clause_builder`, `conditional_builder`,
  `reported_speech_builder`. These are wired into `extract_sentence_features`.
- Added typed dataclass scaffolding for lexical layer (`TimeMarkerFeature`,
  `LexicalClassFeature`, `VerbPatternFeature`, `AdjectivePatternFeature`,
  `ComparisonFeature`, `TypedQuantifierFeature`, `PhrasalVerbFeature`,
  `DiscourseMarkerFeature`, `ContractionFeature`, `NounInflectionFeature`)
  plus NP-level `CountabilityFeature` and `ReferenceFeature`. The
  `LexicalFeatures.lexical_classes`, `verb_patterns`, `adjective_patterns`,
  and `quantifiers` fields are now typed; their builders remain follow-up.
- Added production `--output-dir` mode to the CLI, writing per-page
  `grammar_features.page_NNNNN.json` files with a final
  `grammar_features.manifest.json` (schema, kind, page_size, page_count,
  total_sentences, page list with sha256, diagnostics). `--output` and
  `--output-dir` are mutually exclusive.
- Extended `proof_surface_validator` to assert WordRef validity for the new
  syntax feature groups.
- Added tests for new feature groups and `--output-dir` (including
  debug/non-debug determinism).
- Added proof-surface foundation with `ProofProvenance`, feature tiers,
  proof sources, provenance serialization, and proof-surface validation.
- Updated the Coq spec to a v3 proof-surface shell with provenance and
  matcher-facing structural invariants.
- Added predicate TAVM/form signatures, lexical word-order/negation basics,
  NP/article profiles, first construction signatures, absence features,
  contrastive support hints, and catalog validation schema skeletons.
- Added v3 predicate parity extraction under `syntax.predicates`, replacing
  the old public `predicate_groups` shape.
- Added the v3 M1 checkpoint fixture under `tests/fixtures/v3_minimal/`.
- Added v3 structural syntax extraction for phrases, clauses, complements,
  coordination, and subordination.
- Added focused evidence and morphology tests for matcher-facing invariants.
- Documented the v2 to v3 migration policy.
- Moved v2 golden outputs under `tests/fixtures/v2_reference/` as
  reference-only fixtures.
- Initial v1 implementation scaffold.
