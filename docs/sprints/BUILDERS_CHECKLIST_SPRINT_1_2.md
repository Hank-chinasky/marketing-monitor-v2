# BUILDERS_CHECKLIST — Sprint 1–2 (V2.0 Marketing Monitor)

This document is the build contract for Sprint 1–2.
If something is not explicitly listed here, it is out-of-scope.

## 0) Scope (hard)

### In scope (ONLY)
- auth / login
- users
- operators
- creators
- creator_channels
- operator_assignments
- base Creator Detail page

### Explicitly out of scope (DO NOT BUILD)
- dashboard
- content queue
- publish log
- tracking links
- traffic events
- results
- operator time entries
- access audit
- bonus/payout/backoffice
- customer access, public registration
- multi-tenant SaaS
- automation/scheduler
- DM tools, asset library, AI features

Guardrail: **do not "half-prepare" out-of-scope modules**.

## 1) Object contract (models + validations)

> Naming below is canonical for Sprint 1–2. If your code uses different names, add an alias layer and keep semantics identical.

### 1.1 User (auth identity)
Required fields (minimum):
- `email` (unique)
- `password` (or hash via Django auth)
- `role` ∈ {`admin`, `operator`}
- `status` ∈ {`active`, `inactive`}

Rules:
- Only `status=active` may log in.
- No public registration.
- No creator/channel credentials are stored.

### 1.2 Operator (operational identity)
Required fields (minimum):
- `user` (OneToOne to User, REQUIRED, UNIQUE)  ← explicit mapping (no email linkage)
- `name`
- `status` ∈ {`active`, `inactive`}
Optional:
- `hourly_cost`
- `notes`

Rules:
- `Operator.user` is REQUIRED + UNIQUE.
- Operator authorization is derived from: `user.role` + active assignments (NOT from email).

### 1.3 Creator
Required:
- `display_name`
- `status` ∈ {`active`, `paused`, `offboarded`}
- `consent_status` ∈ {`pending`, `active`, `revoked`}
Optional:
- `primary_operator` (FK to Operator, nullable)
- `notes`

Rules:
- If `status='active'`, then `consent_status` MUST be `'active'`.
- `primary_operator` is a label/default owner; **never** a scope/permissiebron.

### 1.4 CreatorChannel
Required:
- `creator` (FK)
- `platform` ∈ {`instagram`, `tiktok`, `telegram`, `other`}
- `handle`
- `status` ∈ {`active`, `paused`, `restricted`, `banned`}
- `access_mode` ∈ {`creator_only`, `operator_with_approval`, `operator_direct`, `draft_only`}
Optional:
- `profile_url`
- `recovery_owner` ∈ {`creator`, `agency`, `shared`}
- `risk_flag` (bool)
- `notes`

Rules:
- Each channel belongs to exactly one creator.
- Prevent or gracefully handle duplicate `(platform, handle)` (case-insensitive is recommended).
- `access_mode` is required.

### 1.5 OperatorAssignment (scope source of truth)
Required:
- `operator` (FK)
- `creator` (FK)
- `scope` ∈ {`full_management`, `posting_only`, `draft_only`, `analytics_only`}
- `starts_at` (datetime/date)
- `ends_at` (nullable)
- `active` (bool)

Rules:
- Operator may only view/work within *active + date-valid* assignments.
- For Sprint 1–2: validate overlapping assignments for the same (operator, creator) if undesired:
  - recommended: disallow >1 overlapping active assignment per (operator, creator).

## 2) Authorization contract (Sprint 1–2)

### Roles
- Admin: full CRUD within Sprint 1–2 objects.
- Operator: **scoped read-only** (Sprint 1–2 UI has no operator edits).

### Scope definition
An operator has access to a creator if there exists an assignment with:
- `active=True`
- `starts_at <= now`
- `ends_at is NULL OR ends_at >= now`

Scope must be enforced **server-side** in the queryset/view layer (not by hiding links).

## 3) Screens (server-rendered) — MUST/ MUST NOT

### MUST exist (Sprint 1–2)
1) Login
2) Admin: Operators (CRUD)
3) Admin: Creators (CRUD)
4) Admin: Channels (CRUD via Creator Detail or Channel list)
5) Admin: Assignments (CRUD)
6) Creator Detail (base page)
7) Operator: Creators list (scoped)
8) Operator: Creator Detail (scoped, read-only)
9) Operator: Assignments list (scoped, read-only) — optional screen, but data must be visible somewhere

### MUST NOT exist (Sprint 1–2)
- any UI for Users management (use Django admin / seed scripts only)
- any audit UI
- any dashboard/metrics/results/tracking UI
- any operator edit flows

## 4) Acceptance criteria (Sprint 1–2)

### Auth
- Active user can log in; inactive user cannot.
- CSRF/session use Django defaults.

### Admin flows
- Admin can create/update/delete: Operators, Creators, Channels, Assignments.
- Admin can view Creator Detail page with channels + assignments.

### Operator flows (read-only)
- Operator sees ONLY creators/channels/assignments inside scope.
- Direct URL access to out-of-scope objects returns 404 (preferred) or PermissionDenied.
- Operator cannot create/update/delete any Sprint 1–2 objects via UI routes.

### Data integrity
- Consent rule enforced: Creator cannot be `active` unless consent is `active`.
- Assignment validity enforced by `active + date window`.
- Duplicate channel (platform, handle) is prevented or handled predictably.

## 5) Builder PR checklist (paste into PR template)
- [ ] No out-of-scope models, migrations, endpoints, or screens added.
- [ ] Scope enforced in queryset/view layer (not templates).
- [ ] Operator UI is read-only (no write endpoints/routes).
- [ ] Assignment validity uses `active + starts_at/ends_at`.
- [ ] Creator consent rule enforced at validation.
- [ ] Tests cover: admin full access, operator scoped access, operator out-of-scope blocked.

