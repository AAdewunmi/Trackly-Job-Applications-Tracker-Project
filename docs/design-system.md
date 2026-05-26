# Trackly Design System

This document is the canonical design and implementation guide for Trackly
templates. Every project template should extend `templates/base.html` and use
the shared styling in `static/css/theme.css`.

## Inspiration

Trackly takes product inspiration from Huntr's job tracker experience:

- A focused job-search workflow with clear account and dashboard actions.
- Calm, organized layouts for tracking applications, contacts, documents, and
  interview activity.
- Strong primary calls to action with supportive secondary actions.
- Rounded cards, soft shadows, generous spacing, and friendly but practical
  copy.
- A product tone that helps users feel in control of a busy job search.

Trackly should not copy Huntr's brand, content, assets, or exact UI. Use the
same product-quality principles while keeping Trackly visually distinct.

## Design Principles

1. Make the next action obvious.
   Each screen should have one primary action and, when useful, one secondary
   action. Avoid competing buttons.

2. Keep job-search context visible.
   Page copy should connect account, dashboard, profile, and future application
   tracking features back to the user's job-search workflow.

3. Prefer calm operational UI.
   Trackly is a productivity product. Use clean sections, readable forms, and
   organized cards instead of decorative layouts.

4. Use consistent surfaces.
   Forms, account details, and future dashboard panels should use the same card,
   border, shadow, spacing, and heading patterns.

5. Design for growth.
   Current pages are account-first, but the system should support future job
   cards, application stages, metrics, contacts, documents, and interview
   milestones.

## Layout

- Templates must extend `base.html`.
- Use `.tl-page`, `.tl-section`, `.tl-card`, and `.tl-stack` utilities before
  adding one-off layout CSS.
- Use Bootstrap's grid for page structure and Trackly CSS variables for visual
  styling.
- Keep main content centered and readable.
- Use cards for contained forms and account details.
- Use full-width or unframed sections for landing content.

## Colour

Trackly uses a clean light theme with a blue primary, green success accents, and
warm off-white backgrounds.

- Primary: `--tl-primary`
- Primary dark: `--tl-primary-dark`
- Accent: `--tl-accent`
- Background: `--tl-bg`
- Surface: `--tl-surface`
- Text: `--tl-text`
- Muted text: `--tl-muted`
- Border: `--tl-border`

Do not create pages dominated by a single colour family. Use neutral surfaces
with primary CTAs and restrained accent states.

## Typography

- Use the base system font stack from `theme.css`.
- Use clear, practical headings.
- Avoid oversized headings inside cards.
- Use `.tl-eyebrow` for small uppercase context labels.
- Keep body copy short and action-oriented.

## Components

### Buttons

- Primary actions use `.btn.btn-primary`.
- Secondary actions use `.btn.btn-outline-secondary`.
- Destructive actions should be rare and clearly labelled.

### Cards

- Use `.tl-card` for forms, profile details, and future dashboard panels.
- Cards should have consistent radius, border, and shadow.
- Do not nest cards inside cards.

### Forms

- Forms should use `novalidate` and render field-level errors.
- Labels should be visible.
- Help text should use `.form-text`.
- Submit buttons should be full width on narrow account forms.

### Messages

- Use Django messages through `base.html`.
- Success, info, warning, and error states should be visible above page content.

## Template Rules

- Every template must start with `{% extends "base.html" %}` unless there is a
  documented technical reason not to.
- Every page must define `{% block title %}`.
- Primary page content belongs in `{% block content %}`.
- Avoid inline styles.
- Use `theme.css` for reusable visual rules.
- Prefer existing Trackly utility classes over page-specific CSS.

## Current Canonical Files

- `docs/design-system.md`: design rules and product UI principles.
- `templates/base.html`: shared HTML shell, Bootstrap include, navigation,
  messages, and content block.
- `static/css/theme.css`: Trackly theme variables, component styling, and layout
  utilities.

## References

- Huntr job tracker product page: https://huntr.co/product/job-tracker
