# Changelog

## [Unreleased]

### Fixed
- Fixed Docker healthcheck behavior for the ops app so the container becomes healthy behind Traefik and HTTPS redirect handling.
- Fixed Traefik routing for `ops.creatorworkboard.com`.
- Restored Traefik basic authentication for the ops environment.
- Fixed browser login flow by correcting the referrer policy that caused Django CSRF validation to fail.
- Restored the missing `creator-material-bulk-delete` route after the opportunity queue URL update.
- Removed an invalid `OperatorAssignmentReactivateView` import from `core/urls.py` to stop the web container restart loop.

### Changed
- Updated the Creator Workboard ops deployment to run cleanly on the VPS under Docker and Traefik.
- Standardized live routing and healthcheck behavior for the `creatorworkboard-ops` service.
- Adjusted reverse-proxy behavior so Django login works correctly behind Traefik.
- Added paginated rendering for the admin-seeded V1 opportunity queue.
- Kept opportunity creation outside app flow in V1; records can be created through Django admin.

### Added
- Added superuser access for the deployed environment.
- Added operator user accounts and matching `Operator` model records.
- Added the first `Creator` record and linked it to an operator for initial data validation.
- Added `ProfileOpportunity` in `core/` for small admin-seeded intake, scoring, handoff and queue handling.
- Added `OutcomeEntry` with fixed outcome choices for minimal per-opportunity outcome logging.
- Added opportunity queue and detail views with small server-rendered templates.
- Added a server-side scoring service for `priority_band` and `action_bucket`.

### Documentation
- Aligned strategic and technical markdown files with the current deployed state, the admin-seeded V1 opportunity flow, and the next live proof sprint in Mara’s chat environment.
- Clarified that the internal route can include social intake, while the first paid wedge remains limited to the workflow control layer.

### Ops
- Verified migrations, static collection, Gunicorn startup, healthchecks, Traefik labels, and protected access flow.
- Confirmed the full access chain: Traefik auth -> Django login -> app access.
- Rebuilt and restarted the `creatorworkboard-ops` web container after the opportunity queue URL fix.
- Validated live access to `/opportunities/` after the rebuild.

### Tests
- Added tests for opportunity scoring rules, override validation, scoped visibility, queue ordering, and queue pagination.
- Re-ran the full Django test suite on the VPS after the URL fix; 102 tests passed.

## 2026-03-25 — Ticket 1 assignment-scoped operational access

### Changed
- Added central assignment scope helpers in `core/services/scope.py`.
- Patched creator list/detail/edit views to use assignment-scoped querysets.
- Patched channel list/detail/edit views to use assignment-scoped querysets.
- Scoped operations dashboard data to the same assignment-based access rules.
- Removed `primary_operator` from authorization decisions.
- Kept admin breadth via existing `is_staff` / `is_superuser` semantics.

### Added
- Added scope tests for assignment windows, object access, dashboard behavior, and delete admin-only mixin behavior.

### Notes
- Confirmed `ends_at == now` is tested with a fixed patched clock to avoid flakiness.
- No model changes.
- No migrations.
- No connector or auth framework changes.

## 2026-03-22 — CreatorWorkboard ops deployment stabilized

### Changed
- Compose drift verwijderd.
- Container healthcheck gefixt.
- Traefik routing bevestigd.
- Traefik auth hersteld.
- Main op VPS gelijkgetrokken.

## 2026-03-18 — Content intake is modeled as source-based and future-proof

### Decision
Content intake is stored as source metadata on `Creator`, not as a forced internal media-hosting model.

### Why
This keeps the current workflow light and legally/operationally simpler, while allowing later transition to internal storage without breaking the domain model.

### Consequence
`Creator` now stores:
- `content_source_type`
- `content_source_url`
- `content_source_notes`
- `content_ready_status`

## 2026-03-18 — Creator materials MVP

### Added
- Added `CreatorMaterial` as a creator-bound internal material model for file uploads used directly in the ops cockpit.
- Added a materials section to creator detail with admin upload support and scoped operator visibility.
- Added app-controlled material opening/download flow for creator materials.
- Added preview-first creator materials for images and videos on creator detail pages.
- Added simple in-page media viewer for creator material previews.
- Added multi-select upload for creator materials so multiple files can be uploaded in one action.

### Changed
- Restricted creator edit and channel edit flows to admin-only access.
- Aligned scope behavior so operators can access assigned creator/channel detail pages but not full edit forms.
- Established creator-bound materials as the first MVP slice for internal operator use before any creator portal or external upload layer.
- Changed creator materials upload flow from single-file upload to multi-file upload.
- Improved creator materials UX so images and videos are visually recognizable before opening.
- Kept creator materials attached directly to creators without adding folders or a broader media management layer.

### Fixed
- Fixed migration dependency for `CreatorMaterial` so it follows the current `core` migration chain and no longer creates multiple migration leaf nodes.
- Fixed scope test expectations to match the chosen product rule: admin manages structure, operator works through scoped operational flows.

### Validated
- Handmatig lokaal gevalideerd: superadmin kan materiaal uploaden, operator binnen scope kan materiaal zien en openen.
- Confirmed locally that multiple files can be selected and uploaded in one submit.
- Confirmed locally that preview-first materials rendering works in the site UI.
- Confirmed locally that scoped operators can still see uploaded materials.

### Notes
- Current UX works functionally but still needs preview-first improvements for image and video materials.
