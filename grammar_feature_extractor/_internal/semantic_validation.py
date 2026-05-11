from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, NoReturn

from grammar_feature_extractor._internal.diagnostic_registry import (
    diagnostic_specs,
)
from grammar_feature_extractor._internal.errors import (
    ConfigurationError,
    FeatureExtractionError,
    InputValidationError,
)
from grammar_feature_extractor._internal.models import (
    AnnotatedDocument,
    AnnotatedSentence,
    ConstructionFeature,
    FeatureDiagnostic,
)
from grammar_feature_extractor._internal.semantic_validation_registry import (
    SemanticValidationSpec,
    entry as _registry_entry,
)

_EXCEPTION_CLASSES: dict[str, type[Exception]] = {
    "InputValidationError": InputValidationError,
    "ConfigurationError": ConfigurationError,
    "FeatureExtractionError": FeatureExtractionError,
}


def _raise(code: str, **details: Any) -> NoReturn:
    """Raise the registry-mapped exception for a semantic-validation code.

    Looks up `code` in the v5 semantic_validation registry, asserts that
    all `required_details` keys are supplied, formats the message from
    `message_template`, and raises the registry-declared exception with
    a `details` attribute populated from kwargs.
    """
    spec = _registry_entry(code)
    if spec is None:
        raise AssertionError(
            f"semantic_validation: code {code!r} is not in the v5 registry."
        )
    missing = [key for key in spec.required_details if key not in details]
    if missing:
        raise AssertionError(
            f"semantic_validation: code {code!r} requires details "
            f"{sorted(spec.required_details)} but missing {sorted(missing)}."
        )
    exception_class = _EXCEPTION_CLASSES.get(spec.exception)
    if exception_class is None:
        raise AssertionError(
            f"semantic_validation: unknown exception {spec.exception!r} "
            f"for code {code!r}."
        )
    message = _format_message(spec, details)
    error = exception_class(message)
    setattr(error, "details", details)
    setattr(error, "code", code)
    raise error


def _format_message(spec: SemanticValidationSpec, details: dict[str, Any]) -> str:
    try:
        return spec.message_template.format(
            affected_entity=spec.affected_entity, **details
        )
    except (KeyError, IndexError):
        return f"{spec.code}: semantic validation failed for {spec.affected_entity}."


def validate_annotated_document_semantics(document: AnnotatedDocument) -> None:
    for sentence_index, sentence in enumerate(document.sentences):
        words = sentence.words
        for word_index, word in enumerate(words, start=1):
            if word.head < 0 or word.head > len(words):
                _raise(
                    "head_out_of_range",
                    sentence_index=sentence_index,
                    word_index=word_index,
                    head=word.head,
                )
        roots = [
            index
            for index, word in enumerate(words, start=1)
            if word.head == 0
        ]
        if not roots:
            _raise("missing_dependency_root", sentence_index=sentence_index)
        _validate_dependency_graph(sentence_index, sentence)


def validate_resolved_config_semantics(page_size: int, max_page_size: int) -> None:
    if page_size > max_page_size:
        _raise(
            "page_size_exceeds_max_page_size",
            page_size=page_size,
            max_page_size=max_page_size,
        )


def validate_diagnostic_against_registry(diagnostic: FeatureDiagnostic) -> None:
    spec = diagnostic_specs().get(diagnostic.code)
    if spec is None:
        _raise(
            "diagnostic_severity_mismatch",
            reason=f"unknown diagnostic code: {diagnostic.code!r}",
        )
    if diagnostic.severity != spec.severity:
        _raise(
            "diagnostic_severity_mismatch",
            reason=(
                f"diagnostic {diagnostic.code!r} severity {diagnostic.severity!r}"
                f" does not match registry severity {spec.severity!r}"
            ),
        )
    if spec.feature_path_required and not diagnostic.feature_path:
        _raise(
            "diagnostic_feature_path_missing",
            reason=f"diagnostic {diagnostic.code!r} requires feature_path",
        )


def validate_construction_against_registry(feature: ConstructionFeature) -> None:
    from grammar_feature_extractor._internal.construction_registry import (
        signature_specs,
    )

    spec = signature_specs().get(feature.signature)
    if spec is None:
        _raise(
            "construction_slot_unknown",
            reason=f"unknown construction signature: {feature.signature!r}",
        )
    declared_slots = {slot.name: slot for slot in spec.slots}
    for required in (slot for slot in spec.slots if slot.required):
        if required.name not in feature.slots:
            _raise(
                "construction_slot_missing",
                reason=(
                    f"construction {feature.signature!r} missing required slot "
                    f"{required.name!r}"
                ),
            )
    for slot_name, value in feature.slots.items():
        if slot_name not in declared_slots:
            _raise(
                "construction_slot_unknown",
                reason=(
                    f"construction {feature.signature!r} has unknown slot "
                    f"{slot_name!r}"
                ),
            )
        if not _slot_value_matches_type(value, declared_slots[slot_name].value_type):
            _raise(
                "construction_slot_type_mismatch",
                reason=(
                    f"construction {feature.signature!r} slot {slot_name!r} "
                    f"value type does not match {declared_slots[slot_name].value_type!r}"
                ),
            )


