from __future__ import annotations

from grammar_feature_extractor._internal.features.dependency_helpers import (
    children_with_deprel,
    sorted_refs,
)
from grammar_feature_extractor._internal.models import (
    ArticleForm,
    ArticlePresence,
    ArticleRequiredness,
    ArticleSlotFeature,
    Confidence,
    CountabilityFeature,
    Definiteness,
    DeterminerFeature,
    DeterminerNumber,
    DeterminerType,
    GrammarEligibilityFeature,
    ModifierFeature,
    ModifierType,
    NPFeature,
    NPType,
    PhonologySource,
    PluralAnalysisFeature,
    PluralSurfaceClass,
    QuantifierFeature,
    SoundClass,
    SpellingClass,
    SyntacticRole,
)
from grammar_feature_extractor._internal.proof_surface import make_provenance
from grammar_feature_extractor._internal.sentence_context import SentenceContext

VOWEL_LETTERS = frozenset({"a", "e", "i", "o", "u"})
VOWEL_SOUND_EXCEPTIONS = frozenset({"hour", "honest", "honor", "honour", "heir"})
CONSONANT_SOUND_EXCEPTIONS = frozenset({"university", "european", "user", "one"})
UNCOUNTABLE_LEXICON = frozenset(
    {"water", "advice", "information", "money", "furniture", "news"}
)
IRREGULAR_PLURALS = {"children": "child"}
INVARIANT_NOUNS = frozenset({"sheep"})


def build_np_profiles(ctx: SentenceContext) -> tuple[NPFeature, ...]:
    items: list[NPFeature] = []
    for ref in ctx.refs:
        word = ctx.word_by_ref[ref]
        if word.upos not in {"NOUN", "PROPN", "PRON"}:
            continue
        det_refs = children_with_deprel(ctx, ref, "det")
        modifier_refs = children_with_deprel(ctx, ref, "amod", "compound", "nummod")
        quantifier_refs = tuple(
            det_ref for det_ref in det_refs if _det_type(ctx, det_ref) == "quantifier"
        )
        evidence_refs = sorted_refs([ref, *det_refs, *modifier_refs])
        determiner = _determiner(ctx, det_refs[0]) if det_refs else None
        phrase_type = _phrase_type(word.upos)
        number = _number(ctx, ref)
        np_id = f"np-{ref}"
        items.append(
            NPFeature(
                id=np_id,
                head=ref,
                token_refs=evidence_refs,
                determiner_refs=det_refs,
                head_lemma=(word.lemma or word.text).casefold(),
                head_upos=word.upos,
                phrase_type=phrase_type,
                number=number,
                person=_person(ctx, ref),
                grammar_eligibility=_grammar_eligibility(phrase_type),
                determiner=determiner,
                has_determiner=bool(det_refs),
                article_slot=_article_slot(ctx, np_id, ref, determiner, phrase_type),
                modifiers=tuple(
                    ModifierFeature(ref=item, modifier_type=_modifier_type(ctx, item))
                    for item in modifier_refs
                ),
                quantifiers=tuple(
                    QuantifierFeature(ref=item, text=ctx.word_by_ref[item].text)
                    for item in quantifier_refs
                ),
                possessive=_first_child(ctx, ref, "nmod:poss"),
                syntactic_role=_syntactic_role(ctx.word_by_ref[ref].deprel),
                evidence_refs=evidence_refs,
                confidence="high",
                provenance=make_provenance(
                    "deterministic", "dependency", evidence_refs, "high"
                ),
                plural_analysis=_plural_analysis(ctx, ref, number),
                countability=_countability(ctx, ref, phrase_type, number),
            )
        )
    return tuple(items)


def _determiner(ctx: SentenceContext, ref: int) -> DeterminerFeature:
    word = ctx.word_by_ref[ref]
    det_type = _det_type(ctx, ref)
    definite = None
    if det_type == "article_definite":
        definite = True
    elif det_type == "article_indefinite":
        definite = False
    return DeterminerFeature(
        ref=ref,
        text=word.text,
        lemma=(word.lemma or word.text).casefold(),
        determiner_type=det_type,
        definite=definite,
        number=_determiner_number(word.text.casefold()),
        provenance=make_provenance("deterministic", "surface", (ref,), "high"),
    )


