from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Literal, TypeAlias, cast

from grammar_feature_extractor._internal.models import SCHEMA_VERSION, ExtractorConfig

CompatibilityMode: TypeAlias = Literal[
    "exact",
    "semver_compatible",
    "schema_compatible",
    "hash_exact",
]

STAGE_NAME = "grammar_feature_extractor"
STAGE_CONTRACT_VERSION = "grammar_feature_extractor.stage.v5"
OUTPUT_SCHEMA_VERSION = SCHEMA_VERSION
CONFIG_CONTRACT_VERSION = "grammar_feature_extractor.config.v5"
PIPELINE_NAME = "grammar_feature_extractor"
PIPELINE_CONTRACT_VERSION = "grammar_feature_extractor.pipeline.v5"
PACKAGE_DISTRIBUTION_NAME = "grammar-feature-extractor"


@dataclass(frozen=True, slots=True)
class RuntimeDependency:
    name: str
    version: str
    source: str
    compatibility: CompatibilityMode = "exact"
    source_fingerprint: str | None = None


@dataclass(frozen=True, slots=True)
class StageRuntimeAsset:
    name: str
    kind: str
    version: str
    sha256: str | None
    required: bool = True


RuntimeAsset = StageRuntimeAsset


@dataclass(frozen=True, slots=True)
class StageRuntimeMetadata:
    stage_name: str
    stage_contract_version: str
    output_schema_version: str
    config_contract_version: str
    module_version: str
    source_fingerprint: str
    dependencies: tuple[str, ...] = ()
    assets: tuple[StageRuntimeAsset, ...] = ()


@dataclass(frozen=True, slots=True)
class PipelineRuntimeMetadata:
    pipeline_name: str
    pipeline_version: str
    pipeline_contract_version: str
    stages: dict[str, StageRuntimeMetadata]


def grammar_feature_extractor_runtime_metadata() -> PipelineRuntimeMetadata:
    stage = build_stage_runtime_metadata()
    return PipelineRuntimeMetadata(
        pipeline_name=PIPELINE_NAME,
        pipeline_version=get_module_version(PACKAGE_DISTRIBUTION_NAME),
        pipeline_contract_version=PIPELINE_CONTRACT_VERSION,
        stages={stage.stage_name: stage},
    )


def build_stage_runtime_metadata() -> StageRuntimeMetadata:
    return StageRuntimeMetadata(
        stage_name=STAGE_NAME,
        stage_contract_version=STAGE_CONTRACT_VERSION,
        output_schema_version=OUTPUT_SCHEMA_VERSION,
        config_contract_version=CONFIG_CONTRACT_VERSION,
        module_version=get_module_version(PACKAGE_DISTRIBUTION_NAME),
        source_fingerprint=directory_source_fingerprint(package_source_root()),
        dependencies=(),
        assets=runtime_assets(),
    )


def runtime_assets() -> tuple[StageRuntimeAsset, ...]:
    root = repository_root()
    schema_root = root / "schema" / "grammar_feature_extractor.v5"
    if not schema_root.exists():
        return ()
    collected: list[StageRuntimeAsset] = []
    for path in sorted(schema_root.glob("*.v5.*")):
        if not path.is_file():
            continue
        kind = "registry" if "registry" in path.name else "schema"
        collected.append(
            StageRuntimeAsset(
                name=path.relative_to(root).as_posix(),
                kind=kind,
                version="v5",
                sha256=sha256_file(path),
                required=True,
            )
        )
    collected.sort(key=lambda asset: (asset.kind, asset.name, asset.version))
    return tuple(collected)


