from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

from grammar_feature_extractor._internal.errors import (
    ConfigurationError,
    FeatureExtractionError,
    InputValidationError,
    SerializationError,
)
from grammar_feature_extractor._internal.models import (
    SCHEMA_VERSION,
    AnnotatedDocument,
    ExtractorConfig,
    GrammarFeaturePage,
    PagingConfig,
)
from grammar_feature_extractor._internal.pipeline import GrammarFeatureExtractor
from grammar_feature_extractor._internal.runtime_metadata import (
    contract_runtime_metadata,
)
from grammar_feature_extractor._internal.schema_validation_report import (
    write_schema_validation_report,
)
from grammar_feature_extractor._internal.semantic_validation import (
    validate_manifest_semantics,
)
from grammar_feature_extractor._internal.serialization import dumps_page, loads_document


class _CliUsageError(Exception):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise _CliUsageError(message)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        if args.input and args.input_dir:
            raise ConfigurationError("--input and --input-dir are mutually exclusive.")
        if args.output and args.output_dir:
            raise ConfigurationError(
                "--output and --output-dir are mutually exclusive."
            )
        if args.input_dir and args.output:
            raise ConfigurationError("--output cannot be used with --input-dir.")
        if args.input_dir and not args.output_dir:
            raise ConfigurationError("--input-dir requires --output-dir.")
        page_number = _positive_int(args.page, "--page")
        page_size = _positive_int(args.page_size, "--page-size")
        paging = PagingConfig(page_number=page_number, page_size=page_size)
        config = ExtractorConfig(
            include_diagnostics=True,
            include_evidence=not args.no_evidence,
            enable_heuristics=not args.no_heuristics,
            debug=args.debug,
        )
        if args.input_dir:
            _write_batch_output_dir(
                args.input_dir,
                page_size,
                config,
                args.output_dir,
                args.overwrite,
            )
            return 0
        payload = _read_input(args.input)
        document = loads_document(payload)
        if args.output_dir:
            _write_output_dir(
                document,
                page_size,
                config,
                args.output_dir,
                hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                args.overwrite,
            )
        else:
            page = GrammarFeatureExtractor().extract_page(document, paging, config)
            output = dumps_page(page)
            _write_output(args.output, output)
        return 0
    except _CliUsageError as exc:
        _emit_cli_error("cli_usage_error", str(exc))
        return 2
    except SerializationError as exc:
        _emit_cli_error("input_json_serialization_error", str(exc))
        return 1
    except InputValidationError as exc:
        _emit_cli_error("input_validation_error", str(exc))
        return 1
    except ConfigurationError as exc:
        _emit_cli_error("configuration_error", str(exc))
        return 1
    except ValueError as exc:
        _emit_cli_error("input_json_serialization_error", str(exc))
        return 1
    except FeatureExtractionError as exc:
        _emit_cli_error("unexpected_system_error", str(exc))
        return 4
    except OSError as exc:
        _emit_cli_error("output_write_error", str(exc))
        return 3
    except Exception as exc:  # noqa: BLE001
        _emit_cli_error("unexpected_system_error", str(exc))
        return 4


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="grammar-feature-extractor", add_help=True)
    parser.add_argument(
        "--input",
        default=None,
        help="AnnotatedDocument JSON input file.",
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help=(
            "Batch mode: directory of stanza_annotator_document JSON files. "
            "Requires --output-dir."
        ),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="GrammarFeaturePage JSON output file.",
    )
    parser.add_argument("--page", default="1", help="1-based page number.")
    parser.add_argument(
        "--page-size",
        default="300",
        help="Number of sentences per page.",
    )
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug logs.")
    parser.add_argument(
        "--no-evidence",
        action="store_true",
        help="Omit serialized evidence arrays for compact output.",
    )
    parser.add_argument(
        "--no-heuristics",
        action="store_true",
        help="Disable heuristic-only feature extraction.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Production mode: write all GrammarFeaturePage files plus a "
            "manifest into this directory. Mutually exclusive with --output."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow writing into a non-empty --output-dir.",
    )
    return parser


def _read_input(path: str | None) -> str:
    if path is None:
        return sys.stdin.read()
    input_path = Path(path)
    if input_path.is_symlink() or not input_path.is_file():
        raise OSError("--input must be a regular file.")
    return input_path.read_text(encoding="utf-8")


