# Changelog

## 2026-07-21 — Sanitized Send Preview v1 live

### Status

- Sanitized Send Preview v1 is gemerged en live gedeployed.
- Pull request: `#107`
- Feature commits:
  - `390909a` — Add sanitized send preview v1
  - `8eadd0a` — Prevent stale sanitized preview responses
- Merge commit / productiecommit:
  - `e77ecea04ab16464a72b6307fc1fa2e83547da2a`
- Vorige productie- en rollbackcommit:
  - `cad2dbd4fd34a85dcbbb709c71d0678ad9d1c4fe`
- Geen database- of infrastructuurmigratie uitgevoerd.
- Venice blijft uit.
- Echte verzending blijft uit.

### Added

- Nieuwe interne, POST-only previewroute:
  - `/chats/send-preview/`
- Nieuwe `SanitizedSendPreviewView` voor gecontroleerde verzendpreview.
- Server-side sanitizing via de bestaande centrale Contact Data Sanitizer v1.
- Previewpaneel in de Operator Composer met:
  - gesanitiseerde previewtekst;
  - status `Contactgegevens geblokkeerd`;
  - status `Geen contactgegevens gevonden`;
  - gevonden matchtypes voor e-mail en telefoon;
  - expliciete preview-only melding.
- CSRF-beveiligde same-origin JSON-request.
- Maximale previewlengte van 10.000 tekens.
- `Cache-Control: private, no-store`.
- Fail-closed responseveld:
  - `send_available: false`
- Stale-responsebescherming met:
  - `AbortController`;
  - annuleren van een lopende previewrequest bij tekstwijziging;
  - controle dat de response nog bij de actuele tekst hoort.

### Changed

- De bestaande knop `Verzenden (demo)` maakt nu uitsluitend een veilige preview.
- De oorspronkelijke tekst in het antwoordveld blijft ongewijzigd.
- De preview verdwijnt zodra de operator de concepttekst wijzigt.
- De bestaande kopieeractie blijft buiten deze slice ongewijzigd.
- Er wordt exact één interne fetch uitgevoerd per previewklik.

### Guardrails

- Geen echte verzending.
- Geen automatische actie.
- Geen bronadapter of writeback.
- Geen Chatties- of Eurotikken-aanroep.
- Geen databaseopslag van de preview.
- Geen modelwijzigingen.
- Geen migrations.
- Geen settings- of env-wijzigingen.
- Geen providerwijziging.
- Demo-viewers blijven read-only.
- Menselijke controle blijft verplicht.

### Files changed

- `core/send_preview_views.py`
- `core/urls.py`
- `templates/chats/_buddy_reply_focus.html`
- `core/tests/test_sanitized_send_preview_v1.py`
- `core/tests/test_buddy_reply_focus_v1.py`

### Tested

- 24 gerichte tests:
  - OK
- Volledige testsuite:
  - 382 tests OK
- Django system check:
  - geen issues
- Migration drift check:
  - `No changes detected`
- Handmatige browsercontrole:
  - contactgegevens worden gemaskeerd;
  - datum, tijd en ordernummer blijven intact;
  - preview verdwijnt na tekstwijziging;
  - één interne `POST /chats/send-preview/`;
  - status `200`;
  - geen externe request zichtbaar.

### Deploy

- Productiecommit:
  - `e77ecea04ab16464a72b6307fc1fa2e83547da2a`
- Container:
  - `creatorworkboard-ops-web-1`
  - status `healthy`
- Interne healthcheck:
  - `200`
- Publieke healthcheck zonder Basic Auth:
  - `401`
- Migrations:
  - geen
- Venice:
  - uit
- Echte verzending:
  - uit

### Rollback and backup

- Rollback image:
  - `creatorworkboard-ops-rollback:cad2dbd-20260721T214337Z`
- Databasebackup:
  - `/opt/commandcenter/backups/creatorworkboard-ops/db-predeploy-20260721T214118Z-cad2dbd.sqlite3`
- Databasebackup SHA-256:
  - `cb2beb53abb4700f26e514a56b24450bb3828f1ca0aaaa08ad707f63a1ec0912`
- Deploymanifest:
  - `/opt/commandcenter/backups/creatorworkboard-ops/deploy-20260721T214337Z-e77ecea.txt`

### Operational note

- Twee eerdere deploypogingen stopten vóór de live containerswitch:
  - eerst omdat Django settings niet waren geïnitialiseerd;
  - daarna omdat ten onrechte `config.settings` werd gebruikt.
- De repository en live container bleven tijdens beide mislukte pogingen ongewijzigd.
- De definitieve backup werd veilig gemaakt via `python manage.py shell`, waardoor de werkelijke settingsmodule `marketing_monitor.settings` werd gebruikt.
- De uiteindelijke deploy is daarna volledig geslaagd zonder rollback.

