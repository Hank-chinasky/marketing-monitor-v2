# DECISION_LOG_v1 — V2.0 Sprint 1–2 Canon

**Status:** Canonical (Sprint 1–2)  
**Applies to:** `SPRINT_1_2_BUILDER_BRIEFING.md` scope only  
**Last updated:** 2026-03-17

## 0. Purpose

Freeze the **non-negotiable build decisions** for Sprint 1–2 so builders do not invent scope, permissions, or semantics.

If a builder request conflicts with this document, **this document wins** (unless Startdocument/SPEC-1 explicitly overrides, see §9).

---

## 1. Sprint 1–2 scope boundary

### In scope (build now)

- auth / login
- users
- operators
- creators
- creator_channels
- operator_assignments
- basic creator detail page

### Explicitly out of scope (do not build now)

- dashboard
- content queue
- publish log
- tracking links
- traffic events
- results
- operator time entries
- access audit
- bonus/payout/backoffice/customer access/multi-tenant/automation/scheduler/DM/asset library/AI/LinkedIn

**Rule:** don’t “half-build” out-of-scope modules (no placeholder apps/models/screens).

---

## 2. Architecture stance (Sprint 1–2)

**D001 — Monolith, server-rendered, Django-first.**  
No SPA + API-first split. Use framework standards (auth/sessions/CSRF/forms/ORM/admin/migrations).  
SQLite is allowed for local dev; keep migrations portable to PostgreSQL.

---

## 3. Identity model (auth vs operations)

**D002 — `User` ≠ `Operator`.**

- `User` = authentication identity (login, role).
- `Operator` = operational domain identity (assignments, performance, costs).

**D003 — Operator ↔ User link is explicit.**

- `Operator.user_id` is **required** and **unique** (1 operator ↔ 1 user).
- Not every user must be an operator (e.g. admin can be “admin-only”).
- No implicit linking via email/username. Ever.

---

## 4. Scope & permissions source of truth

**D004 — `operator_assignments` is the only permission source.**

- An operator may **only** see records when there is an **active, valid assignment** for that creator.
- Scope must be enforced in the **queryset/view layer** (not “hide links”).

**D005 — `primary_operator` is NOT a permission source.**

- `primary_operator` is a **default responsibility label** only.
- It may be used later for KPI attribution fallback (see D008), but never for access.

---

## 5. Sprint 1–2 authorization policy (builder-proof)

**D006 — Sprint 1–2 is conservative: operator UI is read-only.**

- **Admin:** full CRUD within Sprint 1–2 objects.
- **Operator:** **scoped READ only** in the UI.
- **Operator writes:** only if explicitly required (none required in current Sprint 1–2 brief).

### Authorization matrix (Sprint 1–2)

| Object | Admin | Operator (in scope) | Operator (out of scope) |
|---|---|---|---|
| Users | CRUD **via Django Admin only** | – | – |
| Operators | CRUD (UI allowed) | – *(no Operators screen for operators)* | – |
| Creators | CRUD | R (only assigned creators) | – |
| Creator Channels | CRUD | R (only channels of assigned creators) | – |
| Operator Assignments | CRUD (admin-only management) | R (only own/assigned creators) | – |
| Creator Detail | R/W | R (only assigned creator) | – |

---

## 6. UI edit-flow boundaries (Sprint 1–2)

**D010 — UI edit flows are admin-only.**

- Admin UI includes list/create/update for: Operators, Creators, Channels, Assignments.
- Operator UI has **no create/update/delete flows** in Sprint 1–2.
- Deletes happen via Django Admin (framework-admin).

---

## 7. KPI attribution decision (decide now, build later)

**D008 — Operator attribution rule v1 (for Results/Dashboard later).**

When a metric needs an `operator_id`:

1. If there is an explicit `publish_event.operator_id` → use it.
2. Else fallback to `creator.primary_operator_id`.
3. Else `operator_id = null`.

**Note:** this is a product/KPI decision. Implementation is deferred (Sprint 5–7).

---

## 8. Validation strategy (practical enforcement)

**D009 — Layered enforcement (Django-concrete).**

Enforcement order:

1. Form validation (UI).
2. `Model.clean()` / model-level validation.
3. DB constraints **where feasible** (stronger later with PostgreSQL).

Sprint 1–2 must at least enforce:

- `consent_status` required; active creator cannot exist without valid consent.
- `access_mode` required on channels.
- scope filtering/authorization on every query.
- prevent duplicate `(platform, handle)` conflicts (normalize/case-insensitive strategy decided in implementation).

---

## 9. Document hierarchy (conflict rule)

If documents conflict:

1. **Startdocument** wins on **scope/product boundaries**.
2. **SPEC-1** wins on **technical modeling & implementation**.
3. This Decision Log is the **Sprint 1–2 canonical interpretation layer** to remove ambiguity.

---

## 10. Change control

Any change requires:

- new decision id or updated decision with rationale
- version bump (`DECISION_LOG_vX`)
- explicit note of what builders must change