def _input_files_from_dir(path: str) -> list[Path]:
    input_dir = Path(path)
    if input_dir.is_symlink() or not input_dir.is_dir():
        raise OSError("--input-dir must be a directory.")
    files = sorted(
        candidate
        for candidate in input_dir.iterdir()
        if candidate.is_file()
        and not candidate.is_symlink()
        and candidate.suffix.casefold() == ".json"
    )
    if not files:
        raise OSError("--input-dir must contain at least one .json file.")
    return files


def _write_output(path: str | None, payload: str) -> None:
    if path is None:
        sys.stdout.write(payload)
        sys.stdout.flush()
        return
    output_path = Path(path)
    if output_path.is_symlink():
        raise OSError("Symlink output targets are rejected.")
    if output_path.exists() and output_path.is_dir():
        raise OSError("--output must not be a directory.")
    parent = output_path.parent if output_path.parent != Path("") else Path(".")
    payload_bytes = payload.encode("utf-8")
    with tempfile.NamedTemporaryFile(
        "wb",
        dir=parent,
        delete=False,
    ) as tmp:
        tmp.write(payload_bytes)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    try:
        os.replace(tmp_path, output_path)
    except OSError:
        try:
            tmp_path.unlink(missing_ok=True)
        finally:
            raise


def _write_output_dir(
    document: AnnotatedDocument,
    page_size: int,
    config: ExtractorConfig,
    output_dir: str,
    input_sha256: str,
    overwrite: bool,
) -> None:
    out_path = Path(output_dir)
    if out_path.is_symlink():
        raise OSError("Symlink output targets are rejected.")
    if out_path.exists() and not out_path.is_dir():
        raise OSError("--output-dir must be a directory path.")
    out_path.mkdir(parents=True, exist_ok=True)
    if not overwrite and any(out_path.iterdir()):
        raise OSError("--output-dir must be empty unless --overwrite is set.")
    extractor = GrammarFeatureExtractor()
    total_sentences = len(document.sentences)
    page_count = (
        max(1, math.ceil(total_sentences / page_size)) if total_sentences else 1
    )
    pages_manifest: list[dict[str, object]] = []
    for page_number in range(1, page_count + 1):
        paging = PagingConfig(page_number=page_number, page_size=page_size)
        page = extractor.extract_page(document, paging, config)
        payload = dumps_page(page)
        file_name = f"grammar_features.page_{page_number:05d}.json"
        target = out_path / file_name
        _atomic_write_text(target, payload)
        sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        on_disk_sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
        if on_disk_sha256 != sha256:
            raise SerializationError(
                "Canonical page bytes on disk diverge from payload hash "
                f"({file_name}); aborting to avoid manifest mismatch."
            )
        pages_manifest.append(
            {
                "page_number": page_number,
                "file_name": file_name,
                "sentence_start": page.page.sentence_start,
                "sentence_end_exclusive": page.page.sentence_end_exclusive,
                "sha256": sha256,
            }
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": "grammar_feature_manifest",
        "runtime_metadata": contract_runtime_metadata(),
        "page_size": page_size,
        "page_count": page_count,
        "total_sentences": total_sentences,
        "pages": pages_manifest,
        "diagnostics": _manifest_diagnostics(document),
    }
    manifest_payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    _atomic_write_text(out_path / "grammar_features.manifest.json", manifest_payload)
    validate_manifest_semantics(manifest, out_path)
    write_schema_validation_report(out_path)


def _manifest_diagnostics(document: AnnotatedDocument) -> list[dict[str, object]]:
    lineage = document.input_lineage
    if lineage.source_status in {"succeeded", "completed", "success"}:
        return []
    selected = lineage.selected_unit_count
    sentences_present = len(document.sentences)
    # Hardened partial-upstream rollup: split exact (from lineage) from
    # inferred (heuristic). Hard requirement: nothing in `exact` may be a
    # heuristic estimate.
    details: dict[str, object] = {
        "source_status": lineage.source_status,
        "exact": {
            "processed_unit_count": selected,
            "processed_sentence_count": sentences_present,
        },
        "estimated": {
            "skipped_unit_count": 0,
            "unsafe_unit_count": 0,
            "failed_unit_count": 0,
            "skipped_reasons": {},
        },
        "estimation_basis": "selected_unit_count_only",
    }
    return [
        {
            "severity": "warning",
            "code": "partial_upstream_input",
            "message": (
                "Input lineage reports partial upstream status; manifest exposes "
                "exact and estimated unit rollups for downstream risk "
                "quantification."
            ),
            "refs": [],
            "feature_path": "input_lineage.source_status",
            "details": details,
        }
    ]


