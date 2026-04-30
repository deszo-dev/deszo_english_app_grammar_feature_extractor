from __future__ import annotations

import argparse
import logging
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
from grammar_feature_extractor._internal.models import ExtractorConfig, PagingConfig
from grammar_feature_extractor._internal.pipeline import GrammarFeatureExtractor
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


def _positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer >= 1.") from exc
    if parsed < 1:
        raise ConfigurationError(f"{name} must be an integer >= 1.")
    return parsed
