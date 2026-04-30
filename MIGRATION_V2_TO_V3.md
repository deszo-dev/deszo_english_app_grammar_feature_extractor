# Migration v2 to v3

This document records the implementation policy for the v3 migration. The
authoritative public contract remains `docs/architecture.md`; this file captures
the decisions that guide the migration work.

## Fixed Decisions

1. `grammar_feature_extractor.v3` is a breaking output contract.
2. v2 golden outputs are reference-only fixtures, not active expected output.
3. Public v3 feature-group fields are always present.
4. Disabled feature groups serialize as empty arrays or empty objects, not as
   omitted fields.
5. `features.evidence` remains present when evidence is disabled:

   ```json
   {
     "words": [],
     "dependencies": []
   }
   ```

6. `features.diagnostics` remains present when diagnostics are disabled:

   ```json
   []
   ```

7. `syntax.predicate_groups` is removed from public v3 output. v3 uses only
   `syntax.predicates`.
8. The implementation baseline remains dataclasses, custom validation, and a
   custom stable JSON serializer.
9. File splitting should be gradual. Start with `SentenceContext`, evidence, and
   morphology builders before broader mechanical decomposition.
10. Construction signatures must come from registry constants.
11. Feature metadata is represented with flat fields such as `evidence_refs`,
    `sources`, and `confidence`; there is no mandatory nested `meta` object.
12. Public diagnostic codes are snake_case.
13. Coq is updated at stable structural checkpoints, not after every individual
    builder.

## Fixture Policy

v2 fixtures live under:

```text
tests/fixtures/v2_reference/
```

They are retained for migration comparison and manual debugging only. Active
golden tests must assert v3 output.

## First Milestone

The first implementation milestone is intentionally smaller than full P0:

```text
M1:
  valid v3 shell
  input validation
  paging
  stable serialization
  CLI
  evidence layer
  morphology layer
  empty-but-valid syntax/lexical/constructions/contrastive_support/absences
  diagnostics infrastructure
```

Full matcher readiness belongs to the next milestone.

Checkpoint artifacts:

```text
tests/fixtures/v3_minimal/
```

This fixture is the active minimal v3 reference for the shell, evidence,
morphology, empty-but-present feature groups, and the first structural syntax
surface.

## Documentation Rule

If a public schema, semantic rule, CLI flag, diagnostic code, or default behavior
changes, update `docs/architecture.md` in the same change as the implementation
and tests.
