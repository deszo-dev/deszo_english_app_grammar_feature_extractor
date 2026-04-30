From Stdlib Require Import Arith.Arith.
From Stdlib Require Import Lists.List.
From Stdlib Require Import micromega.Lia.
From Stdlib Require Import Strings.String.

Import ListNotations.
Open Scope string_scope.
Open Scope list_scope.
Open Scope nat_scope.

Module GrammarFeatureExtractorSpec.

Definition schema_version : string := "grammar_feature_extractor.v2".
Definition default_page_size : nat := 300.

Inductive ExitCode : Type :=
| Success
| ExpectedError
| SystemError.

Definition exit_code_value (c : ExitCode) : nat :=
  match c with
  | Success => 0
  | ExpectedError => 1
  | SystemError => 2
  end.

Theorem exit_code_contract :
  exit_code_value Success = 0 /\
  exit_code_value ExpectedError = 1 /\
  exit_code_value SystemError >= 2.
Proof.
  repeat split; simpl; lia.
Qed.

Definition non_empty_string (s : string) : Prop := s <> "".
Definition valid_span (start finish : nat) : Prop := start <= finish.
Definition WordRef : Type := nat.
Definition positive_ref (r : WordRef) : Prop := r > 0.

Record AnnotatedWord : Type := {
  word_id : WordRef;
  word_text : string;
  word_lemma : string;
  word_upos : string;
  word_xpos : option string;
  word_feats : option string;
  word_head : nat;
  word_deprel : string;
  word_start_char : nat;
  word_end_char : nat
}.

Definition valid_word (w : AnnotatedWord) : Prop :=
  positive_ref (word_id w) /\
  valid_span (word_start_char w) (word_end_char w) /\
  non_empty_string (word_text w) /\
  non_empty_string (word_upos w) /\
  non_empty_string (word_deprel w).

Record AnnotatedToken : Type := {
  token_text : string;
  token_words : list AnnotatedWord
}.

Definition valid_token (t : AnnotatedToken) : Prop :=
  non_empty_string (token_text t) /\
  token_words t <> [] /\
  Forall valid_word (token_words t).

Record AnnotatedSentence : Type := {
  sentence_text : string;
  sentence_tokens : list AnnotatedToken;
  sentence_words : list AnnotatedWord
}.

Definition valid_sentence (s : AnnotatedSentence) : Prop :=
  non_empty_string (sentence_text s) /\
  sentence_words s <> [] /\
  Forall valid_token (sentence_tokens s) /\
  Forall valid_word (sentence_words s).

Record AnnotatedDocument : Type := {
  doc_sentences : list AnnotatedSentence
}.

Definition valid_annotated_document (d : AnnotatedDocument) : Prop :=
  Forall valid_sentence (doc_sentences d).

Definition ref_in_sentence (s : AnnotatedSentence) (r : WordRef) : Prop :=
  exists w : AnnotatedWord,
    In w (sentence_words s) /\ word_id w = r.

Definition valid_ref (s : AnnotatedSentence) (r : WordRef) : Prop :=
  positive_ref r /\ ref_in_sentence s r.

Definition valid_optional_ref
  (s : AnnotatedSentence)
  (r : option WordRef) : Prop :=
  match r with
  | Some ref => valid_ref s ref
  | None => True
  end.

Inductive PhraseType : Type := NP | VP | PP.

Record Phrase : Type := {
  phrase_type : PhraseType;
  phrase_head : WordRef;
  phrase_tokens : list WordRef
}.

Definition valid_phrase (s : AnnotatedSentence) (p : Phrase) : Prop :=
  valid_ref s (phrase_head p) /\
  phrase_tokens p <> [] /\
  Forall (valid_ref s) (phrase_tokens p).

Record Roles : Type := {
  role_subject : option WordRef;
  role_object : option WordRef;
  role_indirect_object : option WordRef;
  role_oblique : list WordRef
}.

Definition valid_roles (s : AnnotatedSentence) (r : Roles) : Prop :=
  valid_optional_ref s (role_subject r) /\
  valid_optional_ref s (role_object r) /\
  valid_optional_ref s (role_indirect_object r) /\
  Forall (valid_ref s) (role_oblique r).

Record Valency : Type := {
  valency_subject : bool;
  valency_object : bool;
  valency_indirect_object : bool
}.

