from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    ConstructionFeature,
    ContrastiveHint,
    ContrastiveSupportFeature,
)
from grammar_feature_extractor._internal.proof_surface import make_provenance


def build_contrastive_support(
    constructions: tuple[ConstructionFeature, ...],
) -> tuple[ContrastiveSupportFeature, ...]:
    items: list[ContrastiveSupportFeature] = []
    signatures = {item.signature: item for item in constructions}
    if "present_progressive_affirmative" in signatures:
        item = signatures["present_progressive_affirmative"]
        items.append(
            _hint(
                "present_simple_vs_present_progressive",
                "present_progressive",
                ("present_simple",),
                ("be + V-ing",),
                ("intended meaning: habitual vs ongoing",),
                item,
            )
        )
    if "present_perfect_have_participle" in signatures:
        item = signatures["present_perfect_have_participle"]
        items.append(
            _hint(
                "present_perfect_vs_past_simple",
                "present_perfect",
                ("past_simple",),
                ("have + past participle",),
                ("intended time relation",),
                item,
            )
        )
    for signature, observed in (
        ("article_indefinite_a_np", "a"),
        ("article_indefinite_an_np", "an"),
    ):
        if signature in signatures:
            item = signatures[signature]
            items.append(
                _hint(
                    "a_vs_an",
                    observed,
                    ("a" if observed == "an" else "an",),
                    ("article spelling class",),
                    ("phonology if spelling is insufficient",),
                    item,
                )
            )
    if "article_definite_the_np" in signatures:
        item = signatures["article_definite_the_np"]
        items.append(
            _hint(
                "a_an_vs_the",
                "the",
                ("a/an",),
                ("definite article",),
                ("discourse reference",),
                item,
            )
        )
    return tuple(items)


def _hint(
    hint: ContrastiveHint,
    observed: str,
    competing: tuple[str, ...],
    cues: tuple[str, ...],
    missing: tuple[str, ...],
    construction: ConstructionFeature,
) -> ContrastiveSupportFeature:
    return ContrastiveSupportFeature(
        contrastive_hint=hint,
        observed_choice=observed,
        competing_choices=competing,
        local_cues=cues,
        missing_context=missing,
        confidence="medium",
        provenance=make_provenance(
            "heuristic", "surface", construction.evidence_refs, "medium"
        ),
    )
