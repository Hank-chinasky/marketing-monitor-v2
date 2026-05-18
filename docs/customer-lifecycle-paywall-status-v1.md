# Customer lifecycle / paywall status v1 — scope lock

## Status

Docs-only decision lock. No code, no migration, no deploy.

## Problem

Operators need to know whether a creator/contact is a lead, outside paywall, inside paywall, former customer, or blocked/do-not-contact.

Without this, manual conversation intake can capture threads, but customer context remains inconsistent.

## Decision

V1 uses one field on `Creator`:

```text
customer_stage
```

V1 does not introduce a separate `paywall_status`.

## Why Creator, not ConversationThread

Customer/paywall stage describes the creator/customer relationship, not one individual thread.

Conversation threads may reference the status, but they should not own it.

## V1 choices

```text
unknown
lead
outside_paywall
inside_paywall
former_customer
blocked_do_not_contact
```

## Meaning

- `unknown`: status not reviewed yet.
- `lead`: potential customer/contact, not clearly inside or outside paywall.
- `outside_paywall`: known contact/customer context, currently outside paid/paywall environment.
- `inside_paywall`: active inside paid/paywall environment.
- `former_customer`: was customer before, not currently active.
- `blocked_do_not_contact`: do not contact or high-risk contact restriction.

## Default

Existing creators default to:

```text
unknown
```

## Operator rules

Operators may see customer stage inside their existing scoped creator access.

Operators may update customer stage only if the later code-slice explicitly allows it within scoped creator access.

Admin may manage customer stage broadly.

## Buddy rules

Buddy may only show `customer_stage` read-only as existing context.

Buddy must not:

- determine customer stage
- change customer stage
- recommend status changes
- automate lifecycle decisions

## V1 UI candidates

Possible later code-slice:

- show on creator detail
- show in conversation intake form/context
- show in `/chats/` context
- optionally show in dashboard cards or quick access

## Not in V1

- separate `paywall_status`
- `returning_customer`
- `active_customer` as separate from `inside_paywall`
- lifecycle history
- audit trail
- automatic status inference
- chat integration
- Buddy decisioning
- external API
- migration before approval

## Expected later code impact

Likely files in later code-slice:

```text
core/models.py
core/forms.py
core/views.py
core/admin.py
templates/...
core/tests/...
migration
```

No code is approved by this document.

## Acceptance before code

Code-slice may only start after Architect + Stack Guardian approve:

- field location
- choices
- default
- who can view/edit
- migration plan
- tests
- UI locations
