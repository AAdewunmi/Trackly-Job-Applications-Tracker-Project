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
  terms, missing target terms, similarity score, score label, explanation,
  source hash, and pipeline version.
- A single allowed pipeline version:
  `nltk-tfidf-cosine-v1`.
- Service-level enforcement that users need an active target role profile before
  generating an insight.
- Ownership validation so job applications and target role profiles must belong
  to the same user.

The current service implementation writes durable `JobInsight` records under
the `nltk-tfidf-cosine-v1` contract and uses the implemented NLTK/scikit-learn
TF-IDF cosine pipeline.

## Canonical Pipeline

The canonical pipeline for `nltk-tfidf-cosine-v1` is:

```text
job source text
+
target profile text

-> NLTK-backed preprocessing
-> lemmatised clean text
-> scikit-learn TF-IDF vectorisation
-> cosine similarity
-> top overlapping high-value terms
-> missing target terms
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
- The service creates and reuses insight records for unchanged job/profile
  sources.

### Phase 2: NLTK Preprocessing

Implemented:

- Token normalisation backed by NLTK.
- Stop-word filtering for common and low-value role-description terms.
- Lemmatized clean job and target text.

### Phase 3: TF-IDF Cosine Matching

Implemented:

- scikit-learn TF-IDF vectorisation.
- Cosine similarity between job and target documents.
- Stable score calculation stored as `similarity_score`.

### Phase 4: Explainability Terms

Implemented:

- Top overlapping high-value terms.
- Missing target terms.
- Explanation text derived from the similarity score and term analysis.

Deterministic ranking rules:

- `top_overlapping_terms` are generated from terms with non-zero TF-IDF weight
  in both the job and target vectors.
- Overlap ranking uses `job_tfidf_weight * target_tfidf_weight`, descending.
- `missing_target_terms` are generated from terms with non-zero target TF-IDF
  weight and zero job TF-IDF weight.
- Missing-term ranking uses target TF-IDF weight, descending.
- Equal weights are ordered alphabetically, so repeated generation for the same
  cleaned input produces the same term order.
- Stored explanation fields contain the ranked term names, not raw numeric
  TF-IDF weights.

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
- `missing_target_terms`
- `similarity_score`
- `score_label`
- `explanation`
- `created_at`

The `source_hash` and `pipeline_version` pair make insight records stable for
unchanged inputs and a specific algorithm version.
