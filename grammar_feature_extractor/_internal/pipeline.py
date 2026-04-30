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
from grammar_feature_extractor._internal.validation import (
    assert_valid_feature_refs,
    validate_extractor_config,
    validate_paging_config,
)


class GrammarFeatureExtractor:
    """Extract deterministic grammar features from an AnnotatedDocument."""

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
