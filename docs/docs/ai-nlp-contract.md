
## `docs/ai-nlp-contract.md`

```markdown
# Trackly AI/NLP Contract

## Purpose

Trackly includes a lightweight retrieval-style AI/NLP feature that helps users compare job descriptions against a target role profile.

This feature is designed as explainable product behaviour, not as a heavy machine learning model.

## Non-goals

The Sprint 3 AI/NLP feature does not:

- Call a third-party LLM.
- Generate personalised career advice.
- Claim hiring probability.
- Rank candidates.
- Replace human judgement.
- Train a model from user data.

## Inputs

The insight generation service uses a job-side document and a target-side document.

The job-side document includes:

- Job title.
- Company.
- Job description.
- Application notes.

The target-side document includes:

- Target role title.
- Target role description.
- Target role keywords.

## Pipeline

The retrieval-style pipeline is:

```text
job source text
+
target profile text

→ NLTK-backed preprocessing
→ lemmatised clean text
→ scikit-learn TF-IDF vectorisation
→ cosine similarity
→ top overlapping high-value terms
→ missing target terms
→ score label
→ explanation
→ stored JobInsight