## 2026-05-31 — Buddy draft quality v1 live

### Status

- Buddy draft quality v1 is live.
- Final live commit: `1779b54`.
- Rollback anchor: `961a0ef`.
- Deploy type: app-only.
- No rollback required.
- No further VPS actions now.

### Changed

- Improved deterministic Buddy reply draft quality inside the existing service boundary.
- Added structured draft quality fields:
  - `missing_context_note`
  - `tone_note`
- Changed newly generated draft source from `deterministic_stub` to `deterministic_quality_v1`.
- Improved deterministic language detection for:
  - Dutch / `nl`
  - German / `de`
  - English / `en`
  - Portuguese / `pt`
- Switched language detection to marker scoring to avoid simple ordering conflicts.
- Updated safety notes to English-first wording.
- Kept existing `latest_buddy_draft` behavior read-only behind the same service boundary.

### Guardrails

- No model changes.
- No migrations.
- No settings/env changes.
- No URL changes.
- No template changes.
- No Docker/Compose config changes.
- No Traefik changes.
- No external AI/API calls.
- No provider registry.
- No send/reply/post action.
- No auto-send/autopilot behavior.
- No background worker.
- No training/vector/import flow.

### Tested

- `python manage.py test core.tests.test_buddy_reply`
  - 9 tests OK
- Targeted shared-core Buddy draft rendering test
  - OK
- Full test suite
  - 242 tests OK
- `python manage.py makemigrations --check --dry-run`
  - No changes detected

### Deploy verification

- VPS app repo updated to `1779b54`.
- Container healthy.
- Docker healthcheck returned `200`.
- Django check OK.
- `makemigrations --check` clean.
- Migrations applied through `core.0017`.
- Public anonymous `/` returned expected `HTTP/2 401 Basic Auth`.
- Public anonymous `/healthz/` returned expected `HTTP/2 401 Basic Auth`.
- TLS and Traefik routing/auth confirmed.
- No rollback required.

### Browser/functionality smoke

- Functional smoke OK.
- `/chats/` opens.
- ConversationMessage panel remains live.
- Buddy draft quality v1 visible within the read-only Buddy boundary.
- No send/reply/post/autopilot action visible or executable.
- Deploy accepted.
- No further VPS actions now.

### Deploy note

Public curl immediately after `docker compose up` may briefly return `404` while Traefik re-detects the replaced container.

Public smoke is only decisive after the web container is healthy.

Expected anonymous public response remains `HTTP/2 401 Basic Auth`.


## [Unreleased] — main, not deployed

### Added

- Added `ConversationMessage` as a stored, read-only message context model for Chats Workspace v1.
- Added migration `core.0017_conversation_message`.
- Added `ConversationMessage` admin registration for admin-only inspection/management.
- Added a read-only `Berichtcontext` panel to `/chats/` for the selected `ConversationThread`.
- Added empty-state rendering when a selected thread has no stored messages.
- Added tests for:
  - `ConversationMessage` defaults and required body validation;
  - direction choice validation;
  - message ordering by `occurred_at`, `id`;
  - `/chats/` rendering only messages from the selected scoped thread;
  - no message add/send form in the Chats panel.

### Technical details

- `ConversationMessage` is linked to `ConversationThread` with `related_name="conversation_messages"`.
- Message visibility in `/chats/` is loaded only through:

```python
selected_thread.conversation_messages.order_by("occurred_at", "id")
```

- The read-only panel does not introduce a write flow, send/reply action, import API, webhook, background worker, livechat sync, embedded chatclient, attachment handling, raw payload storage, metadata field, or Buddy posting/decisioning.
- The scope boundary remains the already-scoped `selected_thread`.

### Verification

Local proof before merge:

```text
Targeted tests: 64 OK
Full test suite: 231 OK
makemigrations --check --dry-run: No changes detected
```

Merge result:

```text
PR #60 merged
Target on main: 14d6593
Commit: Add conversation message read-only panel (#60)
```

### Deploy status

```text
Not deployed.
No VPS action performed.
No live migration performed.
Migration-aware deploy gate required before live deployment.
```

### Guardrails

- No `forms.py` changes.
- No `urls.py` changes.
- No `conversation_views.py` changes.
- No settings changes.
- No `.env` changes.
- No Docker/Compose changes.
- No Traefik changes.
- No livechat API.
- No realtime sync.
- No import/webhook/background worker.
- No send/reply action.
- No operator message create/update flow.
- No Buddy posting or Buddy decisioning.

## 2026-05-14 — Chats manual thread intake live on top of Buddy prefill

### Added

- Added manual `ConversationThread` intake for Chats Workspace v1.
- Added scoped manual create/edit views for conversation threads:
  - `/conversations/create/`
  - `/conversations/<pk>/edit/`