def _slot_value_matches_type(value: object, value_type: str) -> bool:
    if value_type == "word_ref":
        return isinstance(value, int) and not isinstance(value, bool)
    if value_type == "word_ref_array":
        return isinstance(value, tuple) and all(
            isinstance(item, int) and not isinstance(item, bool) for item in value
        )
    if value_type == "string":
        return isinstance(value, str)
    if value_type == "boolean":
        return isinstance(value, bool)
    if value_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def validate_manifest_semantics(manifest: dict[str, object], output_dir: Path) -> None:
    pages = manifest.get("pages")
    if not isinstance(pages, list):
        _raise("manifest_page_gap", reason="manifest pages must be a list")
    page_count = manifest.get("page_count")
    total_sentences = manifest.get("total_sentences")
    if page_count != len(pages):
        _raise(
            "manifest_page_gap",
            reason="manifest page_count does not match pages length",
        )
    if not isinstance(total_sentences, int):
        _raise(
            "manifest_page_gap",
            reason="manifest total_sentences must be an integer",
        )

    expected_start = 0
    for index, page in enumerate(pages, start=1):
        if not isinstance(page, dict):
            _raise("manifest_page_gap", reason="manifest page entry must be an object")
        if page.get("page_number") != index:
            _raise(
                "manifest_page_overlap",
                reason="manifest pages must be sorted by page_number",
            )
        if page.get("sentence_start") != expected_start:
            _raise(
                "manifest_page_gap",
                reason="manifest page ranges must be gap-free",
            )
        sentence_end = page.get("sentence_end_exclusive")
        if not isinstance(sentence_end, int):
            _raise(
                "manifest_page_gap",
                reason="manifest sentence_end_exclusive must be an integer",
            )
        if sentence_end < expected_start:
            _raise(
                "manifest_page_overlap",
                reason="manifest sentence_end_exclusive must be >= sentence_start",
            )
        file_name = page.get("file_name")
        if not isinstance(file_name, str):
            _raise(
                "manifest_page_gap", reason="manifest file_name must be a string"
            )
        payload = (output_dir / file_name).read_text(encoding="utf-8")
        sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if page.get("sha256") != sha256:
            _raise(
                "manifest_hash_mismatch",
                reason=f"manifest page {file_name!r} sha256 does not match file contents",
            )
        expected_start = sentence_end

    if pages and expected_start != total_sentences:
        _raise(
            "manifest_page_gap",
            reason="manifest last page range does not match total_sentences",
        )


def validate_runtime_metadata_payload(metadata: dict[str, object]) -> None:
    resources = metadata.get("resources")
    if not isinstance(resources, list):
        raise ValueError("Runtime metadata resources must be a list.")
    seen: set[tuple[str, str]] = set()
    for resource in resources:
        if not isinstance(resource, dict):
            raise ValueError("Runtime resource must be an object.")
        kind = resource.get("kind")
        name = resource.get("name")
        version = resource.get("version")
        sha256 = resource.get("sha256")
        required = resource.get("required")
        if (
            not isinstance(kind, str)
            or not isinstance(name, str)
            or not isinstance(version, str)
        ):
            raise ValueError("Runtime resource identity fields must be strings.")
        if not isinstance(required, bool):
            raise ValueError("Runtime resource required must be boolean.")
        if sha256 is not None:
            if (
                not isinstance(sha256, str)
                or len(sha256) != 64
                or any(ch not in "0123456789abcdef" for ch in sha256)
            ):
                raise ValueError(
                    "Runtime resource sha256 must be lowercase 64-char hex."
                )
        key = (kind, name)
        if key in seen:
            raise ValueError("Runtime resources must be unique by (kind, name).")
        seen.add(key)


def _validate_dependency_graph(
    sentence_index: int,
    sentence: AnnotatedSentence,
) -> None:
    words = sentence.words
    for start in range(1, len(words) + 1):
        seen: list[int] = []
        seen_set: set[int] = set()
        current = start
        while current != 0:
            if current in seen_set:
                cycle_refs = tuple(seen[seen.index(current):])
                _raise(
                    "dependency_cycle",
                    sentence_index=sentence_index,
                    cycle_refs=cycle_refs,
                )
            seen.append(current)
            seen_set.add(current)
            current = words[current - 1].head
