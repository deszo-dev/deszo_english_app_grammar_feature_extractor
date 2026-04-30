from __future__ import annotations

from collections.abc import Mapping, Sequence

from grammar_feature_extractor._internal.errors import (
    ConfigurationError,
    InputValidationError,
)
from grammar_feature_extractor._internal.models import (
    MAX_PAGE_SIZE,
    AnnotatedDocument,
    AnnotatedSentence,
    AnnotatedToken,
    AnnotatedWord,
    Entity,
    ExtractorConfig,
    GrammarFeatureSet,
    PagingConfig,
    WordRef,
)


def parse_annotated_document(value: object) -> AnnotatedDocument:
    if not isinstance(value, Mapping):
        raise InputValidationError("Input must be an AnnotatedDocument object.")

    sentences_value = _required(value, "sentences")
    entities_value = _required(value, "entities")
    sentences = _sequence(sentences_value, "sentences")
    entities = _sequence(entities_value, "entities")

    parsed_sentences = tuple(
        _parse_sentence(item, f"sentences[{index}]")
        for index, item in enumerate(sentences)
    )
    parsed_entities = tuple(
        _parse_entity(item, f"entities[{index}]") for index, item in enumerate(entities)
    )
    return AnnotatedDocument(sentences=parsed_sentences, entities=parsed_entities)


def validate_paging_config(paging: PagingConfig) -> None:
    if isinstance(paging.page_number, bool) or paging.page_number < 1:
        raise ConfigurationError("page_number must be an integer >= 1.")
    if isinstance(paging.page_size, bool) or paging.page_size < 1:
        raise ConfigurationError("page_size must be an integer >= 1.")
    if paging.page_size > MAX_PAGE_SIZE:
        raise ConfigurationError(f"page_size must be <= {MAX_PAGE_SIZE}.")


def validate_extractor_config(config: ExtractorConfig) -> None:
    if not isinstance(config.include_diagnostics, bool):
        raise ConfigurationError("include_diagnostics must be a boolean.")
    if not isinstance(config.include_evidence, bool):
        raise ConfigurationError("include_evidence must be a boolean.")
    if not isinstance(config.include_construction_signatures, bool):
        raise ConfigurationError("include_construction_signatures must be a boolean.")
    if not isinstance(config.include_contrastive_support, bool):
        raise ConfigurationError("include_contrastive_support must be a boolean.")
    if not isinstance(config.enable_heuristics, bool):
        raise ConfigurationError("enable_heuristics must be a boolean.")
    if not isinstance(config.debug, bool):
        raise ConfigurationError("debug must be a boolean.")


