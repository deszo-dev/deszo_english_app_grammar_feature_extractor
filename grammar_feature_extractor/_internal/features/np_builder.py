from __future__ import annotations

from grammar_feature_extractor._internal.features.dependency_helpers import (
    children_with_deprel,
    sorted_refs,
)
from grammar_feature_extractor._internal.models import (
    ArticleForm,
    ArticleRequiredness,
    ArticleSlotFeature,
    Definiteness,
    DeterminerFeature,
    DeterminerNumber,
    DeterminerType,
    ModifierFeature,
    ModifierType,
    NPFeature,
    NPType,
    QuantifierFeature,
    SpellingClass,
    SyntacticRole,
)
from grammar_feature_extractor._internal.proof_surface import make_provenance
from grammar_feature_extractor._internal.sentence_context import SentenceContext

VOWEL_LETTERS = frozenset({"a", "e", "i", "o", "u"})


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
        items.append(
            NPFeature(
                id=f"np-{ref}",
                head=ref,
                head_lemma=(word.lemma or word.text).casefold(),
                phrase_type=_phrase_type(word.upos),
                number=_number(ctx, ref),
                person=_person(ctx, ref),
                determiner=determiner,
                has_determiner=bool(det_refs),
                article_slot=_article_slot(ctx, ref, determiner),
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
    head: int,
    determiner: DeterminerFeature | None,
) -> ArticleSlotFeature:
    word = ctx.word_by_ref[head]
    if determiner is None:
        requiredness: ArticleRequiredness = (
            "zero_article"
            if ctx.normalized_morph_by_ref[head].is_plural_noun
            else "missing_required_determiner_candidate"
        )
        article_form: ArticleForm | None = (
            "zero" if requiredness == "zero_article" else None
        )
        definiteness: Definiteness = "generic" if article_form == "zero" else "unknown"
    elif determiner.determiner_type in {"article_definite", "article_indefinite"}:
        requiredness = "article_present"
        article_form = _article_form(determiner.text.casefold())
        definiteness = "definite" if article_form == "the" else "indefinite"
    else:
        requiredness = "determiner_present"
        article_form = None
        definiteness = "unknown"
    return ArticleSlotFeature(
        requiredness=requiredness,
        article_form=article_form,
        following_sound_class="unknown",
        following_spelling_class=_spelling_class(word.text),
        definiteness=definiteness,
        provenance=make_provenance("deterministic", "surface", (head,), "medium"),
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
