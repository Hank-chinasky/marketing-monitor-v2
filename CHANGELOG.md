# Changelog

## [Unreleased]

### Fixed
- Fixed Docker healthcheck behavior for the ops app so the container becomes healthy behind Traefik and HTTPS redirect handling.
- Fixed Traefik routing for `ops.creatorworkboard.com`.
- Restored Traefik basic authentication for the ops environment.
- Fixed browser login flow by correcting the referrer policy that caused Django CSRF validation to fail.
- Fixed creator material persistence by storing uploaded media under the persistent `/app/data/media` path.
- Fixed creator material delete flow so admin returns directly to the materials section instead of the top of the creator page.

### Changed
- Updated the Creator Workboard ops deployment to run cleanly on the VPS under Docker and Traefik.
- Standardized live routing and healthcheck behavior for the `creatorworkboard-ops` service.
- Adjusted reverse-proxy behavior so Django login works correctly behind Traefik.
- Replaced the Instagram workspace loose handoff note with a structured session closeout on `CreatorChannel`.
- Promoted risk/policy visibility and launch-first quick actions higher in the Instagram workspace.
- Removed `last_operator_update` and `last_operator_update_at` from the main channel edit form so the workspace structured session becomes the primary operator handoff source.
- Added an admin-only delete action for creator materials on the existing creator detail flow.
- Replaced the duplicate `Open bestand` action with one clear `Bekijk groter` action for previewable materials while keeping non-previewable files accessible through `Open bestand`.
- Returned image preview on creator materials to the in-page popup flow while keeping video preview on the dedicated preview page.

### Added
- Added superuser access for the deployed environment.
- Added operator user accounts and matching `Operator` model records.
- Added the first `Creator` record and linked it to an operator for initial data validation.
- Added structured Instagram workspace session fields on `CreatorChannel` for what was done, next action, blockers, policy-context review, and session timestamp.
- Added `ConversationThread` as an admin-seeded Mara-only workflow thread model with scoped creator anchoring, `source_system` choices, status choices, source-thread uniqueness, and no transcript/runtime fields.
- Added a dedicated creator material preview page for video materials.
- Added an explicit fail-closed Mara conversation workflow profile resolver with hard workflow-only defaults for human approval and context handling.
- Added `BuddyDraft` as a structured conversation draft model with explicit state, risk level, generation source, and human-review-oriented draft semantics.

### Ops
- Verified migrations, static collection, Gunicorn startup, healthchecks, Traefik labels, and protected access flow.
- Confirmed the full access chain: Traefik auth -> Django login -> app access.
- Fixed Docker healthcheck for `creatorworkboard-ops` so the container becomes healthy behind Traefik.
- Restored Traefik routing for `ops.creatorworkboard.com`.
- Restored Traefik basic auth for the ops app.
- Fixed Django login CSRF failure caused by reverse-proxy referrer policy.
- Validated end-to-end access flow: Traefik auth -> Django login -> app access.

### Data
- Added superuser access for the live environment.
- Added operator user accounts and matching `Operator` records.
- Added first `Creator` test record and linked it to an operator.
- Added admin registration for `ConversationThread` so phase 1 threads can be created through Django admin only.

### Tests
- Added Instagram workspace session-discipline tests for required structured save fields, derived legacy summary output, latest-session rendering, risk visibility, launch-first actions, channel-edit form discipline, posting-only save access, and analytics-only denial.
- Updated Instagram workspace tests to use the structured session-closeout contract.
- Updated channel handoff tests to validate the structured session form instead of the legacy loose note field.
- Added `ConversationThread` model tests for CRUD behavior, unique source-thread constraint, choices validation, nullable channel handling, and required creator anchoring.
- Added creator material tests for admin-only delete access, visible delete actions for admins, video preview-page access, anchored post-delete redirects, image-popup rendering, non-previewable file access, and delete denial for scoped operators.
- Added conversation workflow profile tests for Mara defaults and unknown-source fail-closed behavior.
- Added `BuddyDraft` model tests for creation, required thread anchoring, state/risk/source choices, explicit draft-state behavior, and conservative human-attention defaults.

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

## 2026-03-22 — creatorworkboard ops deployment stabilized

- Compose drift verwijderd.
- Container healthcheck gefixt.
- Traefik routing bevestigd.
- Traefik auth hersteld.
- Main op VPS gelijkgetrokken.

## 2026-03-18 — Content intake is modeled as source-based and future-proof

**Decision**  
Content intake is stored as source metadata on Creator, not as a forced internal media-hosting model.

**Why**  
This keeps the current workflow light and legally/operationally simpler, while allowing later transition to internal storage without breaking the domain model.

**Consequence**  
Creator now stores:
- `content_source_type`
- `content_source_url`
- `content_source_notes`
- `content_ready_status`

## 2026-03-18

- Documented decision: content intake modeled as source-based metadata on `Creator`.

### Added
- Added `CreatorMaterial` as a creator-bound internal material model for file uploads used directly in the ops cockpit.
- Added a materials section to creator detail with admin upload support and scoped operator visibility.
- Added app-controlled material opening/download flow for creator materials.

### Changed
- Restricted creator edit and channel edit flows to admin-only access.
- Aligned scope behavior so operators can access assigned creator/channel detail pages but not full edit forms.
- Established creator-bound materials as the first MVP slice for internal operator use before any creator portal or external upload layer.

### Fixed
- Fixed migration dependency for `CreatorMaterial` so it follows the current `core` migration chain and no longer creates multiple migration leaf nodes.
- Fixed scope test expectations to match the chosen product rule: admin manages structure, operator works through scoped operational flows.

### Notes
- Handmatig lokaal gevalideerd: superadmin kan materiaal uploaden, operator binnen scope kan materiaal zien en openen.
- Current UX works functionally but still needs preview-first improvements for image and video materials.

### Added
- Added preview-first creator materials for images and videos on creator detail pages.
- Added simple in-page media viewer for creator material previews.
- Added multi-select upload for creator materials so multiple files can be uploaded in one action.

### Changed
- Changed creator materials upload flow from single-file upload to multi-file upload.
- Improved creator materials UX so images and videos are visually recognizable before opening.
- Kept creator materials attached directly to creators without adding folders or a broader media management layer.

### Validated
- Confirmed locally that multiple files can be selected and uploaded in one submit.
- Confirmed locally that preview-first materials rendering works in the site UI.
- Confirmed locally that scoped operators can still see uploaded materials.