def _write_batch_output_dir(
    input_dir: str,
    page_size: int,
    config: ExtractorConfig,
    output_dir: str,
    overwrite: bool,
) -> None:
    input_files = _input_files_from_dir(input_dir)
    out_path = Path(output_dir)
    if out_path.is_symlink():
        raise OSError("Symlink output targets are rejected.")
    if out_path.exists() and not out_path.is_dir():
        raise OSError("--output-dir must be a directory path.")
    out_path.mkdir(parents=True, exist_ok=True)
    if not overwrite and any(out_path.iterdir()):
        raise OSError("--output-dir must be empty unless --overwrite is set.")

    inputs_manifest: list[dict[str, object]] = []
    used_names: set[str] = set()
    for input_file in input_files:
        payload = input_file.read_text(encoding="utf-8")
        document = loads_document(payload)
        input_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        subdir_name = _unique_batch_subdir_name(input_file.stem, used_names)
        target_dir = out_path / subdir_name
        _write_output_dir(
            document,
            page_size,
            config,
            str(target_dir),
            input_sha256,
            overwrite,
        )
        manifest_path = target_dir / "grammar_features.manifest.json"
        child_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        inputs_manifest.append(
            {
                "input_file": input_file.name,
                "output_dir": subdir_name,
                "manifest_file": f"{subdir_name}/grammar_features.manifest.json",
                "input_sha256": input_sha256,
                "page_count": child_manifest["page_count"],
                "total_sentences": child_manifest["total_sentences"],
            }
        )

    batch_manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": "grammar_feature_batch_manifest",
        "runtime_metadata": contract_runtime_metadata(),
        "input_dir": str(Path(input_dir)),
        "output_dir": str(out_path),
        "input_count": len(inputs_manifest),
        "page_size": page_size,
        "inputs": inputs_manifest,
    }
    batch_payload = json.dumps(batch_manifest, ensure_ascii=False, indent=2) + "\n"
    _atomic_write_text(out_path / "grammar_features.batch_manifest.json", batch_payload)


def _unique_batch_subdir_name(stem: str, used_names: set[str]) -> str:
    safe = "".join(
        char if char.isalnum() or char in {"-", "_", "."} else "_"
        for char in stem.strip()
    ).strip("._")
    if not safe:
        safe = "input"
    candidate = safe
    index = 2
    while candidate in used_names:
        candidate = f"{safe}_{index}"
        index += 1
    used_names.add(candidate)
    return candidate


def _diagnostics_in_page(page: GrammarFeaturePage) -> list[dict[str, object]]:
    collected: list[dict[str, object]] = []
    for sentence in page.features:
        for diagnostic in sentence.features.diagnostics:
            entry: dict[str, object] = {
                "severity": diagnostic.severity,
                "code": diagnostic.code,
                "message": diagnostic.message,
                "refs": list(diagnostic.refs),
                "sentence_index": sentence.sentence_index,
            }
            if diagnostic.feature_path is not None:
                entry["feature_path"] = diagnostic.feature_path
            collected.append(entry)
    return collected


def _atomic_write_text(target: Path, payload: str) -> None:
    if target.is_symlink():
        raise OSError("Symlink output targets are rejected.")
    parent = target.parent if target.parent != Path("") else Path(".")
    parent.mkdir(parents=True, exist_ok=True)
    payload_bytes = payload.encode("utf-8")
    with tempfile.NamedTemporaryFile(
        "wb",
        dir=parent,
        delete=False,
    ) as tmp:
        tmp.write(payload_bytes)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    try:
        os.replace(tmp_path, target)
    except OSError:
        try:
            tmp_path.unlink(missing_ok=True)
        finally:
            raise


def _positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer >= 1.") from exc
    if parsed < 1:
        raise ConfigurationError(f"{name} must be an integer >= 1.")
    return parsed


def _emit_cli_error(error_code: str, message: str) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "kind": "cli_error",
        "error_code": error_code,
        "message": message,
    }
    sys.stderr.write(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
