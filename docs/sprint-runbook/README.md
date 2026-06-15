# Sprint Runbooks

The executable scripts in this directory are console-only verification runbooks
for Trackly delivery checkpoints. They are intentionally incremental: each
script records the files, routes, services, and tests expected at the end of a
specific sprint day.

## Current Completion Check

Sprint 3 Day 5 is the current completed Sprint 3 checkpoint. Run the Sprint 3
Day 5 script for the current end-to-end verification path:

```bash
./docs/sprint-runbook/sprint-3/sprint-3-day-5.sh
```

The script uses the Docker Compose project name
`trackly-job-applications-tracker-project`, expects the web container prefix
`trackly-job-applications-tracker-project-web`, and verifies the
`postgres:16-alpine` database image. It also verifies the insight browser
workspace, secured insights API endpoints, authentication and ownership
boundaries, NLTK preprocessing, TF-IDF cosine scoring, explainability terms,
weighted evidence, idempotent generation, style checks, and the full regression
suite.

For local demos, screenshots, or manual reviewer walkthroughs, run the
deterministic showcase seed command after migrations:

```bash
make seed
```

The seed command is separate from the sprint verification scripts. It creates
repeatable demo accounts, applications across every workflow status, notes,
target profiles, and persisted insights for product walkthroughs.

## Historical Checkpoints

The earlier scripts remain executable delivery receipts:

- `sprint-1/` records the Django, PostgreSQL, identity, authentication, and
  initial dashboard foundation.
- `sprint-2/sprint-2-day-1.sh` through `sprint-2/sprint-2-day-4.sh` record the
  incremental job model, application workflow, ownership, and note milestones.
- `sprint-2/sprint-2-day-5.sh` records the completed dashboard metrics and
  Sprint 2 workflow checkpoint.
- `sprint-3/sprint-3-day-1.sh` records the DRF/JWT job application API
  checkpoint.
- `sprint-3/sprint-3-day-2.sh` records the insights persistence, model,
  service, migration, and idempotency checkpoint.
- `sprint-3/sprint-3-day-3.sh` records the deterministic NLTK/TF-IDF/cosine NLP
  pipeline checkpoint.
- `sprint-3/sprint-3-day-4.sh` records the browser insight generation workflow
  and dashboard/admin verification checkpoint.

Use those scripts when reviewing the corresponding historical checkpoint. Use
Sprint 3 Day 5 when validating the current completed Sprint 3 state.
