from __future__ import annotations

from grammar_feature_extractor._internal.models import (
    AnnotatedSentence,
    AnnotatedWord,
    FeatureDiagnostic,
    MorphFeature,
    MorphologyFeatures,
    NormalizedMorph,
    WordRef,
)


def build_morphology(
    sentence: AnnotatedSentence,
    diagnostics: list[FeatureDiagnostic],
) -> MorphologyFeatures:
    word_morphology: list[MorphFeature] = []
    normalized: list[NormalizedMorph] = []
    words_by_ref = {index + 1: word for index, word in enumerate(sentence.words)}
    for ref, word in words_by_ref.items():
        features = parse_ud_feats(word.feats, ref, diagnostics)
        word_morphology.append(
            MorphFeature(
                ref=ref,
                pos=word.upos,
                xpos=word.xpos,
                lemma=word.lemma,
                features=features,
            )
        )
        previous = words_by_ref.get(ref - 1)
        normalized.append(_normalize_word(ref, word, features, previous))
    return MorphologyFeatures(
        word_morphology=tuple(word_morphology),
        normalized=tuple(normalized),
    )


def parse_ud_feats(
    feats: str | None,
    ref: WordRef,
    diagnostics: list[FeatureDiagnostic],
) -> dict[str, str]:
    if feats is None or feats == "":
        return {}
    result: dict[str, str] = {}
    malformed = False
    for part in feats.split("|"):
        if "=" not in part:
            malformed = True
            continue
        key, value = part.split("=", 1)
        if not key or not value:
            malformed = True
            continue
        result[key] = value
    if malformed:
        diagnostics.append(
            FeatureDiagnostic(
                severity="warning",
                code="malformed_feats",
                message="Malformed morphology features were partially ignored.",
                refs=(ref,),
                feature_path="morphology.word_morphology",
            )
        )
    return result


def _normalize_word(
    ref: WordRef,
    word: AnnotatedWord,
    features: dict[str, str],
    previous: AnnotatedWord | None,
) -> NormalizedMorph:
    verb_form = features.get("VerbForm")
    tense = features.get("Tense")
    xpos = word.xpos or ""
    is_verb = word.upos in {"VERB", "AUX"}
    is_noun = word.upos in {"NOUN", "PROPN"}
    is_to_infinitive = (
        is_verb
        and verb_form == "Inf"
        and previous is not None
        and previous.text.casefold() == "to"
    )
    is_base_verb = is_verb and (
        verb_form == "Inf" or xpos == "VB" or (verb_form is None and tense is None)
    )
    is_participle = is_verb and verb_form == "Part"
    is_finite = is_verb and (
        verb_form == "Fin" or (verb_form is None and tense in {"Past", "Pres"})
    )
    return NormalizedMorph(
        ref=ref,
        is_finite_verb=is_finite,
        is_base_verb=is_base_verb,
        is_to_infinitive=is_to_infinitive,
        is_bare_infinitive=is_base_verb and not is_to_infinitive,
        is_gerund=is_verb and verb_form == "Ger",
        is_past_participle=is_participle
        and (tense == "Past" or xpos in {"VBN"} or features.get("Aspect") == "Perf"),
        is_present_participle=is_participle
        and (tense == "Pres" or xpos in {"VBG"} or features.get("Aspect") == "Prog"),
        is_plural_noun=is_noun and features.get("Number") == "Plur",
        is_singular_noun=is_noun and features.get("Number") == "Sing",
        is_comparative=word.upos in {"ADJ", "ADV"}
        and (features.get("Degree") == "Cmp" or xpos in {"JJR", "RBR"}),
        is_superlative=word.upos in {"ADJ", "ADV"}
        and (features.get("Degree") == "Sup" or xpos in {"JJS", "RBS"}),
    )
