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
        if args.output and args.output_dir:
            raise ConfigurationError(
                "--output and --output-dir are mutually exclusive."
            )
        page_number = _positive_int(args.page, "--page")
        page_size = _positive_int(args.page_size, "--page-size")
        paging = PagingConfig(page_number=page_number, page_size=page_size)
        config = ExtractorConfig(
            include_diagnostics=True,
            include_evidence=not args.no_evidence,
            enable_heuristics=not args.no_heuristics,
            debug=args.debug,
        )
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
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=parent,
        delete=False,
    ) as tmp:
        tmp.write(payload)
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
    diagnostics_collected: list[dict[str, object]] = []
    for page_number in range(1, page_count + 1):
        paging = PagingConfig(page_number=page_number, page_size=page_size)
        page = extractor.extract_page(document, paging, config)
        payload = dumps_page(page)
        file_name = f"grammar_features.page_{page_number:05d}.json"
        target = out_path / file_name
        _atomic_write_text(target, payload)
        sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        pages_manifest.append(
            {
                "page_number": page_number,
                "file_name": file_name,
                "sentence_start": page.page.sentence_start,
                "sentence_end_exclusive": page.page.sentence_end_exclusive,
                "sha256": sha256,
            }
        )
        for diagnostic in _diagnostics_in_page(page):
            diagnostics_collected.append(diagnostic)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": "grammar_feature_manifest",
        "runtime_metadata": contract_runtime_metadata(),
        "page_size": page_size,
        "page_count": page_count,
        "total_sentences": total_sentences,
        "pages": pages_manifest,
        "diagnostics": diagnostics_collected,
    }
    manifest_payload = (
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    _atomic_write_text(out_path / "grammar_features.manifest.json", manifest_payload)
    validate_manifest_semantics(manifest, out_path)


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
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=parent,
        delete=False,
    ) as tmp:
        tmp.write(payload)
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