- Added `ConversationThreadForm` with scoped creator and channel querysets.
- Added `conversation_thread_form.html`.
- Added create/edit links to conversation thread list/detail pages.
- Added tests for manual thread intake access, scoped operators, admin access, unsupported authenticated accounts, anonymous access, out-of-scope creators/channels and wrong-creator channel validation.

### Context

- Buddy context prefill was already live at rollback anchor `ab7327e`.
- This deploy moved live from `ab7327e` to `4272843`.
- Deploy range: `ab7327e..4272843`.
- Included in this deploy range:
  - `#52` Manual conversation thread intake
  - `#53` Deploy preflight docs

### Changed

- Improved Chats Workspace support for manual thread creation and correction without introducing external chat integration.
- Kept all manual thread intake within existing scoped creator/channel access rules.

### Guardrails

- No model changes.
- No migrations.
- No settings changes.
- No `.env` changes.
- No Docker/Compose changes.
- No Traefik changes.
- No external chat integration.
- No AI/Buddy API.
- No memory/vector/training layer.
- No new product layer.
- No autonomous actions.
- No new permission model.

### Verified

Local before deploy:

```bash
./.venv/bin/python manage.py test
./.venv/bin/python manage.py makemigrations --check --dry-run
```

Result:

```text
Found 220 test(s).
Ran 220 tests in 66.488s
OK
No changes detected
```

VPS after deploy:

```bash
docker compose exec -T web python manage.py makemigrations --check --dry-run
docker compose exec -T web python manage.py check
```

Result:

```text
No changes detected
System check identified no issues (0 silenced).
```

### Deploy result

- Deploy target: `4272843`.
- Rollback anchor: `ab7327e`.
- Deployed service: `creatorworkboard-ops-web-1`.
- Deployment type: app-service only.
- Container status after deploy: healthy.
- Browser smoke checks confirmed.
- No rollback required.
- No further VPS/deploy actions.

## Current shipped baseline — Ops, workspace, materials, conversation and BuddyDraft

### Fixed

- Fixed Docker healthcheck behavior for the ops app so the container becomes healthy behind Traefik and HTTPS redirect handling.
- Fixed Traefik routing for `ops.creatorworkboard.com`.
- Restored Traefik basic authentication for the ops environment.
- Fixed browser login flow by correcting the referrer policy that caused Django CSRF validation to fail.
- Fixed creator material persistence by storing uploaded media under the persistent `/app/data/media` path.
- Fixed creator material delete flow so admin returns directly to the materials section instead of the top of the creator page.
- Fixed conversation thread view tests to accept localized BuddyDraft confidence rendering instead of assuming a dot decimal separator.

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
- Improved the read-only BuddyDraft presentation on conversation detail pages with a clearer draft context block and explicit empty-state messaging.

### Added

- Added superuser access for the deployed environment.
- Added operator user accounts and matching `Operator` model records.
- Added the first `Creator` record and linked it to an operator for initial data validation.
- Added structured Instagram workspace session fields on `CreatorChannel` for what was done, next action, blockers, policy-context review, and session timestamp.
- Added `ConversationThread` as an admin-seeded Mara-only workflow thread model with scoped creator anchoring, `source_system` choices, status choices, source-thread uniqueness, and no transcript/runtime fields.
- Added a dedicated creator material preview page for video materials.
- Added an explicit fail-closed Mara conversation workflow profile resolver with hard workflow-only defaults for human approval and context handling.
- Added `BuddyDraft` as a structured conversation draft model with explicit state, risk level, generation source, and human-review-oriented draft semantics.
- Added a Mara-only Buddy draft stub service that creates conservative operator-facing `BuddyDraft` records with fail-closed source validation.
- Added read-only conversation thread list and detail views with assignment-scoped visibility and latest-draft context rendering.
- Added the first BuddyDraft approval action as a small POST-only workflow step from conversation detail for admin and scoped operators, including approver attribution.

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

### Tests

- Added Instagram workspace session-discipline tests for required structured save fields, derived legacy summary output, latest-session rendering, risk visibility, launch-first actions, channel-edit form discipline, posting-only save access, and analytics-only denial.
- Updated Instagram workspace tests to use the structured session-closeout contract.
- Updated channel handoff tests to validate the structured session form instead of the legacy loose note field.
- Added creator material tests for admin-only delete access, visible delete actions for admins, video preview-page access, anchored post-delete redirects, image-popup rendering, non-previewable file access, and delete denial for scoped operators.
- Added conversation workflow profile tests for Mara defaults and unknown-source fail-closed behavior.
- Added `BuddyDraft` model tests for creation, required thread anchoring, state/risk/source choices, explicit draft-state behavior, and conservative human-attention defaults.
- Added Buddy draft service tests for Mara-only draft creation, deterministic stub defaults, operator assignment passthrough, thread immutability, and fail-closed unsupported-source behavior.
- Added conversation thread view tests for scoped list/detail access, out-of-scope denial, empty-list behavior without active assignment, optional channel handling, and latest-draft detail rendering.
- Added BuddyDraft detail UI tests for read-only latest-draft rendering, empty-state behavior, and preserved scoped detail access.
- Added BuddyDraft approval action tests for scoped access, approved state transition, approver attribution, timestamp updates, drafted-only action visibility, and latest-draft-only approval behavior.

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