Inductive ClauseType : Type :=
| RootClause | CCompClause | XCompClause | AdvclClause | RelclClause | AclClause.

Record Clause : Type := {
  clause_head : WordRef;
  clause_type : ClauseType;
  clause_tokens : list WordRef;
  clause_local_tokens : list WordRef;
  clause_roles : Roles;
  clause_valency : Valency
}.

Definition valid_clause (s : AnnotatedSentence) (c : Clause) : Prop :=
  valid_ref s (clause_head c) /\
  clause_tokens c <> [] /\
  clause_local_tokens c <> [] /\
  Forall (valid_ref s) (clause_tokens c) /\
  Forall (valid_ref s) (clause_local_tokens c) /\
  valid_roles s (clause_roles c).

Inductive ComplementType : Type :=
| ComplementNP | ComplementPP | ComplementFiniteClause | ComplementNonfiniteClause.

Record Complement : Type := {
  complement_governor : WordRef;
  complement_head : WordRef;
  complement_type : ComplementType;
  complement_deprel_source : string;
  complement_confidence : string
}.

Definition valid_complement (s : AnnotatedSentence) (c : Complement) : Prop :=
  valid_ref s (complement_governor c) /\
  valid_ref s (complement_head c) /\
  non_empty_string (complement_deprel_source c) /\
  non_empty_string (complement_confidence c).

Inductive Tense : Type := PastTense | PresentTense.
Inductive Aspect : Type := PerfectAspect | ProgressiveAspect.
Inductive Voice : Type := PassiveVoice.

Record TAVM : Type := {
  tavm_tense : option Tense;
  tavm_aspect : list Aspect;
  tavm_voice : option Voice;
  tavm_modality : option string
}.

Record Agreement : Type := {
  agreement_subject : option WordRef;
  agreement_controller : option WordRef;
  agreement_subject_person : option nat;
  agreement_subject_number : option string;
  agreement_predicate_person : option nat;
  agreement_predicate_number : option string;
  agreement_match : option bool
}.

Definition valid_agreement (s : AnnotatedSentence) (a : Agreement) : Prop :=
  valid_optional_ref s (agreement_subject a) /\
  valid_optional_ref s (agreement_controller a).

Inductive PredicateType : Type :=
| VerbalPredicate
| AdjectivalPredicate
| NominalPredicate
| PrepositionalPredicate
| UnknownPredicate.

Record PredicateGroup : Type := {
  predicate_group_main : WordRef;
  predicate_group_type : PredicateType;
  predicate_group_copula : option WordRef;
  predicate_group_auxiliaries : list WordRef;
  predicate_group_negation : option WordRef;
  predicate_group_tokens : list WordRef;
  predicate_group_clause_head : WordRef;
  predicate_group_finite : bool;
  predicate_group_tavm : TAVM;
  predicate_group_agreement : Agreement
}.

Definition valid_predicate_group
  (s : AnnotatedSentence)
  (g : PredicateGroup) : Prop :=
  valid_ref s (predicate_group_main g) /\
  valid_optional_ref s (predicate_group_copula g) /\
  Forall (valid_ref s) (predicate_group_auxiliaries g) /\
  valid_optional_ref s (predicate_group_negation g) /\
  predicate_group_tokens g <> [] /\
  Forall (valid_ref s) (predicate_group_tokens g) /\
  valid_ref s (predicate_group_clause_head g) /\
  valid_agreement s (predicate_group_agreement g).

Record Coordination : Type := {
  coordination_head : WordRef;
  coordination_conjuncts : list WordRef
}.

Definition valid_coordination (s : AnnotatedSentence) (c : Coordination) : Prop :=
  valid_ref s (coordination_head c) /\
  Forall (valid_ref s) (coordination_conjuncts c).

Record Subordination : Type := {
  subordination_marker : string;
  subordination_marker_ref : WordRef;
  subordination_clause_head : WordRef;
  subordination_marker_type : string;
  subordination_confidence : string;
  subordination_sources : list string
}.

Definition valid_subordination (s : AnnotatedSentence) (m : Subordination) : Prop :=
  non_empty_string (subordination_marker m) /\
  valid_ref s (subordination_marker_ref m) /\
  valid_ref s (subordination_clause_head m) /\
  non_empty_string (subordination_marker_type m) /\
  non_empty_string (subordination_confidence m).

