# Trackly Domain Model

Trackly is a Django SaaS MVP for tracking job applications and matching job descriptions against target-role profiles using explainable NLP. Sprint 2 introduces the core workflow domain: user-owned job applications, application notes, and user-scoped dashboard metrics.

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
| `job_description` | Optional source text for later AI/NLP analysis. |
| `notes` | Lightweight internal notes stored on the application. |
| `created_at` | Timestamp for record creation. |
| `updated_at` | Timestamp for the latest update. |

## Status Workflow

Trackly uses explicit status choices so metrics and future API behaviour remain predictable.

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

Sprint 2 introduces selectors for reusable read queries:

- `application_queryset_for_user(user)`
- `get_user_application_or_404(user, pk)`
- `get_recent_applications_for_user(user, limit=5)`
- `notes_queryset_for_user(user)`
- `get_note_count_for_user(user)`

Selectors keep ownership filtering out of templates and reduce duplicated query behaviour across views and services.

## Services

Sprint 2 introduces service-layer metric helpers:

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
| Interviews | Applications with `interviewing` status. |
| Offers | Applications with `offer` status. |
| Rejections | Applications with `rejected` status. |
| Notes | Notes attached to the current user's applications. |

The current dashboard template still displays static preview values. Rendering the prepared metrics and recent applications is the remaining dashboard UI work.

## Sprint 2 Completion Criteria

Sprint 2 is complete when:

1. Users can create job applications.
2. Users can list only their own applications.
3. Users can view only their own application details.
4. Users can update only their own applications.
5. Users can delete only their own applications.
6. Users can add notes only to their own applications.
7. Dashboard metrics reflect real user-owned data.
8. Selectors and services are covered by database-backed tests.
9. Permission tests prove cross-user access is blocked.
10. All Sprint 2 tests pass through Docker Compose.