def _article_slot(
    ctx: SentenceContext,
    owner_np_id: str,
    head: int,
    determiner: DeterminerFeature | None,
    phrase_type: NPType,
) -> ArticleSlotFeature:
    word = ctx.word_by_ref[head]
    if determiner is None:
        if phrase_type in {"pronoun_np", "proper_noun_np"}:
            requiredness: ArticleRequiredness = "not_applicable"
            article_presence: ArticlePresence = "absent_not_applicable"
        elif ctx.normalized_morph_by_ref[head].is_plural_noun:
            requiredness = "zero_article"
            article_presence = "zero"
        else:
            requiredness = "unknown"
            article_presence = "unknown"
        article_form: ArticleForm | None = (
            "zero" if requiredness == "zero_article" else None
        )
        definiteness: Definiteness = "generic" if article_form == "zero" else "unknown"
    elif determiner.determiner_type in {"article_definite", "article_indefinite"}:
        requiredness = "article_present"
        article_presence = "overt"
        article_form = _article_form(determiner.text.casefold())
        definiteness = "definite" if article_form == "the" else "indefinite"
    else:
        requiredness = "determiner_present"
        article_presence = "overt"
        article_form = None
        definiteness = "unknown"
    sound_class, sound_source, sound_confidence = _sound_class(word.text)
    evidence_refs = sorted_refs(
        [ref for ref in (determiner.ref if determiner else None, head) if ref]
    )
    return ArticleSlotFeature(
        requiredness=requiredness,
        owner_np_id=owner_np_id,
        article_presence=article_presence,
        article_form=article_form,
        determiner_ref=determiner.ref if determiner else None,
        head_ref=head,
        following_word_ref=head,
        following_sound_class=sound_class,
        following_sound_source=sound_source,
        following_sound_confidence=sound_confidence,
        following_spelling_class=_spelling_class(word.text),
        definiteness=definiteness,
        evidence_refs=evidence_refs,
        source="heuristic" if sound_source != "unknown" else "unknown",
        confidence="medium" if sound_source != "unknown" else "low",
        provenance=make_provenance("deterministic", "surface", evidence_refs, "medium"),
    )


def _det_type(ctx: SentenceContext, ref: int) -> DeterminerType:
    lower = ctx.word_by_ref[ref].text.casefold()
    if lower == "the":
        return "article_definite"
    if lower in {"a", "an"}:
        return "article_indefinite"
    if lower in {"this", "that", "these", "those"}:
        return "demonstrative"
    if lower in {"my", "your", "his", "her", "its", "our", "their"}:
        return "possessive"
    if lower in {"some", "any", "many", "much", "few", "several", "all"}:
        return "quantifier"
    if lower == "no":
        return "negative_no"
    return "unknown"


def _phrase_type(upos: str) -> NPType:
    if upos == "NOUN":
        return "common_noun_np"
    if upos == "PROPN":
        return "proper_noun_np"
    if upos == "PRON":
        return "pronoun_np"
    return "unknown"


def _grammar_eligibility(phrase_type: NPType) -> GrammarEligibilityFeature:
    if phrase_type == "common_noun_np":
        return GrammarEligibilityFeature(
            article_choice_eligible=True,
            countability_choice_eligible=True,
            plural_inflection_choice_eligible=True,
            reason="common_noun_np",
        )
    reason = (
        "proper_noun_np_default_exclusion"
        if phrase_type == "proper_noun_np"
        else phrase_type
    )
    return GrammarEligibilityFeature(
        article_choice_eligible=False,
        countability_choice_eligible=False,
        plural_inflection_choice_eligible=False,
        reason=reason,
    )


def _countability(
    ctx: SentenceContext,
    ref: int,
    phrase_type: NPType,
    number: DeterminerNumber,
) -> CountabilityFeature:
    lemma = (ctx.word_by_ref[ref].lemma or ctx.word_by_ref[ref].text).casefold()
    if phrase_type == "pronoun_np":
        return CountabilityFeature(
            status="pronoun_not_applicable", source="parser", confidence="high"
        )
    if phrase_type == "proper_noun_np":
        return CountabilityFeature(
            status="proper_name", source="parser", confidence="high"
        )
    if lemma in UNCOUNTABLE_LEXICON:
        return CountabilityFeature(
            status="uncountable", source="lexicon", confidence="high"
        )
    if number == "plural":
        return CountabilityFeature(
            status="count_plural", source="morphology", confidence="high"
        )
    return CountabilityFeature(status="unknown", source="unknown", confidence="low")


