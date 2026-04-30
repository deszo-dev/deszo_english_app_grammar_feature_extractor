# Changelog

## Unreleased

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
