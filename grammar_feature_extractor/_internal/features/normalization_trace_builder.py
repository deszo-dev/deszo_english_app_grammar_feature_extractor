from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    NormalizationTrace,
    NormalizationTraceStep,
    PredicateFeature,
)


def _step(name: str, result: str, refs: tuple[int, ...] = (), reason: str | None = None) -> NormalizationTraceStep:
    return NormalizationTraceStep(step=name, result=result, refs=refs, reason=reason)


def build_predicate_normalization_traces(
    predicates: tuple[PredicateFeature, ...],
) -> tuple[NormalizationTrace, ...]:
    traces: list[NormalizationTrace] = []
    for index, predicate in enumerate(predicates):
        steps: list[NormalizationTraceStep] = [
            _step("collect_predicate_head", predicate.main_lemma, (predicate.main,)),
        ]
        aux_refs = tuple(aux.ref for aux in predicate.auxiliaries)
        if aux_refs:
            steps.append(_step("collect_auxiliaries", "found", aux_refs))
        else:
            steps.append(_step("collect_auxiliaries", "none", ()))
        if predicate.negation is not None:
            steps.append(_step("detect_negation", "present", (predicate.negation,)))
        else:
            steps.append(_step("detect_negation", "absent", ()))
        steps.append(
            _step(
                "detect_finite",
                "finite" if predicate.finite else "non_finite",
                (predicate.main,),
            )
        )
        steps.append(_step("detect_tense", predicate.tense or "unknown", (predicate.main,)))
        steps.append(_step("detect_aspect", predicate.aspect or "unknown", (predicate.main,)))
        steps.append(_step("detect_voice", predicate.voice or "unknown", (predicate.main,)))
        if predicate.modality is not None:
            steps.append(
                _step(
                    "detect_modality",
                    predicate.modality.modal_type or "unknown",
                    (predicate.main,),
                )
            )
        else:
            steps.append(_step("detect_modality", "none", ()))

        form_signature = predicate.form_signature or "unknown"
        if form_signature == "unknown":
            steps.append(
                _step(
                    "assign_form_signature",
                    "unknown",
                    (predicate.main,),
                    reason="form_signature_not_registered_for_combination",
                )
            )
        else:
            steps.append(
                _step(
                    "assign_form_signature",
                    form_signature,
                    (predicate.main,),
                )
            )

        traces.append(
            NormalizationTrace(
                trace_id=f"trace.predicate.{index}",
                target_group="predicate",
                steps=tuple(steps),
                target_feature_id=predicate.id,
                nearest_known_signatures=(),
            )
        )
    return tuple(traces)


__all__ = ["build_predicate_normalization_traces"]
