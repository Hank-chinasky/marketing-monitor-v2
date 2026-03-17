# Sprint 1–2 Scope/Auth Reference Implementation (Django)

This folder contains a **small, server-side enforced** reference implementation for **Sprint 1–2** authorization,
scope filtering, and a handful of canonical validations.

## Canon (Sprint 1–2)
- **Auth model:** standard Django `User` (no custom user model assumed).
- **Identity split:**
  - `User` = authentication identity
  - `Operator` = operational identity
  - `User` links to `Operator` via a single fixed relation: `user.operator_profile`
- **Admin detection:** active internal user AND (`user.is_staff` or `user.is_superuser`)
- **Active internal user:** `user.is_authenticated` and `user.is_active`
- **Scope source (the only one):** active, valid `OperatorAssignment`
- **Non-scope field:** `Creator.primary_operator` is **not** a permission source (label/fallback only).
- **Sprint 1–2 UI rights:**
  - Admin: full access; UI writes allowed
  - Operator: **scoped read-only** in UI (no writes in this reference)
  - Deletes happen later via Django admin

## Assignment window semantics (Sprint 1–2)
Assignments define a visibility window that is **start-inclusive and end-exclusive**:

- Active if `starts_at <= now`
- And `ends_at` is either NULL (open-ended) **or** `ends_at > now`

In interval notation: **[starts_at, ends_at)**.

## Assignment overlap rule (Sprint 1–2)
Overlapping assignment windows for the **same creator** are **not allowed**, even across different operators.
This makes scope deterministic and prevents accidental multi-operator scope overlap.

## Expected model fields / relations
This reference assumes the following relations/fields exist:

- `Operator.user` (OneToOne to `User`, with `related_name="operator_profile"`)
- `Creator.primary_operator` (ForeignKey to `Operator`, NOT used for scope)
- `Creator.display_name` (str)
- `Creator.status` (str), with `'active'` meaning operationally active
- `Creator.consent_status` (str), with `'active'` meaning active consent
- `CreatorChannel.creator` (ForeignKey to `Creator`)
- `CreatorChannel.platform` (str)
- `CreatorChannel.handle` (str)
- `CreatorChannel.access_mode` (str) (required at creation)
- `CreatorChannel.status` (str)
- `OperatorAssignment.operator` (ForeignKey to `Operator`)
- `OperatorAssignment.creator` (ForeignKey to `Creator`)
- `OperatorAssignment.starts_at` (datetime)
- `OperatorAssignment.ends_at` (datetime, nullable)

If your project uses different names, keep **canon semantics** and adjust imports/field names in
these reference files.

## Files
- `core/authz.py`: single source of truth for scope/auth helpers
- `core/mixins.py`: small CBV mixins to enforce admin-only and scoped querysets
- `core/validators.py`: Django-concrete validation helpers for Sprint 1–2 invariants
- `core/tests/test_scope.py`: regression tests for canon scope semantics
