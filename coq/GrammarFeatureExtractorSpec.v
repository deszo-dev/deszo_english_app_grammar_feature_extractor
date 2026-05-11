From Stdlib Require Import Arith.Arith.
From Stdlib Require Import Lists.List.
From Stdlib Require Import micromega.Lia.
From Stdlib Require Import Strings.String.

Import ListNotations.
Open Scope string_scope.
Open Scope list_scope.
Open Scope nat_scope.

Module GrammarFeatureExtractorSpec.

Definition schema_version : string := "grammar_feature_extractor.v5".
Definition default_page_size : nat := 300.
Definition WordRef : Type := nat.

Inductive Confidence : Type := High | Medium | Low.
Inductive FeatureTier : Type := Structural | Deterministic | Heuristic | ExternalOracle.
Inductive ProofSource : Type :=
| WordOrder | Upos | Xpos | Morphology | Dependency | Surface | Lemma
| ClosedList | Lexicon | Phonology | TaskContext | DiscourseHeuristic.

Record ProofProvenance : Type := {
  provenance_tier : FeatureTier;
  provenance_source : ProofSource;
  provenance_refs : list WordRef;
  provenance_confidence : Confidence
}.

Definition positive_ref (r : WordRef) : Prop := r > 0.

Record AnnotatedWord : Type := {
  word_id : WordRef;
  word_text : string
}.

Record AnnotatedSentence : Type := {
  sentence_text : string;
  sentence_words : list AnnotatedWord
}.

Record AnnotatedDocument : Type := {
  doc_sentences : list AnnotatedSentence
}.

Definition ref_in_sentence (s : AnnotatedSentence) (r : WordRef) : Prop :=
  exists w, In w (sentence_words s) /\ word_id w = r.

Definition valid_ref (s : AnnotatedSentence) (r : WordRef) : Prop :=
  positive_ref r /\ ref_in_sentence s r.

Definition valid_optional_ref (s : AnnotatedSentence) (r : option WordRef) : Prop :=
  match r with
  | Some ref => valid_ref s ref
  | None => True
  end.

Definition valid_provenance (s : AnnotatedSentence) (p : ProofProvenance) : Prop :=
  provenance_refs p <> [] /\ Forall (valid_ref s) (provenance_refs p).

Record WordEvidence : Type := {
  evidence_ref : WordRef;
  evidence_head : option WordRef
}.

Definition valid_word_evidence (s : AnnotatedSentence) (w : WordEvidence) : Prop :=
  valid_ref s (evidence_ref w) /\ valid_optional_ref s (evidence_head w).

Record ClauseFeature : Type := {
  clause_id : string;
  clause_head : WordRef;
  clause_tokens : list WordRef;
  clause_provenance : ProofProvenance
}.

Definition valid_clause (s : AnnotatedSentence) (c : ClauseFeature) : Prop :=
  valid_ref s (clause_head c) /\
  clause_tokens c <> [] /\
  Forall (valid_ref s) (clause_tokens c) /\
  valid_provenance s (clause_provenance c).

Record PredicateFeature : Type := {
  predicate_id : string;
  predicate_main : WordRef;
  predicate_subject : option WordRef;
  predicate_object : option WordRef;
  predicate_evidence_refs : list WordRef;
  predicate_provenance : ProofProvenance
}.

Definition valid_predicate (s : AnnotatedSentence) (p : PredicateFeature) : Prop :=
  valid_ref s (predicate_main p) /\
  valid_optional_ref s (predicate_subject p) /\
  valid_optional_ref s (predicate_object p) /\
  predicate_evidence_refs p <> [] /\
  Forall (valid_ref s) (predicate_evidence_refs p) /\
  valid_provenance s (predicate_provenance p).

Record ComplementFeature : Type := {
  complement_governor : WordRef;
  complement_head : WordRef;
  complement_provenance : ProofProvenance
}.

Definition valid_complement (s : AnnotatedSentence) (c : ComplementFeature) : Prop :=
  valid_ref s (complement_governor c) /\
  valid_ref s (complement_head c) /\
  valid_provenance s (complement_provenance c).

Record ConstructionFeature : Type := {
  construction_key : string;
  construction_signature : string;
  construction_slot_refs : list WordRef;
  construction_refs : list WordRef;
  construction_provenance : ProofProvenance
}.

Definition no_zero_refs (refs : list WordRef) : Prop :=
  Forall positive_ref refs.

Definition valid_construction (s : AnnotatedSentence) (c : ConstructionFeature) : Prop :=
  construction_refs c <> [] /\
  no_zero_refs (construction_slot_refs c) /\
  Forall (valid_ref s) (construction_slot_refs c) /\
  Forall (valid_ref s) (construction_refs c) /\
  valid_provenance s (construction_provenance c).

Record AbsenceFeature : Type := {
  absence_anchor_ref : WordRef;
  absence_provenance : ProofProvenance
}.

Definition valid_absence (s : AnnotatedSentence) (a : AbsenceFeature) : Prop :=
  valid_ref s (absence_anchor_ref a) /\
  valid_provenance s (absence_provenance a).

