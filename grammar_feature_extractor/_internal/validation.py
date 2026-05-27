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
    ExtractorConfig,
    GrammarFeatureSet,
    PagingConfig,
    STANZA_DOCUMENT_PRODUCER,
    StanzaDocumentInputLineage,
    WordRef,
)
from grammar_feature_extractor._internal.semantic_validation import (
    validate_annotated_document_semantics,
    validate_resolved_config_semantics,
)


def parse_annotated_document(value: object) -> AnnotatedDocument:
    if not isinstance(value, Mapping):
        raise InputValidationError("Input must be a stanza_annotator_document object.")
    return _parse_stanza_document(value)


def _parse_stanza_document(value: Mapping[object, object]) -> AnnotatedDocument:
    producer = _string(_required(value, "producer"), "producer")
    if producer != STANZA_DOCUMENT_PRODUCER:
        raise InputValidationError("producer must be stanza_annotator_document.")
    schema_version = _string(_required(value, "schema_version"), "schema_version")
    document_id = _string(_required(value, "document_id"), "document_id")
    status = _string(_required(value, "status"), "status")
    if status not in {"success", "succeeded", "partial"}:
        raise InputValidationError("status must be success, succeeded or partial.")
    language = _optional_nullable_string(value, "language", "language")
    traversal = _mapping(_required(value, "traversal"), "traversal")
    selected_unit_count = _int(
        _required(traversal, "selected_unit_count"),
        "traversal.selected_unit_count",
    )
    global_sentence_count = _int(
        _required(traversal, "global_sentence_count"),
        "traversal.global_sentence_count",
    )
    global_word_count = _int(
        _required(traversal, "global_word_count"),
        "traversal.global_word_count",
    )
    diagnostics = _sequence(_required(value, "diagnostics"), "diagnostics")
    _reject_blocking_diagnostics(diagnostics, "diagnostics")
    validation_summary = _mapping(
        _required(value, "validation_summary"),
        "validation_summary",
    )
    if validation_summary.get("is_handoff_ready") is False:
        raise InputValidationError("validation_summary.is_handoff_ready must not be false.")
    error_count = validation_summary.get("error_count")
    if isinstance(error_count, int) and not isinstance(error_count, bool) and error_count > 0:
        raise InputValidationError("validation_summary.error_count must be 0.")
    units = _sequence(_required(value, "units"), "units")
    parsed_sentences: list[AnnotatedSentence] = []
    for unit_index, raw_unit in enumerate(units):
        parsed_sentences.extend(_parse_stanza_unit(raw_unit, f"units[{unit_index}]"))

    parsed_sentences.sort(key=lambda sentence: sentence.global_sentence_index or 0)
    _validate_global_sentence_indexes(parsed_sentences)
    document = AnnotatedDocument(
        sentences=tuple(parsed_sentences),
        entities=(),
        input_lineage=StanzaDocumentInputLineage(
            source_module=STANZA_DOCUMENT_PRODUCER,
            source_schema_version=schema_version,
            document_id=document_id,
            language=language,
            source_status=status,  # type: ignore[arg-type]
            selected_unit_count=selected_unit_count,
            global_sentence_count=global_sentence_count,
            global_word_count=global_word_count,
        ),
    )
    validate_annotated_document_semantics(document)
    return document


