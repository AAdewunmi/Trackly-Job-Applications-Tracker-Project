# Trackly Domain Model

Trackly is a Django SaaS MVP for tracking job applications and matching job
descriptions against target-role profiles using explainable NLP. The current
domain includes user-owned job applications, application notes, user-scoped
dashboard metrics, target role profiles, and persisted job-fit insights.

## Core Entity: JobApplication

`JobApplication` is the central product object in Trackly. Every application belongs to exactly one authenticated user.

### Fields

| Field | Purpose |
| --- | --- |
| `owner` | The authenticated user who owns the application. |
| `title` | The role title, such as Backend Engineer. |
| `company` | The hiring organisation. |
| `status` | The current workflow state. |
| `job_link` | Optional link to the job advert. |
| `applied_date` | Optional date when the user applied. |
| `job_description` | Optional source text for AI/NLP insight generation. |
| `notes` | Lightweight internal notes stored on the application. |
| `created_at` | Timestamp for record creation. |
| `updated_at` | Timestamp for the latest update. |

## Status Workflow

Trackly uses explicit status choices so metrics and API behaviour remain
predictable.

Current statuses:

| Value | Display | Meaning |
| --- | --- | --- |
| `saved` | Saved | The role is saved but not yet applied to. |
| `applied` | Applied | The user has submitted an application. |
| `screening` | Screening | The application is in recruiter or initial review. |
| `interviewing` | Interviewing | The user is in an interview process. |
| `offer` | Offer | The application resulted in an offer. |
| `rejected` | Rejected | The application was rejected. |
| `withdrawn` | Withdrawn | The user withdrew from the process. |

## Validation Rules

The model enforces these constraints:

1. Title is required.
2. Company is required.
3. Status must be one of the defined workflow states.
4. Applied date cannot be in the future.
5. Job link is optional, but when supplied it must be a valid URL.

Validation is run before saving so invalid state is blocked before persistence.

## ApplicationNote

`ApplicationNote` captures timeline-style context for a job application. Notes are linked to a parent `JobApplication`, and ownership is derived through that parent.

### Fields

| Field | Purpose |
| --- | --- |
| `application` | The parent application. |
| `body` | The note content. |
| `created_at` | Timestamp for creation. |
| `updated_at` | Timestamp for latest edit. |

A note body cannot be blank.

## Ownership Contract

All application and note access is scoped to the authenticated user.

The application list, detail, update, delete, and note creation flows query through user-scoped selectors. A user attempting to access another user's application receives a 404 response. This is deliberate because the object should behave as though it does not exist for that user.

## Selectors

Trackly implements selectors for reusable read queries:

- `application_queryset_for_user(user)`
- `get_user_application_or_404(user, pk)`
- `get_recent_applications_for_user(user, limit=5)`
- `get_recent_applications_for_user_by_status(user, status, limit=5)`
- `notes_queryset_for_user(user)`
- `get_note_count_for_user(user)`

Selectors keep ownership filtering out of templates and reduce duplicated query behaviour across views and services.

## Services

Trackly implements service-layer metric helpers:

- `get_application_status_counts(user)`
- `get_user_pipeline_metrics(user)`
- `get_user_dashboard_context(user)`

Dashboard metrics are calculated from database state and scoped to the logged-in user.

## Dashboard Metrics

The dashboard service prepares these user-scoped metrics for rendering:

| Metric | Definition |
| --- | --- |
| Total applications | All applications owned by the current user. |
| Active applications | Applications with `applied`, `screening`, or `interviewing` status. |
| Saved jobs | Applications with `saved` status. |
| Follow-ups | Applications with `screening` status. |
| Interviews | Applications with `interviewing` status. |
| Offers | Applications with `offer` status. |
| Rejections | Applications with `rejected` status. |
| Notes | Notes attached to the current user's applications. |

The dashboard template renders prepared metrics and recent applications while preserving an actionable empty state for new users.

## Insights Domain

`TargetRoleProfile` stores a user's target-role baseline for retrieval-style
matching.

### TargetRoleProfile Fields

| Field | Purpose |
| --- | --- |
| `owner` | The authenticated user who owns the profile. |
| `title` | The target role title. |
| `description` | Optional longer target-role description. |
| `keywords` | Normalised list of desired skills or target terms. |
| `is_active` | Whether the profile can be used for insight generation. |
| `created_at` | Timestamp for record creation. |
| `updated_at` | Timestamp for latest update. |

`JobInsight` stores the durable output of comparing one job application against
one target role profile.

### JobInsight Fields

| Field | Purpose |
| --- | --- |
| `job_application` | The job application being matched. |
| `target_profile` | The target role profile used as the matching baseline. |
| `source_hash` | Stable hash of cleaned job text, cleaned target text, and pipeline version. |
| `pipeline_version` | Supported NLP pipeline, currently `nltk-tfidf-cosine-v1`. |
| `clean_job_text` | NLTK-processed job-side text used for vectorisation. |
| `clean_target_text` | NLTK-processed target-side text used for vectorisation. |
| `extracted_terms` | Top weighted terms extracted from the job text. |
| `top_overlapping_terms` | Ranked terms present in both job and target vectors. |
| `top_overlapping_weighted_terms` | Overlap terms with job weight, target weight, and overlap contribution. |
| `missing_target_terms` | Ranked target terms absent from the job vector. |
| `missing_weighted_target_terms` | Missing target terms with target-side TF-IDF weights. |
| `similarity_score` | Rounded TF-IDF cosine similarity score. |
| `score_label` | Deterministic label derived from the score. |
| `explanation` | User-facing explanation derived from score and term evidence. |
| `created_at` | Timestamp for insight generation. |

Insight generation requires the job application and target profile to share an
owner. Repeated generation for unchanged cleaned inputs and the same pipeline
version reuses the same persisted insight record.

## Deterministic Demo Data

Trackly includes a deterministic `seed_demo_data` management command for local
showcase and reviewer workflows. The command seeds baseline roles, demo users,
job applications, notes, target role profiles, and persisted job insights using
the current service layer.

The dataset is intentionally broad enough to exercise the main product
surfaces:

- Applications cover every status in the workflow.
- Multiple member accounts demonstrate user scoping and cross-user isolation.
- One empty-state account preserves setup and onboarding screens for review.
- Multiple target profiles support insight filtering and comparison.
- Generated insights use `generate_job_insight()` so seeded records follow the
  same NLTK, TF-IDF, source-hash, and ownership rules as user-generated output.

The command is idempotent and should be treated as local/demo data only.

## Current Completion Status

Trackly currently supports:

1. Users can create job applications.
2. Users can list only their own applications.
3. Users can view only their own application details.
4. Users can update only their own applications.
5. Users can delete only their own applications.
6. Users can add notes only to their own applications.
7. Dashboard metrics reflect real user-owned data.
8. Users can persist target-role profiles for retrieval-style matching.
9. Users can generate persisted job insights from the NLTK + TF-IDF + cosine
   similarity pipeline.
10. Users can review stored insights in the browser insights workspace with
    score labels, extracted terms, overlap terms, missing terms, and explanation
    text.
11. Authenticated API users can list only their own insights and generate or
    reuse insights for user-owned applications and active target profiles.
12. Selectors, services, browser workflows, insight API endpoints, and ownership
    boundaries are covered by database-backed tests.
13. Permission tests prove cross-user access is blocked.
14. Deterministic showcase seed data supports local demos, screenshots, manual
    QA, and reviewer walkthroughs.