Record NPProfile : Type := {
  np_profile_head : WordRef;
  np_profile_determiner : option string;
  np_profile_modifiers : list WordRef
}.

Definition valid_np_profile (s : AnnotatedSentence) (p : NPProfile) : Prop :=
  valid_ref s (np_profile_head p) /\
  Forall (valid_ref s) (np_profile_modifiers p).

Record SyntaxFeatures : Type := {
  syntax_phrases : list Phrase;
  syntax_clauses : list Clause;
  syntax_predicate_groups : list PredicateGroup;
  syntax_complements : list Complement;
  syntax_coordination : list Coordination;
  syntax_subordination : list Subordination;
  syntax_np_profiles : list NPProfile
}.

Definition valid_syntax_features (s : AnnotatedSentence) (f : SyntaxFeatures) : Prop :=
  Forall (valid_phrase s) (syntax_phrases f) /\
  Forall (valid_clause s) (syntax_clauses f) /\
  Forall (valid_predicate_group s) (syntax_predicate_groups f) /\
  Forall (valid_complement s) (syntax_complements f) /\
  Forall (valid_coordination s) (syntax_coordination f) /\
  Forall (valid_subordination s) (syntax_subordination f) /\
  Forall (valid_np_profile s) (syntax_np_profiles f).

Inductive QuestionType : Type := YesNoQuestion | WhQuestion | TagQuestion | NoQuestion.
Inductive ComparativeType : Type := ErComparative | MoreComparative | AsAsComparative.

Record Comparative : Type := {
  comparative_type : ComparativeType;
  comparative_tokens : list WordRef;
  comparative_confidence : string;
  comparative_sources : list string
}.

Definition valid_comparative (s : AnnotatedSentence) (c : Comparative) : Prop :=
  comparative_tokens c <> [] /\
  Forall (valid_ref s) (comparative_tokens c) /\
  non_empty_string (comparative_confidence c).

Record PhrasalVerb : Type := {
  phrasal_verb : WordRef;
  phrasal_particle : string;
  phrasal_particle_ref : WordRef;
  phrasal_confidence : string;
  phrasal_sources : list string
}.

Definition valid_phrasal_verb (s : AnnotatedSentence) (p : PhrasalVerb) : Prop :=
  valid_ref s (phrasal_verb p) /\
  non_empty_string (phrasal_particle p) /\
  valid_ref s (phrasal_particle_ref p) /\
  non_empty_string (phrasal_confidence p).

Record DiscourseMarker : Type := {
  discourse_marker_token : string;
  discourse_marker_refs : list WordRef;
  discourse_marker_type : string;
  discourse_marker_confidence : string;
  discourse_marker_sources : list string
}.

Definition valid_discourse_marker (s : AnnotatedSentence) (m : DiscourseMarker) : Prop :=
  non_empty_string (discourse_marker_token m) /\
  discourse_marker_refs m <> [] /\
  Forall (valid_ref s) (discourse_marker_refs m) /\
  non_empty_string (discourse_marker_type m) /\
  non_empty_string (discourse_marker_confidence m).

Record Complexity : Type := {
  complexity_token_count : nat;
  complexity_clause_count : nat;
  complexity_avg_dependency_depth_x100 : nat
}.

Definition valid_complexity (s : AnnotatedSentence) (c : Complexity) : Prop :=
  complexity_token_count c = List.length (sentence_words s).

Record QuestionFeature : Type := {
  question_feature_type : QuestionType;
  question_feature_confidence : string;
  question_feature_sources : list string
}.

Definition valid_question_feature (q : QuestionFeature) : Prop :=
  non_empty_string (question_feature_confidence q).

Record LexicalFeatures : Type := {
  lexical_sentence_kind : string;
  lexical_question_type : QuestionFeature;
  lexical_comparatives : list Comparative;
  lexical_phrasal_verbs : list PhrasalVerb;
  lexical_discourse_markers : list DiscourseMarker;
  lexical_complexity : Complexity
}.

Definition valid_lexical_features (s : AnnotatedSentence) (f : LexicalFeatures) : Prop :=
  non_empty_string (lexical_sentence_kind f) /\
  valid_question_feature (lexical_question_type f) /\
  Forall (valid_comparative s) (lexical_comparatives f) /\
  Forall (valid_phrasal_verb s) (lexical_phrasal_verbs f) /\
  Forall (valid_discourse_marker s) (lexical_discourse_markers f) /\
  valid_complexity s (lexical_complexity f).

