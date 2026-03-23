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
- documented decision: content intake modeled as source-based metadata on `Creator`

##2026-03-22 — creatorworkboard ops deployment stabilized
- compose drift verwijderd
- container healthcheck gefixt
- traefik routing bevestigd
- traefik auth hersteld
- main op VPS gelijkgetrokken

## [Unreleased]

### Fixed
- Fixed Docker healthcheck behavior for the ops app so the container becomes healthy behind Traefik and HTTPS redirect handling.
- Fixed Traefik routing for `ops.creatorworkboard.com`.
- Restored Traefik basic authentication for the ops environment.
- Fixed browser login flow by correcting the referrer policy that caused Django CSRF validation to fail.

### Changed
- Updated the Creator Workboard ops deployment to run cleanly on the VPS under Docker and Traefik.
- Standardized live routing and healthcheck behavior for the `creatorworkboard-ops` service.
- Adjusted reverse-proxy behavior so Django login works correctly behind Traefik.

### Added
- Added superuser access for the deployed environment.
- Added operator user accounts and matching `Operator` model records.
- Added the first `Creator` record and linked it to an operator for initial data validation.

### Ops
- Verified migrations, static collection, Gunicorn startup, healthchecks, Traefik labels, and protected access flow.
- Confirmed the full access chain: Traefik auth → Django login → app access.