def _parse_stanza_unit(value: object, path: str) -> list[AnnotatedSentence]:
    unit = _mapping(value, path)
    execution_status = unit.get("execution_status")
    if execution_status not in {
        None,
        "completed",
        "completed_with_warnings",
        "succeeded",
        "success",
    }:
        raise InputValidationError(f"{path}.execution_status must be completed/succeeded.")
    unit_id = _string(_required(unit, "unit_id"), f"{path}.unit_id")
    unit_type = _string(_required(unit, "unit_type"), f"{path}.unit_type")
    role = _string(_required(unit, "role"), f"{path}.role")
    unit_order = _int(unit.get("unit_order", unit.get("order")), f"{path}.unit_order")
    text_hash = _optional_nullable_string(unit, "text_hash", f"{path}.text_hash")
    annotation = _mapping(_required(unit, "annotation"), f"{path}.annotation")
    annotation_status = annotation.get("status")
    annotation_execution_status = annotation.get("execution_status")
    if annotation_status not in {None, "succeeded", "success", "partial"}:
        raise InputValidationError(f"{path}.annotation.status is not usable.")
    if annotation_execution_status not in {
        None,
        "completed",
        "completed_with_warnings",
        "succeeded",
        "success",
    }:
        raise InputValidationError(f"{path}.annotation.execution_status is not usable.")
    _reject_blocking_diagnostics(
        _sequence(annotation.get("diagnostics", []), f"{path}.annotation.diagnostics"),
        f"{path}.annotation.diagnostics",
    )
    sentences = _sequence(
        _required(annotation, "sentences"),
        f"{path}.annotation.sentences",
    )
    return [
        _parse_stanza_handoff_sentence(
            raw_sentence,
            f"{path}.annotation.sentences[{sentence_index}]",
            unit_id=unit_id,
            unit_type=unit_type,
            role=role,
            unit_order=unit_order,
            text_hash=text_hash,
        )
        for sentence_index, raw_sentence in enumerate(sentences)
    ]


def _parse_stanza_handoff_sentence(
    value: object,
    path: str,
    *,
    unit_id: str,
    unit_type: str,
    role: str,
    unit_order: int,
    text_hash: str | None,
) -> AnnotatedSentence:
    sentence = _mapping(value, path)
    text = _string(_required(sentence, "text"), f"{path}.text")
    if text == "":
        raise InputValidationError(f"{path}.text must be non-empty.")
    global_sentence_id = _string(
        _required(sentence, "global_sentence_id"),
        f"{path}.global_sentence_id",
    )
    global_sentence_index = _int(
        _required(sentence, "global_sentence_index"),
        f"{path}.global_sentence_index",
    )
    local_sentence_index = _int(
        _required(sentence, "local_sentence_index"),
        f"{path}.local_sentence_index",
    )
    raw_words = _sequence(_required(sentence, "words"), f"{path}.words")
    if len(raw_words) == 0:
        raise InputValidationError(f"{path}.words must be non-empty.")
    ordered = sorted(
        (
            _parse_handoff_word(raw_word, f"{path}.words[{word_index}]", unit_id)
            for word_index, raw_word in enumerate(raw_words)
        ),
        key=lambda item: item[0],
    )
    words = tuple(word for _, word in ordered)
    tokens = tuple(AnnotatedToken(text=word.text, words=(word,)) for word in words)
    return AnnotatedSentence(
        text=text,
        tokens=tokens,
        words=words,
        global_sentence_id=global_sentence_id,
        global_sentence_index=global_sentence_index,
        local_sentence_index=local_sentence_index,
        source_unit_id=unit_id,
        source_unit_order=unit_order,
        source_unit_type=unit_type,
        source_unit_role=role,
        source_text_hash=text_hash,
    )