Inductive DiagnosticSeverity : Type :=
| DiagnosticInfo
| DiagnosticWarning
| DiagnosticError.

Record FeatureDiagnostic : Type := {
  diagnostic_severity : DiagnosticSeverity;
  diagnostic_code : string;
  diagnostic_message : string;
  diagnostic_refs : list WordRef;
  diagnostic_feature_path : option string
}.

Definition valid_diagnostic (s : AnnotatedSentence) (d : FeatureDiagnostic) : Prop :=
  non_empty_string (diagnostic_code d) /\
  non_empty_string (diagnostic_message d) /\
  Forall (valid_ref s) (diagnostic_refs d).

Record GrammarFeatureSet : Type := {
  feature_syntax : SyntaxFeatures;
  feature_lexical : LexicalFeatures;
  feature_diagnostics : list FeatureDiagnostic
}.

Definition valid_feature_set (s : AnnotatedSentence) (f : GrammarFeatureSet) : Prop :=
  valid_syntax_features s (feature_syntax f) /\
  valid_lexical_features s (feature_lexical f) /\
  Forall (valid_diagnostic s) (feature_diagnostics f).

Record ExtractorConfig : Type := {
  cfg_include_diagnostics : bool;
  cfg_debug : bool
}.

Record SentenceGrammarFeatures : Type := {
  sentence_feature_index : nat;
  sentence_feature_text : string;
  sentence_feature_set : GrammarFeatureSet
}.

Definition valid_sentence_feature
  (indexed : nat * AnnotatedSentence)
  (out : SentenceGrammarFeatures) : Prop :=
  let '(idx, sentence) := indexed in
  sentence_feature_index out = idx /\
  sentence_feature_text out = sentence_text sentence /\
  valid_feature_set sentence (sentence_feature_set out).

Record GrammarFeatureDocument : Type := {
  feature_schema_version : string;
  feature_source_sentence_count : nat;
  feature_sentences : list SentenceGrammarFeatures
}.

Fixpoint enumerate_from {A : Type} (start : nat) (items : list A) : list (nat * A) :=
  match items with
  | [] => []
  | head :: tail => (start, head) :: enumerate_from (S start) tail
  end.

Definition valid_feature_document
  (input : AnnotatedDocument)
  (output : GrammarFeatureDocument) : Prop :=
  feature_schema_version output = schema_version /\
  feature_source_sentence_count output = List.length (doc_sentences input) /\
  Forall2 valid_sentence_feature
    (enumerate_from 0 (doc_sentences input))
    (feature_sentences output).

Parameter extract_sentence_features :
  ExtractorConfig -> AnnotatedSentence -> GrammarFeatureSet.

Parameter extract_sentence_features_preserves_schema :
  forall (cfg : ExtractorConfig) (s : AnnotatedSentence),
    valid_sentence s ->
    valid_feature_set s (extract_sentence_features cfg s).

Definition sentence_to_features
  (cfg : ExtractorConfig)
  (indexed : nat * AnnotatedSentence) : SentenceGrammarFeatures :=
  let '(idx, sentence) := indexed in
  {|
    sentence_feature_index := idx;
    sentence_feature_text := sentence_text sentence;
    sentence_feature_set := extract_sentence_features cfg sentence
  |}.

Definition extract_core
  (input : AnnotatedDocument)
  (cfg : ExtractorConfig) : GrammarFeatureDocument :=
  {|
    feature_schema_version := schema_version;
    feature_source_sentence_count := List.length (doc_sentences input);
    feature_sentences :=
      map (sentence_to_features cfg) (enumerate_from 0 (doc_sentences input))
  |}.

Theorem extract_core_deterministic :
  forall input cfg,
    extract_core input cfg = extract_core input cfg.
Proof.
  reflexivity.
Qed.

Lemma enumerate_from_preserves_sentence_features :
  forall start sentences cfg,
    Forall valid_sentence sentences ->
    Forall2 valid_sentence_feature
      (enumerate_from start sentences)
      (map (sentence_to_features cfg) (enumerate_from start sentences)).