- Compose drift verwijderd.
- Container healthcheck gefixt.
- Traefik routing bevestigd.
- Traefik auth hersteld.
- Main op VPS gelijkgetrokken.

## 2026-03-18 — Content intake is modeled as source-based and future-proof

### Decision

Content intake is stored as source metadata on Creator, not as a forced internal media-hosting model.

### Why

This keeps the current workflow light and legally/operationally simpler, while allowing later transition to internal storage without breaking the domain model.

### Consequence

Creator now stores:

- `content_source_type`
- `content_source_url`
- `content_source_notes`
- `content_ready_status`

## 2026-03-18 — Creator materials and source-based content intake

### Added

- Documented decision: content intake modeled as source-based metadata on `Creator`.
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
- Current UX works functionally but still needs preview-first improvements for image and video materials.
- Confirmed locally that multiple files can be selected and uploaded in one submit.
- Confirmed locally that preview-first materials rendering works in the site UI.
- Confirmed locally that scoped operators can still see uploaded materials.

## 2026-04-24 — Feeder Workspace v1 scan-context

### Status

- Live bevestigd op 2026-04-24 als kleine Feeder Workspace v1-verdiepingsslice.
- De slice bleef binnen de bestaande Mara Ops-lijn: shared core → chats → feeder → templates/approvals → buddy.

### Added

- Added compact Feeder scan context in `FeederHubView` for:
  - feeder focus
  - latest feeder handoff
  - next operator action
  - Chats handoff scan
- Added a compact Feeder scan block to `templates/feeder/feeder_hub.html`.
- Added regression coverage for Feeder scan context in `core/tests/test_shared_core_v1_views.py`.

### Changed

- Improved Feeder Workspace scanability inside the existing 3-pane shell.
- Made current focus, handoff state, next operator action, and Chats handoff signal easier to read for operators.
- Het operationele middenvlak van **Feeder Workspace v1** maakt nu explicieter zichtbaar:
  - wat live moet
  - wat aandacht nodig heeft
  - content/context vóór actie
  - door naar chats
  - ritme / opvolging
- De wijziging is bewust klein gehouden en blijft binnen de bestaande Feeder Workspace v1-scope.

### Guardrails

- No model changes.
- No migrations.
- No routing/url changes.
- No settings/env changes.
- No Docker/Compose/VPS/deploy changes in the code-slice itself.
- No approvals action logic changes.
- No buddy expansion.
- No docs/changelog files were included in the original code-slice itself; this changelog update documents the slice afterwards.

### Tested

- `python manage.py test core.tests.test_shared_core_v1_views.SharedCoreV1ViewsTests.test_feeder_scan_context_is_present_in_template_and_context`
- `python manage.py test core.tests.test_shared_core_v1_views`
- `python manage.py makemigrations --check`
- `python manage.py test core.tests.test_shared_core_v1_views core.tests.test_approvals_v1`
- Korte runtime/smoke check uitgevoerd op `/feeder/`.
- Korte regressiecheck uitgevoerd op `/chats/`.

### Deploy

- VPS app-repo bevestigd op `/opt/commandcenter/apps/creatorworkboard-ops`.
- VPS `main` bijgewerkt naar de gemergede feeder-slice.
- `web` service opnieuw gebouwd en gestart via de bestaande stackflow.
- Container healthy bevestigd.
- Live bevestigd op basis van uitgevoerde operator smoke check.

## 2026-05-30 — ConversationMessage read-only panel live

### Deploy completion

```text
Deploy completion — ConversationMessage read-only panel

Target deployed:
- 2c6c0c1

Rollback anchor:
- 8f17f2b

Migration:
- core.0017_conversation_message

Result:
- SQLite backup created before migration:
  /app/data/db.sqlite3.bak.before_conversation_message_0017_20260530132449
- Deployment to 2c6c0c1 completed
- Migration applied successfully
- creatorworkboard-ops-web-1 is healthy
- Django check OK
- showmigrations confirms [X] 0017_conversation_message
- makemigrations check clean
- Browser smoke checks passed
- No rollback required

Scope confirmed:
- /chats/ shows read-only Berichtcontext panel
- no send/reply/import/livechat flow
- no operator message create/update flow
- no Buddy posting/decisioning
- no Traefik/.env/Docker/host changes

Conclusion:
- Deploy accepted as live and stable
- No further VPS actions now

```
