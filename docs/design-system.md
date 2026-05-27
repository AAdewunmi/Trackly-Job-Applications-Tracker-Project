# Trackly Design System

This document is the canonical design and implementation guide for Trackly UI.
The frontend standard is:

```text
Django-rendered HTML + HTMX interactions + Trackly CSS
```

Every template should extend `templates/base.html`. Reusable visual rules live in
`static/css/theme.css`. HTMX should be used progressively for server-rendered
partial updates, not as a replacement for accessible HTML.

## Inspiration

Trackly takes product inspiration from Huntr's job tracker experience:

- Clear job-search positioning and direct calls to action.
- Calm, focused surfaces for managing applications, contacts, documents,
  interviews, and metrics.
- Rounded cards, soft shadows, generous spacing, and practical product copy.
- A polished SaaS feel that still prioritizes workflow clarity.
- Navigation that moves users quickly between account, dashboard, and tracking
  tasks.

Trackly must not copy Huntr's brand, exact layouts, text, imagery, or assets.
Use the same product-quality principles while keeping Trackly visually distinct.

## Frontend Architecture

- Django views return full pages or partial HTML.
- Templates render the initial UI on the server.
- HTMX handles targeted interactions using `hx-get`, `hx-post`, `hx-target`,
  `hx-swap`, and related attributes.
- Trackly CSS provides all styling. Do not add Bootstrap, Tailwind, or another
  global CSS framework.
- JavaScript should be minimal and only introduced when HTMX and server-rendered
  HTML are insufficient.

## HTMX Rules

- Use HTMX for real interaction:
  - inline form validation
  - partial list refreshes
  - status changes
  - filters and search
  - account setting updates
  - dashboard card refreshes
- Keep links and forms valid without HTMX where practical.
- Return small partial templates for HTMX requests.
- Use stable targets such as `#profile-card`, `#application-list`, and
  `#flash-messages`.
- Never use HTMX for static content that does not change.

## Design Principles

1. Make the next action obvious.
   Each screen should have one primary action and a small number of supporting
   actions.

2. Keep job-search context visible.
   Page copy should connect account, dashboard, profile, and future application
   tracking features back to the job search.

3. Prefer calm operational UI.
   Trackly is a productivity product. Use readable forms, structured cards, and
   predictable navigation.

4. Use consistent surfaces.
   Forms, profile details, job cards, metrics, and future dashboard panels should
   use the same radius, border, shadow, and spacing rules.

5. Design for growth.
   The system must support future Kanban stages, saved jobs, contacts,
   documents, interview milestones, and search metrics.

## Layout

- Templates must extend `base.html`.
- Main content belongs in `{% block content %}`.
- Use `.tl-container`, `.tl-page`, `.tl-section`, `.tl-grid`, `.tl-panel`, and
  `.tl-actions` before adding new layout classes.
- Use `.tl-auth-shell` for signup and login pages.
- Use `.tl-account-layout` for account/profile pages.
- Use cards only for contained UI: forms, account details, repeated items,
  future dashboard panels.
- Do not nest cards inside cards.

## Landing Pages

Trackly landing pages should feel like a polished job-tracker product page while
remaining original to Trackly.

- Start with a clear navigation bar, direct account CTAs, and page anchors for
  product sections.
- Use a focused hero with one primary account action and one secondary action.
- Show a dashboard or workflow snapshot even before the real dashboard is fully
  implemented. Placeholder UI should look plausible and be easy to replace with
  real data later.
- Include feature sections for pipeline tracking, follow-ups, contacts,
  documents, metrics, and account identity.
- Include a search/map visualization when discussing location, remote, hybrid,
  or opportunity discovery.
- Include pricing when the landing page needs commercial framing. Prices should
  use pound sterling (`£`) and plan cards should clearly distinguish free and
  paid options.
- Repeat the primary CTA near the bottom of the page.
- End with a footer that exposes product and account navigation.
- Do not copy competitor text, screenshots, logos, or brand assets.

## Colour

Trackly uses a clean light theme with crisp blue primary actions, green success
states, and warm neutral surfaces.

- Primary: `--tl-primary`
- Primary dark: `--tl-primary-dark`
- Accent: `--tl-accent`
- Background: `--tl-bg`
- Surface: `--tl-surface`
- Text: `--tl-text`
- Muted text: `--tl-muted`
- Border: `--tl-border`

Avoid one-note pages dominated by a single colour. Keep most UI neutral and use
colour for action, status, and emphasis.

## Typography

- Use the system font stack from `theme.css`.
- Use strong but practical headings.
- Avoid hero-sized text inside forms and cards.
- Use `.tl-eyebrow` for small uppercase context labels.
- Use `.tl-muted` for supporting copy.

## Components

### Buttons

- Primary actions use `.tl-button.tl-button-primary`.
- Secondary actions use `.tl-button.tl-button-secondary`.
- Button groups use `.tl-actions`.

### Cards and Panels

- Use `.tl-card` for forms and contained surfaces.
- Use `.tl-panel` for future dashboard/account sections.
- Cards should use `--tl-radius`, `--tl-border`, and `--tl-shadow`.

### Forms

- Forms should use `novalidate` and render field-level errors.
- Labels should be visible.
- Help text should use `.tl-help-text`.
- Errors should use `.tl-field-error`.
- Submit buttons can use `.tl-button-full` on account forms.

### Badges

- Use `.tl-badge` with status modifiers such as `.tl-badge-success`,
  `.tl-badge-primary`, and `.tl-badge-muted`.

### Messages

- Django messages render through `base.html`.
- Message containers use `#flash-messages` so future HTMX actions can target
  message updates.

## Template Rules

- Every template must start with `{% extends "base.html" %}` unless documented.
- Every page must define `{% block title %}`.
- Avoid inline styles.
- Avoid Bootstrap utility classes and framework-specific component classes.
- Prefer existing Trackly classes before adding new CSS.
- New interactive templates should state the intended HTMX target and fallback.

## Canonical Files

- `docs/design-system.md`: design rules and implementation standards.
- `templates/base.html`: shared shell, navigation, HTMX include, messages,
  footer, and content block.
- `static/css/theme.css`: Trackly design tokens, components, and utilities.

## References

- Huntr job tracker product page: https://huntr.co/product/job-tracker