Proof.
  intros start sentences cfg Hvalid.
  revert start.
  induction Hvalid as [| sentence rest Hsentence _ IH]; intro start.
  - simpl. constructor.
  - simpl. constructor.
    + unfold valid_sentence_feature, sentence_to_features.
      simpl. split.
      * reflexivity.
      * split.
        -- reflexivity.
        -- apply extract_sentence_features_preserves_schema. exact Hsentence.
    + apply IH.
Qed.

Theorem extract_core_preserves_schema :
  forall input cfg,
    valid_annotated_document input ->
    valid_feature_document input (extract_core input cfg).
Proof.
  intros [sentences] cfg Hvalid.
  unfold valid_feature_document, extract_core.
  simpl in *.
  split.
  - reflexivity.
  - split.
    + reflexivity.
    + apply enumerate_from_preserves_sentence_features. exact Hvalid.
Qed.

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
  unfold valid_paging_config, default_paging_config, default_page_size.
  simpl. lia.
Qed.

Definition page_offset (p : PagingConfig) : nat :=
  (page_number p - 1) * page_size p.

Record GrammarFeaturePage : Type := {
  page_schema_version : string;
  page_features : list SentenceGrammarFeatures;
  page_number_out : nat;
  page_size_out : nat;
  page_total_sentences : nat;
  page_start_index : nat;
  page_end_exclusive : nat;
  page_has_next : bool;
  page_next_page : option nat
}.

Definition paginate_feature_document
  (p : PagingConfig)
  (d : GrammarFeatureDocument) : GrammarFeaturePage :=
  let offset := page_offset p in
  let items := firstn (page_size p) (skipn offset (feature_sentences d)) in
  let finish := offset + List.length items in
  let has_next := Nat.ltb finish (feature_source_sentence_count d) in
  {|
    page_schema_version := schema_version;
    page_features := items;
    page_number_out := page_number p;
    page_size_out := page_size p;
    page_total_sentences := feature_source_sentence_count d;
    page_start_index := offset;
    page_end_exclusive := finish;
    page_has_next := has_next;
    page_next_page := if has_next then Some (S (page_number p)) else None
  |}.

Theorem paginated_page_size_bound :
  forall p d,
    List.length (page_features (paginate_feature_document p d)) <= page_size p.
Proof.
  intros p d.
  unfold paginate_feature_document.
  simpl.
  rewrite length_firstn.
  lia.
Qed.

Theorem pagination_preserves_source_count :
  forall p d,
    page_total_sentences (paginate_feature_document p d) =
    feature_source_sentence_count d.
Proof.
  reflexivity.
Qed.

Definition DebugTrace : Type := list string.

Definition observe_debug
  (doc : GrammarFeatureDocument)
  (_trace : DebugTrace) : GrammarFeatureDocument := doc.

Theorem debug_does_not_change_result :
  forall doc trace,
    observe_debug doc trace = doc.
Proof.
  reflexivity.
Qed.

Inductive CliStatus : Type :=
| CliOkPage (page : GrammarFeaturePage)
| CliExpectedDataError
| CliSystemFailure.

Definition cli_exit_code (r : CliStatus) : ExitCode :=
  match r with
  | CliOkPage _ => Success
  | CliExpectedDataError => ExpectedError
  | CliSystemFailure => SystemError
  end.

Theorem cli_exit_code_mapping :
  forall p,
    cli_exit_code (CliOkPage p) = Success /\
    cli_exit_code CliExpectedDataError = ExpectedError /\
    cli_exit_code CliSystemFailure = SystemError.
Proof.
  intro p.
  repeat split; reflexivity.
Qed.

Record CliObservation : Type := {
  obs_stdout : option GrammarFeaturePage;
  obs_stderr : list string;
  obs_exit : ExitCode
}.

Definition valid_cli_observation (o : CliObservation) : Prop :=
  match obs_exit o with
  | Success => exists page, obs_stdout o = Some page
  | ExpectedError => obs_stdout o = None
  | SystemError => obs_stdout o = None
  end.

Theorem non_success_has_no_stdout_payload :
  forall o,
    valid_cli_observation o ->
    obs_exit o <> Success ->
    obs_stdout o = None.
Proof.
  intros o Hvalid Hnot_success.
  destruct o as [out err exit].
  simpl in *.
  destruct exit; try contradiction; exact Hvalid.
Qed.

End GrammarFeatureExtractorSpec.
