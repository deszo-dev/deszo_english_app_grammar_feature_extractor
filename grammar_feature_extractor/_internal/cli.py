from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import sys
import tempfile
from pathlib import Path

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
from grammar_feature_extractor._internal.runtime_metadata import metadata_to_dict
from grammar_feature_extractor._internal.serialization import dumps_page, loads_document


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        stream=sys.stderr,
        format="%(levelname)s:%(message)s",
    )
    logger = logging.getLogger("grammar_feature_extractor")
    try:
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
        logger.info("pipeline start")
        logger.info("input read start")
        payload = _read_input(args.input)
        logger.info("input read end")
        logger.info("input validation start")
        document = loads_document(payload)
        logger.info("input validation end")
        if args.output_dir:
            logger.info("output-dir mode start")
            _write_output_dir(
                document,
                page_size,
                config,
                args.output_dir,
                hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                logger,
            )
            logger.info("output-dir mode end")
        else:
            logger.info("extraction start")
            page = GrammarFeatureExtractor().extract_page(document, paging, config)
            logger.info("extraction end")
            logger.info("serialization start")
            output = dumps_page(page)
            logger.info("serialization end")
            logger.info("output write start")
            _write_output(args.output, output)
            logger.info("output write end")
        logger.info("pipeline end")
        return 0
    except (InputValidationError, ConfigurationError, SerializationError) as exc:
        logger.error("%s", exc)
        return 1
    except FeatureExtractionError as exc:
        logger.error("%s", exc)
        return 2
    except OSError as exc:
        logger.error("System error while reading or writing files.")
        if args.debug:
            logger.debug("System exception detail", exc_info=exc)
        return 2
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected system error.")
        if args.debug:
            logger.debug("Unexpected exception detail", exc_info=exc)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="grammar-feature-extractor")
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
    return parser


def _read_input(path: str | None) -> str:
    if path is None:
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _write_output(path: str | None, payload: str) -> None:
    if path is None:
        sys.stdout.write(payload)
        sys.stdout.flush()
        return
    output_path = Path(path)
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
    logger: logging.Logger,
) -> None:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    extractor = GrammarFeatureExtractor()
    total_sentences = len(document.sentences)
    page_count = (
        max(1, math.ceil(total_sentences / page_size)) if total_sentences else 1
    )
    pages_manifest: list[dict[str, object]] = []
    diagnostics_collected: list[dict[str, object]] = []
    for page_number in range(1, page_count + 1):
        paging = PagingConfig(page_number=page_number, page_size=page_size)
        logger.info("page %d extraction start", page_number)
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
        logger.info("page %d extraction end", page_number)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": "grammar_feature_manifest",
        "page_size": page_size,
        "page_count": page_count,
        "total_sentences": total_sentences,
        "pages": pages_manifest,
        "diagnostics": diagnostics_collected,
        "runtime_metadata": metadata_to_dict(extractor.runtime_metadata()),
        "stage_fingerprints": {
            "grammar_feature_extraction": extractor.stage_fingerprint(
                config,
                input_artifact_hashes=(input_sha256,),
            )
        },
    }
    manifest_payload = (
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    _atomic_write_text(out_path / "grammar_features.manifest.json", manifest_payload)


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