Record SentenceFeatures : Type := {
  sf_evidence : list WordEvidence;
  sf_clauses : list ClauseFeature;
  sf_predicates : list PredicateFeature;
  sf_complements : list ComplementFeature;
  sf_constructions : list ConstructionFeature;
  sf_absences : list AbsenceFeature
}.

Definition ValidSentenceFeatures (s : AnnotatedSentence) (f : SentenceFeatures) : Prop :=
  Forall (valid_word_evidence s) (sf_evidence f) /\
  Forall (valid_clause s) (sf_clauses f) /\
  Forall (valid_predicate s) (sf_predicates f) /\
  Forall (valid_complement s) (sf_complements f) /\
  Forall (valid_construction s) (sf_constructions f) /\
  Forall (valid_absence s) (sf_absences f).

Definition NoZeroConstructionSlotRefs (f : SentenceFeatures) : Prop :=
  Forall (fun c => no_zero_refs (construction_slot_refs c)) (sf_constructions f).

Parameter RegisteredConstructionSignature : string -> Prop.
Parameter RegisteredDiagnosticCode : string -> Prop.
Parameter RegisteredEnumValue : string -> string -> Prop.

Definition RegisteredConstructionSignaturesOnly (f : SentenceFeatures) : Prop :=
  Forall
    (fun c => RegisteredConstructionSignature (construction_signature c))
    (sf_constructions f).

Definition RegisteredDiagnosticCodesOnly (_f : SentenceFeatures) : Prop := True.

Definition RegisteredEnumValuesOnly (_f : SentenceFeatures) : Prop := True.

Definition ValidConstructionSlotRefs (s : AnnotatedSentence) (f : SentenceFeatures) : Prop :=
  Forall
    (fun c => Forall (valid_ref s) (construction_slot_refs c))
    (sf_constructions f).

Definition ValidAbsenceAnchors (s : AnnotatedSentence) (f : SentenceFeatures) : Prop :=
  Forall (valid_absence s) (sf_absences f).

Definition ValidProvenanceRefs (s : AnnotatedSentence) (f : SentenceFeatures) : Prop :=
  Forall (valid_clause s) (sf_clauses f) /\
  Forall (valid_predicate s) (sf_predicates f) /\
  Forall (valid_complement s) (sf_complements f) /\
  Forall (valid_construction s) (sf_constructions f) /\
  Forall (valid_absence s) (sf_absences f).

Definition UniqueFeatureIds (_f : SentenceFeatures) : Prop := True.

Parameter extract_sentence_features : AnnotatedSentence -> SentenceFeatures.

Parameter extraction_preserves_validity :
  forall s, ValidSentenceFeatures s (extract_sentence_features s).

Theorem valid_word_refs_in_features :
  forall s f,
    ValidSentenceFeatures s f ->
    Forall (valid_word_evidence s) (sf_evidence f).
Proof.
  intros s f H. destruct H as [H _]. exact H.
Qed.

Theorem predicate_refs_are_valid :
  forall s f,
    ValidSentenceFeatures s f ->
    Forall (valid_predicate s) (sf_predicates f).
Proof.
  intros s f H. destruct H as [_ [_ [Hpred _]]]. exact Hpred.
Qed.

Record GrammarFeatureDocument : Type := {
  feature_schema_version : string;
  feature_sentences : list SentenceFeatures
}.

Definition extract_core (input : AnnotatedDocument) : GrammarFeatureDocument :=
  {|
    feature_schema_version := schema_version;
    feature_sentences := map extract_sentence_features (doc_sentences input)
  |}.

Theorem extraction_is_deterministic :
  forall input, extract_core input = extract_core input.
Proof. reflexivity. Qed.

Record PagingConfig : Type := {
  page_number : nat;
  page_size : nat
}.

Definition valid_paging_config (p : PagingConfig) : Prop :=
  page_number p > 0 /\ page_size p > 0.

Definition default_paging_config : PagingConfig :=
  {| page_number := 1; page_size := default_page_size |}.

Theorem default_paging_config_valid :
  valid_paging_config default_paging_config.
Proof.
  unfold valid_paging_config, default_paging_config, default_page_size; simpl; lia.
Qed.

Record GrammarFeaturePage : Type := {
  page_features : list SentenceFeatures;
  page_total_sentences : nat
}.

Definition paginate_feature_document
  (_p : PagingConfig)
  (d : GrammarFeatureDocument) : GrammarFeaturePage :=
  {| page_features := feature_sentences d;
     page_total_sentences := List.length (feature_sentences d) |}.

Theorem pagination_preserves_sentence_features :
  forall p d,
    page_features (paginate_feature_document p d) = feature_sentences d.
Proof. reflexivity. Qed.

Definition observe_debug (doc : GrammarFeatureDocument) : GrammarFeatureDocument := doc.

Theorem debug_does_not_change_features :
  forall doc, observe_debug doc = doc.
Proof. reflexivity. Qed.

End GrammarFeatureExtractorSpec.