def _parse_handoff_word(
    value: object,
    path: str,
    unit_id: str,
) -> tuple[int, AnnotatedWord]:
    word = _mapping(value, path)
    word_number = _int(_required(word, "word_number"), f"{path}.word_number")
    source_word_id = _optional_nullable_string(word, "id", f"{path}.id")
    text = _string(_required(word, "text"), f"{path}.text")
    lemma = _string(_required(word, "lemma"), f"{path}.lemma")
    upos = _string(_required(word, "upos"), f"{path}.upos")
    xpos = _optional_nullable_string(word, "xpos", f"{path}.xpos")
    feats = _feats_to_ud_string(word)
    head = _int(_required(word, "head"), f"{path}.head")
    deprel = _string(_required(word, "deprel"), f"{path}.deprel")
    start_char = _int(_required(word, "start_char"), f"{path}.start_char")
    end_char = _int(_required(word, "end_char"), f"{path}.end_char")
    if text == "":
        raise InputValidationError(f"{path}.text must be non-empty.")
    if lemma == "":
        raise InputValidationError(f"{path}.lemma must be non-empty.")
    if upos == "":
        raise InputValidationError(f"{path}.upos must be non-empty.")
    if deprel == "":
        raise InputValidationError(f"{path}.deprel must be non-empty.")
    if head < 0:
        raise InputValidationError(f"{path}.head must be >= 0.")
    if start_char > end_char:
        raise InputValidationError(f"{path}.start_char must be <= end_char.")
    return (
        word_number,
        AnnotatedWord(
            text=text,
            lemma=lemma,
            upos=upos,
            xpos=xpos,
            feats=feats,
            head=head,
            deprel=deprel,
            start_char=start_char,
            end_char=end_char,
            source_word_id=source_word_id,
            source_token_id=None,
            source_unit_id=unit_id,
        ),
    )


def _feats_to_ud_string(word: Mapping[object, object]) -> str | None:
    raw_map = word.get("feats_map")
    if isinstance(raw_map, Mapping):
        parts: list[str] = []
        for key in sorted(raw_map):
            if not isinstance(key, str):
                continue
            value = raw_map[key]
            if isinstance(value, str) and value:
                parts.append(f"{key}={value}")
        return "|".join(parts) if parts else None
    if word.get("feats") is None and "feats" in word:
        raise InputValidationError("feats must be omitted or a string.")
    raw = word.get("feats_raw", word.get("feats"))
    if raw is None:
        return None
    return _string(raw, "feats_raw")


def _validate_global_sentence_indexes(sentences: list[AnnotatedSentence]) -> None:
    expected = list(range(len(sentences)))
    actual = [sentence.global_sentence_index for sentence in sentences]
    if actual != expected:
        raise InputValidationError(
            "global_sentence_index values must be unique and contiguous from 0."
        )


def _reject_blocking_diagnostics(diagnostics: Sequence[object], path: str) -> None:
    for index, raw_diagnostic in enumerate(diagnostics):
        if not isinstance(raw_diagnostic, Mapping):
            continue
        severity = raw_diagnostic.get("severity")
        result_impact = raw_diagnostic.get("result_impact")
        if severity in {"fatal", "error"} or result_impact in {"blocking", "invalid"}:
            raise InputValidationError(f"{path}[{index}] contains a blocking diagnostic.")


def validate_paging_config(paging: PagingConfig) -> None:
    if isinstance(paging.page_number, bool) or paging.page_number < 1:
        raise ConfigurationError("page_number must be an integer >= 1.")
    if isinstance(paging.page_size, bool) or paging.page_size < 1:
        raise ConfigurationError("page_size must be an integer >= 1.")
    if paging.page_size > MAX_PAGE_SIZE:
        raise ConfigurationError(f"page_size must be <= {MAX_PAGE_SIZE}.")
    validate_resolved_config_semantics(paging.page_size, MAX_PAGE_SIZE)


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
        for ref in word_order.slots.values():
            check(ref)
    for negation in features.lexical.negation:
        check(negation.ref)
        if negation.governor is not None:
            check(negation.governor)
    for lexical_group in (
        features.lexical.time_markers,
        features.lexical.comparisons,
        features.lexical.phrasal_verbs,
        features.lexical.discourse_markers,
        features.lexical.contractions,
        features.lexical.noun_inflections,
    ):
        for item in lexical_group:
            for ref in item.refs:
                check(ref)
            for ref in item.provenance.evidence_refs:
                check(ref)
    for construction in features.constructions:
        for ref in construction.evidence_refs:
            check(ref)
        for value in construction.slots.values():
            if isinstance(value, int):
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


