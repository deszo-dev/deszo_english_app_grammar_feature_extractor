from __future__ import annotations

import math

from grammar_feature_extractor._internal.core import extract_core, paginate
from grammar_feature_extractor._internal.errors import (
    ConfigurationError,
    FeatureExtractionError,
)
from grammar_feature_extractor._internal.models import (
    AnnotatedDocument,
    ExtractorConfig,
    GrammarFeatureDocument,
    GrammarFeaturePage,
    PagingConfig,
)
from grammar_feature_extractor._internal.proof_surface_validator import (
    validate_proof_surface,
)
from grammar_feature_extractor._internal.runtime_metadata import (
    PipelineRuntimeMetadata,
    StageRuntimeMetadata,
    build_stage_runtime_metadata,
    extractor_config_to_fingerprint_payload,
    grammar_feature_extractor_runtime_metadata,
    stage_fingerprint,
)
from grammar_feature_extractor._internal.validation import (
    assert_valid_feature_refs,
    validate_extractor_config,
    validate_paging_config,
)


class GrammarFeatureExtractor:
    """Extract deterministic grammar features from an AnnotatedDocument."""

    def runtime_metadata(self) -> PipelineRuntimeMetadata:
        """Return deterministic runtime metadata for orchestration reuse checks."""
        return grammar_feature_extractor_runtime_metadata()

    def get_runtime_metadata(self) -> StageRuntimeMetadata:
        """Return the v5 stage runtime metadata for this extractor."""
        return build_stage_runtime_metadata()

    def stage_fingerprint(
        self,
        config: ExtractorConfig | None = None,
        input_artifact_hashes: tuple[str, ...] = (),
    ) -> str:
        """Return the reusable-stage fingerprint for the current runtime."""
        resolved_config = config or ExtractorConfig()
        validate_extractor_config(resolved_config)
        metadata = self.runtime_metadata()
        stage = next(iter(metadata.stages.values()))
        return stage_fingerprint(
            stage,
            pipeline_contract_version=metadata.pipeline_contract_version,
            normalized_stage_config=extractor_config_to_fingerprint_payload(
                resolved_config
            ),
            input_artifact_hashes=input_artifact_hashes,
        )

    def extract(
        self,
        document: AnnotatedDocument,
        config: ExtractorConfig | None = None,
    ) -> GrammarFeatureDocument:
        """Extract deterministic grammar features from an AnnotatedDocument."""
        resolved_config = config or ExtractorConfig()
        validate_extractor_config(resolved_config)
        result = extract_core(document, resolved_config)
        for index, sentence in enumerate(document.sentences):
            assert_valid_feature_refs(sentence, result.sentences[index].features)
            validate_proof_surface(sentence, result.sentences[index].features)
        return result

    def extract_page(
        self,
        document: AnnotatedDocument,
        paging: PagingConfig | None = None,
        config: ExtractorConfig | None = None,
    ) -> GrammarFeaturePage:
        """Extract features and return a deterministic paginated page."""
        resolved_paging = paging or PagingConfig()
        validate_paging_config(resolved_paging)
        result = self.extract(document, config)
        return paginate(result, resolved_paging)

    def extract_pages(
        self,
        document: AnnotatedDocument,
        paging: PagingConfig | None = None,
        config: ExtractorConfig | None = None,
    ) -> list[GrammarFeaturePage]:
        """Return the complete deterministic page sequence for the whole document."""
        resolved_paging = paging or PagingConfig()
        if resolved_paging.page_number != 1:
            raise ConfigurationError(
                "extract_pages() requires paging.page_number == 1; "
                "it is an all-pages API."
            )
        validate_paging_config(resolved_paging)
        resolved_config = config or ExtractorConfig()
        result = self.extract(document, resolved_config)

        total_sentences = len(result.sentences)
        if total_sentences == 0:
            return [paginate(result, resolved_paging)]

        page_size = resolved_paging.page_size
        total_pages = max(1, math.ceil(total_sentences / page_size))
        if total_pages > resolved_config.limits.max_output_pages:
            raise FeatureExtractionError(
                "output_pages_exceeds_max_output_pages: "
                f"produced {total_pages} pages, limit is "
                f"{resolved_config.limits.max_output_pages}."
            )
        return [
            paginate(
                result,
                PagingConfig(page_number=page_number, page_size=page_size),
            )
            for page_number in range(1, total_pages + 1)
        ]