def _plural_analysis(
    ctx: SentenceContext,
    ref: int,
    number: DeterminerNumber,
) -> PluralAnalysisFeature:
    word = ctx.word_by_ref[ref]
    lemma = (word.lemma or word.text).casefold()
    surface = word.text.casefold()
    return PluralAnalysisFeature(
        number=number,
        surface_plural_class=_plural_surface_class(lemma, surface, number),
        lemma=lemma,
        surface=word.text,
        confidence="high" if number != "unknown" else "low",
    )


def _plural_surface_class(
    lemma: str,
    surface: str,
    number: DeterminerNumber,
) -> PluralSurfaceClass:
    if number == "singular":
        return "singular"
    if surface in IRREGULAR_PLURALS:
        return "irregular"
    if surface in INVARIANT_NOUNS and lemma == surface:
        return "invariant"
    if surface.endswith("ies") and lemma.endswith("y") and len(lemma) > 1:
        return "consonant_y_ies"
    if surface.endswith("es") and lemma.endswith(("s", "x", "z", "ch", "sh")):
        return "regular_es_after_sibilant"
    if surface.endswith("s"):
        return "regular_s"
    return "unknown"


def _number(ctx: SentenceContext, ref: int) -> DeterminerNumber:
    if ctx.normalized_morph_by_ref[ref].is_plural_noun:
        return "plural"
    if ctx.normalized_morph_by_ref[ref].is_singular_noun:
        return "singular"
    return "unknown"


def _person(ctx: SentenceContext, ref: int) -> int | None:
    value = ctx.morph_by_ref[ref].features.get("Person")
    if value in {"1", "2", "3"}:
        return int(value)
    return None


def _modifier_type(ctx: SentenceContext, ref: int) -> ModifierType:
    deprel = ctx.word_by_ref[ref].deprel
    if deprel == "amod":
        return "adjective"
    if deprel == "compound":
        return "compound"
    if deprel == "nummod":
        return "number"
    return "unknown"


def _syntactic_role(deprel: str) -> SyntacticRole:
    if deprel in {"nsubj", "nsubj:pass"}:
        return "subject"
    if deprel == "obj":
        return "object"
    if deprel == "iobj":
        return "indirect_object"
    if deprel == "obl":
        return "oblique"
    return "unknown"


def _determiner_number(lower: str) -> DeterminerNumber | None:
    if lower in {"this", "that", "a", "an"}:
        return "singular"
    if lower in {"these", "those"}:
        return "plural"
    if lower in {"the", "some", "any"}:
        return "both"
    return None


def _spelling_class(text: str) -> SpellingClass:
    if not text:
        return "unknown"
    return "vowel_letter" if text[0].casefold() in VOWEL_LETTERS else "consonant_letter"


def _sound_class(text: str) -> tuple[SoundClass, PhonologySource, Confidence]:
    lower = text.casefold()
    if lower in VOWEL_SOUND_EXCEPTIONS:
        return "vowel_sound", "exception_list", "high"
    if lower in CONSONANT_SOUND_EXCEPTIONS:
        return "consonant_sound", "exception_list", "high"
    spelling_class = _spelling_class(text)
    if spelling_class == "vowel_letter":
        return "vowel_sound", "spelling_heuristic", "medium"
    if spelling_class == "consonant_letter":
        return "consonant_sound", "spelling_heuristic", "medium"
    return "unknown", "unknown", "low"


def _first_child(ctx: SentenceContext, head: int, deprel: str) -> int | None:
    refs = children_with_deprel(ctx, head, deprel)
    return refs[0] if refs else None


def _article_form(lower: str) -> ArticleForm | None:
    if lower == "a":
        return "a"
    if lower == "an":
        return "an"
    if lower == "the":
        return "the"
    return None