def assert_valid_feature_refs(
    sentence: AnnotatedSentence,
    features: GrammarFeatureSet,
) -> None:
    max_ref = len(sentence.words)

    def check(ref: WordRef) -> None:
        if ref < 1 or ref > max_ref:
            raise AssertionError(f"Invalid WordRef {ref}; expected 1..{max_ref}.")

    for word in features.evidence.words:
        check(word.ref)
        if word.head != 0:
            check(word.head)
        for ref in word.children:
            check(ref)
    for dep in features.evidence.dependencies:
        if dep.governor != 0:
            check(dep.governor)
        check(dep.dependent)
    for word_morph in features.morphology.word_morphology:
        check(word_morph.ref)
    for normalized_morph in features.morphology.normalized:
        check(normalized_morph.ref)
    for phrase in features.syntax.phrases:
        check(phrase.head)
        for ref in phrase.tokens:
            check(ref)
    for clause in features.syntax.clauses:
        check(clause.head)
        if clause.subject is not None:
            check(clause.subject)
        if clause.predicate is not None:
            check(clause.predicate)
        if clause.marker is not None:
            check(clause.marker.marker_ref)
            check(clause.marker.clause_head)
        if clause.roles.subject is not None:
            check(clause.roles.subject)
        if clause.roles.object is not None:
            check(clause.roles.object)
        if clause.roles.indirect_object is not None:
            check(clause.roles.indirect_object)
        for ref in clause.roles.oblique:
            check(ref)
        for ref in clause.tokens:
            check(ref)
        for ref in clause.local_tokens:
            check(ref)
    for predicate in features.syntax.predicates:
        check(predicate.main)
        check(predicate.clause_head)
        for auxiliary in predicate.auxiliaries:
            check(auxiliary.ref)
        if predicate.copula is not None:
            check(predicate.copula)
        if predicate.negation is not None:
            check(predicate.negation)
        if predicate.modality is not None:
            for ref in predicate.modality.marker_refs:
                check(ref)
            if predicate.modality.complement_verb is not None:
                check(predicate.modality.complement_verb)
        for optional_ref in (
            predicate.subject,
            predicate.object,
            predicate.indirect_object,
            predicate.agreement.subject,
            predicate.agreement.predicate,
            predicate.agreement.controller,
        ):
            if optional_ref is not None:
                check(optional_ref)
        for complement in predicate.complements:
            check(complement.governor)
            check(complement.head)
            for ref in complement.evidence_refs:
                check(ref)
        for ref in predicate.agreement.evidence_refs:
            check(ref)
        for ref in predicate.evidence_refs:
            check(ref)
    for complement in features.syntax.complements:
        check(complement.governor)
        check(complement.head)
        for ref in complement.evidence_refs:
            check(ref)
    for coordination in features.syntax.coordination:
        check(coordination.head)
        for ref in coordination.conjuncts:
            check(ref)
    for marker in features.syntax.subordination:
        check(marker.marker_ref)
        check(marker.clause_head)
    for np in features.syntax.np_profiles:
        check(np.head)
        if np.determiner is not None:
            check(np.determiner.ref)
        if np.possessive is not None:
            check(np.possessive)
        for modifier in np.modifiers:
            check(modifier.ref)
        for quantifier in np.quantifiers:
            check(quantifier.ref)
        for ref in np.evidence_refs:
            check(ref)
    for word_order in features.lexical.word_order:
        for ref in word_order.ordered_refs:
            check(ref)
    for negation in features.lexical.negation:
        check(negation.ref)
        if negation.governor is not None:
            check(negation.governor)
    for construction in features.constructions:
        for ref in construction.evidence_refs:
            check(ref)
        for value in construction.slots.values():
            if isinstance(value, int) and value > 0:
                check(value)
            if isinstance(value, tuple):
                for ref in value:
                    check(ref)
    for absence in features.absences:
        check(absence.anchor_ref)
    for contrastive in features.contrastive_support:
        for ref in contrastive.provenance.evidence_refs:
            check(ref)
    for diagnostic in features.diagnostics:
        for ref in diagnostic.refs:
            check(ref)


def _parse_sentence(value: object, path: str) -> AnnotatedSentence:
    mapping = _mapping(value, path)
    text = _string(_required(mapping, "text"), f"{path}.text")
    if text == "":
        raise InputValidationError(f"{path}.text must be non-empty.")
    tokens_value = _sequence(_required(mapping, "tokens"), f"{path}.tokens")
    words_value = _sequence(_required(mapping, "words"), f"{path}.words")
    if len(words_value) == 0:
        raise InputValidationError(f"{path}.words must be non-empty.")
    if len(tokens_value) == 0:
        raise InputValidationError(f"{path}.tokens must be non-empty.")

    words = tuple(
        _parse_word(item, f"{path}.words[{index}]", len(words_value))
        for index, item in enumerate(words_value)
    )
    tokens = tuple(
        _parse_token(item, f"{path}.tokens[{index}]", len(words_value))
        for index, item in enumerate(tokens_value)
    )
    flattened = tuple(word for token in tokens for word in token.words)
    if flattened != words:
        raise InputValidationError(
            f"{path}.tokens flattened words must match {path}.words."
        )
    return AnnotatedSentence(text=text, tokens=tokens, words=words)


