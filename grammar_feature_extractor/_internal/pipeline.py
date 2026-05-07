from __future__ import annotations

from grammar_feature_extractor._internal.core import extract_core, paginate
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

    def stage_fingerprint(
        self,
        config: ExtractorConfig | None = None,
        input_artifact_hashes: tuple[str, ...] = (),
    ) -> str:
        """Return the reusable-stage fingerprint for the current runtime."""
        resolved_config = config or ExtractorConfig()
        validate_extractor_config(resolved_config)
        metadata = self.runtime_metadata()
        stage = metadata.stages["grammar_feature_extraction"]
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
