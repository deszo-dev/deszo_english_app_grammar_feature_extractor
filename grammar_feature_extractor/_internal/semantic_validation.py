from __future__ import annotations

import hashlib
from pathlib import Path

from grammar_feature_extractor._internal.errors import (
    ConfigurationError,
    InputValidationError,
)
from grammar_feature_extractor._internal.models import (
    AnnotatedDocument,
    AnnotatedSentence,
    ConstructionFeature,
    FeatureDiagnostic,
)


def validate_annotated_document_semantics(document: AnnotatedDocument) -> None:
    for sentence_index, sentence in enumerate(document.sentences):
        roots = [
            index
            for index, word in enumerate(sentence.words, start=1)
            if word.head == 0
        ]
        if not roots:
            raise InputValidationError(
                f"sentences[{sentence_index}] is missing dependency root."
            )
        _validate_dependency_graph(sentence_index, sentence)


def validate_resolved_config_semantics(page_size: int, max_page_size: int) -> None:
    if page_size > max_page_size:
        raise ConfigurationError("page_size exceeds max_page_size.")


def validate_diagnostic_against_registry(diagnostic: FeatureDiagnostic) -> None:
    if diagnostic.message == "":
        raise ValueError("Diagnostic message must be non-empty.")


def validate_construction_against_registry(feature: ConstructionFeature) -> None:
    if feature.signature == "":
        raise ValueError("Construction signature must be non-empty.")


def validate_manifest_semantics(manifest: dict[str, object], output_dir: Path) -> None:
    pages = manifest.get("pages")
    if not isinstance(pages, list):
        raise ValueError("Manifest pages must be a list.")
    page_count = manifest.get("page_count")
    total_sentences = manifest.get("total_sentences")
    if page_count != len(pages):
        raise ValueError("Manifest page_count does not match pages length.")
    if not isinstance(total_sentences, int):
        raise ValueError("Manifest total_sentences must be an integer.")

    expected_start = 0
    for index, page in enumerate(pages, start=1):
        if not isinstance(page, dict):
            raise ValueError("Manifest page entry must be an object.")
        if page.get("page_number") != index:
            raise ValueError("Manifest pages must be sorted by page_number.")
        if page.get("sentence_start") != expected_start:
            raise ValueError("Manifest page ranges must be gap-free.")
        sentence_end = page.get("sentence_end_exclusive")
        if not isinstance(sentence_end, int):
            raise ValueError("Manifest sentence_end_exclusive must be an integer.")
        file_name = page.get("file_name")
        if not isinstance(file_name, str):
            raise ValueError("Manifest file_name must be a string.")
        page_bytes = (output_dir / file_name).read_bytes()
        if b"\r\n" in page_bytes:
            raise ValueError(
                f"Page file {file_name} contains CRLF line endings; "
                "canonical pages must use LF only."
            )
        sha256 = hashlib.sha256(page_bytes).hexdigest()
        if page.get("sha256") != sha256:
            raise ValueError("Manifest page sha256 does not match file contents.")
        expected_start = sentence_end

    if pages and expected_start != total_sentences:
        raise ValueError("Manifest last page range does not match total_sentences.")

    _validate_manifest_diagnostics(manifest)


def _validate_manifest_diagnostics(
    manifest: dict[str, object],
) -> None:
    diagnostics = manifest.get("diagnostics")
    if not isinstance(diagnostics, list):
        raise ValueError("Manifest diagnostics must be a list.")


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
        seen: set[int] = set()
        current = start
        while current != 0:
            if current in seen:
                raise InputValidationError(
                    f"sentences[{sentence_index}] contains dependency cycle."
                )
            seen.add(current)
            current = words[current - 1].head