def _parse_token(value: object, path: str, sentence_len: int) -> AnnotatedToken:
    mapping = _mapping(value, path)
    text = _string(_required(mapping, "text"), f"{path}.text")
    if text == "":
        raise InputValidationError(f"{path}.text must be non-empty.")
    words_value = _sequence(_required(mapping, "words"), f"{path}.words")
    if len(words_value) == 0:
        raise InputValidationError(f"{path}.words must be non-empty.")
    words = tuple(
        _parse_word(item, f"{path}.words[{index}]", sentence_len)
        for index, item in enumerate(words_value)
    )
    return AnnotatedToken(text=text, words=words)


def _parse_word(value: object, path: str, sentence_len: int) -> AnnotatedWord:
    mapping = _mapping(value, path)
    text = _string(_required(mapping, "text"), f"{path}.text")
    lemma = _string(_required(mapping, "lemma"), f"{path}.lemma")
    upos = _string(_required(mapping, "upos"), f"{path}.upos")
    xpos = _optional_string(mapping, "xpos", f"{path}.xpos")
    feats = _optional_nullable_string(mapping, "feats", f"{path}.feats")
    head = _int(_required(mapping, "head"), f"{path}.head")
    deprel = _string(_required(mapping, "deprel"), f"{path}.deprel")
    start_char = _int(_required(mapping, "start_char"), f"{path}.start_char")
    end_char = _int(_required(mapping, "end_char"), f"{path}.end_char")

    if text == "":
        raise InputValidationError(f"{path}.text must be non-empty.")
    if upos == "":
        raise InputValidationError(f"{path}.upos must be non-empty.")
    if deprel == "":
        raise InputValidationError(f"{path}.deprel must be non-empty.")
    if head < 0 or head > sentence_len:
        raise InputValidationError(f"{path}.head must be in range 0..{sentence_len}.")
    if start_char > end_char:
        raise InputValidationError(f"{path}.start_char must be <= end_char.")

    return AnnotatedWord(
        text=text,
        lemma=lemma,
        upos=upos,
        xpos=xpos,
        feats=feats,
        head=head,
        deprel=deprel,
        start_char=start_char,
        end_char=end_char,
    )


def _parse_entity(value: object, path: str) -> Entity:
    mapping = _mapping(value, path)
    start_char = _int(_required(mapping, "start_char"), f"{path}.start_char")
    end_char = _int(_required(mapping, "end_char"), f"{path}.end_char")
    if start_char > end_char:
        raise InputValidationError(f"{path}.start_char must be <= end_char.")
    return Entity(
        text=_string(_required(mapping, "text"), f"{path}.text"),
        type=_string(_required(mapping, "type"), f"{path}.type"),
        start_char=start_char,
        end_char=end_char,
    )


def _required(mapping: Mapping[object, object], key: str) -> object:
    if key not in mapping:
        raise InputValidationError(f"Missing required field: {key}.")
    return mapping[key]


def _mapping(value: object, path: str) -> Mapping[object, object]:
    if not isinstance(value, Mapping):
        raise InputValidationError(f"{path} must be an object.")
    return value


def _sequence(value: object, path: str) -> Sequence[object]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise InputValidationError(f"{path} must be an array.")
    return value


def _string(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise InputValidationError(f"{path} must be a string.")
    return value


def _optional_string(
    mapping: Mapping[object, object],
    key: str,
    path: str,
) -> str | None:
    if key not in mapping:
        return None
    value = mapping[key]
    if value is None:
        raise InputValidationError(f"{path} must be omitted or a string.")
    return _string(value, path)


def _optional_nullable_string(
    mapping: Mapping[object, object],
    key: str,
    path: str,
) -> str | None:
    if key not in mapping:
        return None
    value = mapping[key]
    if value is None:
        return None
    return _string(value, path)


def _int(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InputValidationError(f"{path} must be an integer.")
    return value
