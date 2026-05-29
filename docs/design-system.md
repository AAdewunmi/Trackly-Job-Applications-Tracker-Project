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
   Trackly is a Django SaaS MVP for tracking job applications and matching job
   descriptions against target-role profiles using explainable NLP. Use readable
   forms, structured cards, and predictable navigation.

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

## Premium SaaS Visual Direction

Trackly's structure remains its own, but the visual language should move towards
a more premium, data-dense SaaS feel inspired by Prentus's colour confidence and
typography. Trackly must remain a light, approachable job-application tracking
product, not a dark software-engineering dashboard.

### Colour Direction

Use a visible Cool Mist page background with crisp white surfaces, green primary
actions, and violet support accents. Product-heavy sections, dashboard previews,
pricing, and future application-tracking surfaces should look structured and
data-rich without switching the whole product to dark mode.

Recommended tokens:

- Page background: `#c8d2df`
- Background top wash: `#e3e8ee`
- Surface/card background: `#ffffff`
- Soft surface: `#f1f6ef`
- Primary text: `#172033`
- Muted text: `#667085`
- Soft border: `#dfe6dc`
- Strong border: `#c8d5c4`
- Primary green: `#18a058`
- Primary green hover: `#0f7f44`
- Support violet: `#7c5cff`
- Support violet wash: `rgba(124, 92, 255, 0.12)`
- Success green highlight: `#37d99e`

The page background should be visibly Cool Mist, approximately 30% darker than a
near-white mist, so the landing page is distinct from earlier warm/off-white
projects. Use green for primary actions and success states; use violet for
premium emphasis, badges, and subtle radial accents.

### Typography Direction

Use bold, tight, modern headings with clean scannable body text.

- Hero headings: very large, heavy, tight line-height.
- Section headings: large, confident, slightly compressed.
- Card headings: smaller but still bold.
- Body copy: readable, muted, and practical.
- Eyebrows: uppercase, small, letter-spaced, muted.

Suggested scale:

- Hero title: `clamp(3.5rem, 8vw, 6.75rem)`, weight `850`, line-height `0.92`
- Section title: `clamp(2.25rem, 5vw, 4.25rem)`, weight `820`, line-height
  `0.98`
- Card title: `1.2rem`, weight `760`
- Body: `1rem`, line-height `1.65`
- Eyebrow: `0.78rem`, uppercase, letter-spacing `0.08em`

Only use negative letter spacing on large headings.

### Cards And Product Surfaces

Cards should feel like compact product UI, not decorative marketing blocks, while
remaining light and readable.

Use:

- White or near-white raised surfaces.
- Soft but visible borders.
- Subtle inner gradients.
- Compact metrics.
- Status badges.
- Hover lift, clearer border, and a slightly stronger shadow.

Suggested card treatment:

```css
background:
  linear-gradient(135deg, rgba(124, 92, 255, 0.08), transparent 34%),
  linear-gradient(225deg, rgba(24, 160, 88, 0.1), transparent 42%),
  rgba(255, 255, 255, 0.76);
border: 1px solid #dfe6dc;
border-radius: 1.25rem;
box-shadow: 0 20px 45px rgba(23, 32, 51, 0.09);
```

Hover:

```css
transform: translateY(-3px);
border-color: #c8d5c4;
box-shadow: 0 18px 42px rgba(23, 32, 51, 0.11);
```

### Badges And Labels

Use pill badges to make product states scannable.

Examples:

- `AI-ready`
- `Pipeline`
- `Interview prep`
- `Free`
- `Pro`
- `Follow-up due`
- `Remote`
- `Hybrid`

Badge style:

- Rounded pill.
- Light translucent background.
- Soft border.
- Small bold text.
- Accent variants for success, warning, and active states.

### Buttons

Primary CTAs should feel confident and high contrast.

Use:

- Primary button: green gradient.
- Secondary button: white or translucent with soft border.
- Rounded pill shape.
- Strong hover states.

### Layout Density

Keep Trackly's current landing-page structure, but make future sections more
data-rich:

- Dashboard previews should include metrics, rows, statuses, and mini cards.
- Feature sections should avoid vague marketing copy.
- Case-study or proof sections should use numbers prominently.
- FAQ sections should use clean accordion rows with subtle dividers.
- Footer should stay structured and multi-column.

### Design Boundary

Trackly may borrow Prentus's premium SaaS principles, but must not copy Prentus's
exact layout, wording, brand assets, screenshots, logos, or component
composition.

## Colour

Trackly uses a clean light theme with a visible Cool Mist page background, green
primary actions, violet support accents, and crisp white surfaces.

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

### Dashboard Navigation

- User dashboards should use `.tl-dashboard-page` for the two-column shell.
- Use `.tl-dashboard-side-nav` for in-page dashboard navigation.
- Sidebar links use `.tl-dashboard-side-link`; the current section uses
  `.tl-dashboard-side-link-active`.
- Place the page heading above `.tl-dashboard-page`; the sidebar should align
  with the dashboard cards and stretch to the end of the dashboard content.
- Keep sidebar destinations focused on frequent user workflows such as pipeline,
  applications, metrics, insights, empty state, and profile.
- On mobile, dashboard side navigation should stack above content and use compact
  grid links rather than hiding navigation.

### Forms

- Forms should use `novalidate` and render field-level errors.
- Labels should be visible.
- Help text should use `.tl-help-text`.
- Errors should use `.tl-field-error`.
- Submit buttons can use `.tl-button-full` on account forms.

### Tables and Lists

- Data-dense list pages should use `.tl-panel` with `.tl-table-wrap` and
  `.tl-table` when users need to compare multiple records.
- Table links should use `.tl-table-link`; row actions should use existing
  `.tl-button` variants.
- Keep empty states useful: explain what is missing, why it matters, and provide
  one primary action such as adding the first application.
- Use badges for scannable status values rather than plain status text.

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
