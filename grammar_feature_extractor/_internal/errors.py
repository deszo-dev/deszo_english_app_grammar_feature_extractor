class FeatureExtractionError(Exception):
    """Base exception for grammar_feature_extractor."""


class InputValidationError(FeatureExtractionError):
    """AnnotatedDocument input contract was violated."""


class ConfigurationError(FeatureExtractionError):
    """Extractor or paging configuration is invalid."""


class SerializationError(FeatureExtractionError):
    """Input or output JSON serialization failed."""
