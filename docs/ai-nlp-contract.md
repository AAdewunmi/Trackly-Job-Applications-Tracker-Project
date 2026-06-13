# Trackly AI/NLP Contract

## Purpose

Trackly includes a lightweight retrieval-style AI/NLP feature that helps users
compare job descriptions against a target role profile.

This feature is designed as explainable product behaviour, not as a heavy
machine learning model.

## Non-goals

The AI/NLP feature does not:

- Call a third-party LLM.
- Generate personalised career advice.
- Claim hiring probability.
- Rank candidates.
- Replace human judgement.
- Train a model from user data.

## Inputs

The insight generation service uses a job-side document and a target-side
document.

The job-side document includes:

- Job title.
- Company.
- Job description.
- Application notes.

The target-side document includes:

- Target role title.
- Target role description.
- Target role keywords.

## Current Contract

The current project state provides the persistence and service boundary for
retrieval-style job insights.

Implemented now:

- User-owned target role profiles.
- Desired skill keywords stored on target role profiles.
- Stored `JobInsight` records linked to a job application and target role
  profile.
- Durable insight fields for cleaned source text, extracted terms, overlapping
  terms, weighted overlapping terms, missing target terms, weighted missing
  target terms, similarity score, score label, explanation, source hash, and
  pipeline version.
- A single allowed pipeline version:
  `nltk-tfidf-cosine-v1`.
- Service-level enforcement that users need an active target role profile before
  generating an insight.
- Ownership validation so job applications and target role profiles must belong
  to the same user.

The current service implementation writes durable `JobInsight` records under
the `nltk-tfidf-cosine-v1` contract and uses the implemented NLTK/scikit-learn
TF-IDF cosine pipeline. The Docker image provisions required NLTK runtime data
during build; local containers can refresh that data with `make nltk-data`.

## Canonical Pipeline

The canonical pipeline for `nltk-tfidf-cosine-v1` is:

```text
job source text
+
target profile text

-> NLTK-backed preprocessing with deterministic fallback lemmatisation
-> lemmatised clean text
-> scikit-learn TF-IDF vectorisation
-> cosine similarity
-> extracted weighted job terms
-> top overlapping high-value terms
-> top overlapping weighted evidence
-> missing target terms
-> missing weighted target evidence
-> score label
-> explanation
-> stored JobInsight
```

## Score Labels

The cosine similarity score is rounded to two decimal places before labelling.
Labels are deterministic:

- `Excellent match`: score >= 0.75.
- `Strong match`: score >= 0.50 and < 0.75.
- `Partial match`: score >= 0.25 and < 0.50.
- `Low match`: score < 0.25.

## Implementation Status

### Phase 1: Persistence and Contract Boundary

Implemented:

- `TargetRoleProfile` stores the target role baseline.
- `JobInsight` stores generated insight output as durable product state.
- The model enforces `nltk-tfidf-cosine-v1` as the supported pipeline version.
- The service derives `source_hash` from the cleaned job text, cleaned target
  text, and pipeline version.
- The service creates and reuses insight records for unchanged cleaned
  job/profile sources under the same pipeline version.

### Phase 2: NLTK Preprocessing

Implemented:

- Token normalisation backed by NLTK.
- Stop-word filtering for common and low-value role-description terms.
- Lemmatized clean job and target text.
- A runtime-data check that raises an actionable error when required NLTK data
  is missing and points developers to `make nltk-data`.
- Deterministic fallback lemmatisation so preprocessing remains stable if
  WordNet data is unavailable during token lemmatisation.

### Phase 3: TF-IDF Cosine Matching

Implemented:

- scikit-learn TF-IDF vectorisation.
- Cosine similarity between job and target documents.
- Stable score calculation stored as `similarity_score`.

### Phase 4: Explainability Terms

Implemented:

- Top overlapping high-value terms.
- Top overlapping weighted evidence containing term, job TF-IDF weight, target
  TF-IDF weight, and overlap contribution weight.
- Missing target terms.
- Missing weighted target evidence containing term and target TF-IDF weight.
- Explanation text derived from the similarity score and term analysis.
- A user-facing presentation policy that keeps readable single terms and
  approved useful phrases while suppressing mechanically generated bigrams from
  simple display fields and explanation text.

Deterministic ranking rules:

- Weighted overlapping evidence is generated from terms with non-zero TF-IDF
  weight in both the job and target vectors.
- Overlap ranking uses `job_tfidf_weight * target_tfidf_weight`, descending.
- Weighted missing evidence is generated from terms with non-zero target TF-IDF
  weight and zero job TF-IDF weight.
- Missing-term ranking uses target TF-IDF weight, descending.
- Equal weights are ordered alphabetically, so repeated generation for the same
  cleaned input produces the same term order.
- `top_overlapping_weighted_terms` and `missing_weighted_target_terms` contain
  the numeric TF-IDF evidence used to produce those rankings.
- `top_overlapping_terms` and `missing_target_terms` are filtered from the
  ranked weighted evidence for user-facing display and explanation text.
- Stored weights are rounded to four decimal places to avoid noisy floating
  point output while preserving enough precision for explanation and audit.

User-facing presentation policy:

- Single terms are allowed when they pass preprocessing and TF-IDF ranking.
- Two-word phrases are allowed only when they are approved useful phrases such
  as `backend engineer`, `software engineer`, `data analyst`, `data engineer`,
  `machine learning`, `rest api`, `unit test`, `integration test`, `product
  manager`, `product management`, `project management`, `customer success`,
  `cloud platform`, or `ci cd`.
- Mechanically generated bigrams such as `api postgresql`, `delivery python`,
  or `postgresql test` are suppressed from `extracted_terms`,
  `top_overlapping_terms`, `missing_target_terms`, and `explanation`.
- Suppressed bigrams remain available in `top_overlapping_weighted_terms` and
  `missing_weighted_target_terms` for auditability and API/detail consumers.
- The browser insights dashboard displays the filtered simple term lists. The
  API returns both filtered simple term lists and complete weighted evidence.

## Stored Output

`JobInsight` is the durable record for generated output.

Stored fields include:

- `job_application`
- `target_profile`
- `source_hash`
- `pipeline_version`
- `clean_job_text`
- `clean_target_text`
- `extracted_terms`
- `top_overlapping_terms`
- `top_overlapping_weighted_terms`
- `missing_target_terms`
- `missing_weighted_target_terms`
- `similarity_score`
- `score_label`
- `explanation`
- `created_at`

The `source_hash` is calculated from the cleaned job text, cleaned target text,
and pipeline version. The `source_hash` and `pipeline_version` pair make
insight records stable for unchanged cleaned inputs and a specific algorithm
version.