def stage_fingerprint(
    stage: StageRuntimeMetadata,
    *,
    pipeline_contract_version: str,
    normalized_stage_config: dict[str, object] | None = None,
    input_artifact_hashes: tuple[str, ...] = (),
) -> str:
    payload = {
        "stage_name": stage.stage_name,
        "stage_contract_version": stage.stage_contract_version,
        "output_schema_version": stage.output_schema_version,
        "config_contract_version": stage.config_contract_version,
        "normalized_stage_config": normalized_stage_config or {},
        "input_artifact_hashes": sorted(input_artifact_hashes),
        "module_version": stage.module_version,
        "source_fingerprint": stage.source_fingerprint,
        "dependencies": sorted(stage.dependencies),
        "assets": [_canonical_asset(asset) for asset in stage.assets],
        "pipeline_contract_version": pipeline_contract_version,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def extractor_config_to_fingerprint_payload(
    config: ExtractorConfig,
) -> dict[str, object]:
    return {
        "debug": config.debug,
        "enable_heuristics": config.enable_heuristics,
        "include_construction_signatures": config.include_construction_signatures,
        "include_contrastive_support": config.include_contrastive_support,
        "include_diagnostics": config.include_diagnostics,
        "include_evidence": config.include_evidence,
        "limits": {
            "max_input_bytes": config.limits.max_input_bytes,
            "max_sentences": config.limits.max_sentences,
            "max_words_per_sentence": config.limits.max_words_per_sentence,
            "max_total_words": config.limits.max_total_words,
            "max_page_size": config.limits.max_page_size,
            "max_output_page_bytes": config.limits.max_output_page_bytes,
            "max_output_pages": config.limits.max_output_pages,
            "max_diagnostics_per_sentence": config.limits.max_diagnostics_per_sentence,
        },
    }


def canonical_json(value: object) -> str:
    return json.dumps(
        _to_jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def metadata_to_dict(metadata: PipelineRuntimeMetadata) -> dict[str, object]:
    return cast(dict[str, object], _to_jsonable(metadata))


def contract_runtime_metadata() -> dict[str, object]:
    resources: list[dict[str, object]] = []
    schema_root = repository_root() / "schema" / "grammar_feature_extractor.v5"
    if schema_root.exists():
        for path in sorted(schema_root.glob("*.json")):
            kind = "registry" if "registry" in path.name else "schema"
            version = _detect_resource_version(path.name)
            resources.append(
                {
                    "name": path.name,
                    "kind": kind,
                    "version": version,
                    "sha256": sha256_file(path),
                    "required": True,
                }
            )
    resources.sort(key=lambda item: (str(item["kind"]), str(item["name"]), str(item["version"])))
    return {
        "schema_version": SCHEMA_VERSION,
        "extractor_version": get_module_version(PACKAGE_DISTRIBUTION_NAME),
        "resources": resources,
    }


def _detect_resource_version(filename: str) -> str:
    parts = filename.split(".")
    for token in parts:
        if len(token) >= 2 and token[0] == "v" and token[1:].isdigit():
            return token
    return "unknown"


def directory_source_fingerprint(root: Path) -> str:
    relevant_suffixes = {
        ".py",
        ".json",
        ".toml",
    }
    ignored_dirs = {
        "__pycache__",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".venv",
        "node_modules",
    }
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in relevant_suffixes:
            continue
        if any(part in ignored_dirs for part in path.relative_to(root).parts):
            continue
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"tree-sha256:{digest.hexdigest()}"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_module_version(distribution_name: str) -> str:
    try:
        return importlib_metadata.version(distribution_name)
    except importlib_metadata.PackageNotFoundError:
        pyproject = repository_root() / "pyproject.toml"
        return _version_from_pyproject(pyproject) or "unknown"


def _version_from_pyproject(path: Path) -> str | None:
    if not path.exists():
        return None
    in_project = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "[project]":
            in_project = True
            continue
        if line.startswith("[") and line.endswith("]"):
            in_project = False
        if in_project and line.startswith("version"):
            _, value = line.split("=", 1)
            return value.strip().strip('"')
    return None


def _canonical_dependency(dependency: RuntimeDependency) -> dict[str, object]:
    return {
        "compatibility": dependency.compatibility,
        "name": dependency.name,
        "source": dependency.source,
        "source_fingerprint": dependency.source_fingerprint,
        "version": dependency.version,
    }


def _canonical_asset(asset: StageRuntimeAsset) -> dict[str, object]:
    return {
        "kind": asset.kind,
        "name": asset.name,
        "required": asset.required,
        "sha256": asset.sha256,
        "version": asset.version,
    }


def _to_jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _to_jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value
