from __future__ import annotations

from collections.abc import Iterable

from grammar_feature_extractor._internal.models import (
    Confidence,
    FeatureTier,
    ProofProvenance,
    ProofSource,
    WordRef,
)


def normalize_refs(refs: Iterable[WordRef]) -> tuple[WordRef, ...]:
    return tuple(sorted(dict.fromkeys(refs)))


def make_provenance(
    tier: FeatureTier,
    source: ProofSource,
    evidence_refs: Iterable[WordRef],
    confidence: Confidence,
    *,
    allow_empty: bool = False,
) -> ProofProvenance:
    refs = normalize_refs(evidence_refs)
    if not allow_empty and not refs:
        raise ValueError("ProofProvenance requires non-empty evidence_refs.")
    if any(ref < 1 for ref in refs):
        raise ValueError("ProofProvenance evidence_refs must be positive WordRefs.")
    return ProofProvenance(
        tier=tier,
        source=source,
        evidence_refs=refs,
        confidence=confidence,
    )
