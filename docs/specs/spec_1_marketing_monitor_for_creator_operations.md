# SPEC-1 — CreatorWorkboard Connection-Board for Conversion Operations

> Note: the filename of this document still reflects the older repository structure. The product truth does not. This SPEC is now aligned to CreatorWorkboard as a human-controlled connection-board for conversion operations.

## Background

CreatorWorkboard is no longer defined primarily as a marketing monitor.

It is defined as a human-controlled connection-board for creator conversion operations.

The problem being solved is not "how do we automate marketing" and not "how do we build a new chat first".

The problem is:

- conversation-driven conversion work happens across scattered external environments
- operators lose context between shifts, creators and systems
- outside-paywall and inside-paywall work is poorly connected
- next action, handoff, routing and ownership are often unclear
- risk, policy and access context are often discovered too late

The system therefore exists to make human-operated conversion work manageable, transferable and measurable without replacing the existing transport layer too early.

## Product rule

**This system exists to make human-controlled creator conversion operations manageable, transferable and operationally clear — not to automate conversations or replace operators.**

## Scope rule

**Any feature that does not directly improve context, routing, handoff, assignment clarity, next action or operational decision-making does not belong in the current core.**

## Core product stance

CreatorWorkboard is:

- control-first
- context-first
- routing-first
- handoff-first
- human-in-the-loop
- connector-oriented

CreatorWorkboard is not, in the current phase:

- a new inbox as the primary product
- a DM-bot
- an autonomous AI conversation engine
- a broad OF/Fansly suite
- a full backoffice platform
- a broad analytics-first dashboard product
- a generic CRM
- a creator password vault

## Current product core

The system must make it possible to:

1. structure creators, channels, operators and assignments
2. connect work to the correct creator/channel route
3. make outside-paywall and inside-paywall state visible
4. keep handoff, acknowledgement and next action explicit
5. let operators work from context before action
6. connect to existing chat environments without rebuilding them first

## Requirements

### Must have

- Admin can manage all creators, channels, operators, assignments, connection cards, handoffs and acknowledgements.
- Operator can only access records within active assignments and valid scope.
- Every operational work unit must belong to a creator and must be attributable to a route, source or channel context.
- A creator must have a status and consent status; an active creator without valid consent is not allowed.
- A channel must carry operational access and policy context.
- A connection card must represent the controllable work unit around a conversation-driven conversion flow.
- A connection card must support outside-paywall / inside-paywall state.
- A connection card must support explicit routing state and assignee state.
- A connection card must support external thread reference(s) without requiring CreatorWorkboard to own the conversation transport.
- A handoff must be writable and visible in the workspace context.
- An acknowledgement must record that a user has explicitly seen the current handoff/context before proceeding where required.
- The system must show source context, risk context, access policy and next action before execution.
- The system must not store creator or channel passwords.
- Governance-sensitive changes must be lightly logged.
- Existing external chat systems must be connectable by reference even before deep integration exists.

### Should have

- Operators should be able to move through work from one workspace without reconstructing context from multiple tools.
- Routing state should make it clear whether work is outside-paywall, inside-paywall, creator input needed, operator follow-up or blocked.
- Source context should be consistent across creator, channel and connection card layers.
- Workspaces should support creator materials and other contextual references as supporting inputs.
- A lightweight event timeline should support latest actions per connection card.
- Admins should be able to see where handoff is missing, acknowledgement is missing or routing is unclear.

### Could have

- Assisted AI summaries for handoff or source context.
- Assisted AI labeling or prioritisation for connection cards.
- Connector-specific enrichment for external systems.
- Lightweight operational metrics such as queue age, stalled cards and acknowledgement lag.

### Won’t have in the current phase

- autonomous messaging
- AI-generated conversation flows as the core product
- a replacement for all external chat systems
- a full OF/Fansly suite
- a wide backoffice
- a general analytics-first BI environment
- creator password storage
- multitenant SaaS architecture

## Method

### Architectural stance

The current product should be built as one monolithic server-rendered internal application with PostgreSQL as primary datastore.

Recommended stack:

- Django, Rails or Laravel
- PostgreSQL
- server-rendered HTML interface
- simple role/scope-based authorization
- background jobs only where clearly needed for syncing, enrichment or aggregation

### Why this method

This fits the product rule:

- low operational overhead
- easy to reason about
- strong admin and ORM support
- good fit for relational operational data
- easier to enforce scope, access and governance in one app boundary

## Core domain model

### 1. users

Authentication and base authorization layer.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| name | varchar(160) | required |
| email | varchar(255) | unique |
| password_hash | text | required |
| role | enum | admin, operator |
| status | enum | active, inactive |
| last_login_at | timestamptz | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### 2. operators

Operational actor profile linked to a login user.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| user_id | fk users.id | unique |
| name | varchar(160) | required |
| status | enum | active, inactive |
| notes | text | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### 3. creators

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| display_name | varchar(160) | required |
| legal_name | varchar(200) | nullable |
| status | enum | active, paused, offboarded |
| consent_status | enum | pending, active, revoked |
| primary_operator_id | fk operators.id | nullable |
| notes | text | nullable |
| primary_link | text | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### 4. creator_channels

Operational channels or route contexts per creator.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| creator_id | fk creators.id | indexed |
| platform | enum | instagram, tiktok, telegram, onlyfans, fansly, other |
| handle | varchar(160) | required |
| profile_url | text | nullable |
| status | enum | active, paused, restricted, banned |
| access_mode | enum | creator_only, operator_with_approval, operator_direct, draft_only |
| recovery_owner | enum | creator, agency, shared |
| credential_status | enum | known, unknown, needs_reset |
| vpn_required | boolean | default false |
| approved_access_region | varchar(120) | nullable |
| approved_ip_label | varchar(120) | nullable |
| approved_egress_ip | varchar(120) | nullable |
| access_notes | text | nullable |
| access_profile_notes | text | nullable |
| last_operator_update | text | nullable |
| last_operator_update_at | timestamptz | nullable |
| operator_acknowledged_at | timestamptz | nullable |
| operator_acknowledged_by_id | fk users.id | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Note:

Current live slices such as workspaces, creator materials and handoff editing fit naturally around this channel context and remain valid.

### 5. operator_assignments

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| operator_id | fk operators.id | indexed |
| creator_id | fk creators.id | indexed |
| scope | enum | full_management, posting_only, draft_only, analytics_only |
| starts_at | timestamptz | required |
| ends_at | timestamptz | nullable |
| active | boolean | default true |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### 6. connection_cards

This is the minimal controllable work unit around a conversation-driven conversion flow.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| creator_id | fk creators.id | indexed |
| channel_id | fk creator_channels.id | nullable |
| assigned_operator_id | fk operators.id | nullable |
| source_type | enum | instagram_dm, telegram, legacy_chat, onlyfans, fansly, group, referral, other |
| source_label | varchar(160) | nullable |
| source_url | text | nullable |
| external_system | enum | legacy_chat, instagram, telegram, onlyfans, fansly, other |
| external_thread_ref | varchar(255) | nullable |
| external_customer_ref | varchar(255) | nullable |
| paywall_state | enum | outside_paywall, inside_paywall, transitioning |
| routing_state | enum | new, operator_follow_up, creator_input_needed, ready_for_operator, blocked, done, dropped |
| priority | enum | low, normal, high, urgent |
| status | enum | open, paused, closed |
| latest_handoff_excerpt | text | nullable |
| latest_acknowledged_at | timestamptz | nullable |
| latest_acknowledged_by_id | fk users.id | nullable |
| next_action | varchar(200) | nullable |
| risk_flag | boolean | default false |
| policy_blocked | boolean | default false |
| notes | text | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Why this matters:

- the product owns the work card, not the conversation transport
- outside-paywall and inside-paywall become explicit operational states
- routing becomes manageable without requiring a new inbox first

### 7. handoffs

Explicit transfer layer between operators or work moments.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| connection_card_id | fk connection_cards.id | indexed |
| channel_id | fk creator_channels.id | nullable |
| created_by_user_id | fk users.id | indexed |
| body | text | required |
| created_at | timestamptz | required |

Rules:

- a handoff may belong to a connection card and optionally also reflect channel-level context
- the latest handoff should be easy to render in the workspace
- handoff is not a threaded comment system in the current phase

### 8. acknowledgements

Explicit read/seen confirmation for operational context.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| connection_card_id | fk connection_cards.id | nullable |
| channel_id | fk creator_channels.id | nullable |
| acknowledged_by_user_id | fk users.id | indexed |
| acknowledged_at | timestamptz | required |
| acknowledgement_type | enum | handoff_read, context_read |
| notes | text | nullable |

Rules:

- acknowledgement means "seen/read", not "approved" or "completed"
- acknowledgement is part of the control layer, not a workflow engine

### 9. creator_materials

Supporting contextual files or references bound to a creator.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| creator_id | fk creators.id | indexed |
| uploaded_by_user_id | fk users.id | indexed |
| label | varchar(255) | nullable |
| file_ref | text | required |
| mime_type | varchar(120) | nullable |
| notes | text | nullable |
| active | boolean | default true |
| created_at | timestamptz | |
| updated_at | timestamptz | |

This is a supporting slice, not the core product identity.

### 10. connection_events

A lightweight operational timeline for routing and state changes.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| connection_card_id | fk connection_cards.id | indexed |
| actor_user_id | fk users.id | nullable |
| event_type | enum | created, routed, assigned, handoff_added, acknowledged, blocked, unblocked, closed, reopened, note_added |
| payload_json | jsonb | nullable |
| created_at | timestamptz | required |

This is intentionally light. It is not a full audit or messaging store.

### 11. access_audit

Light governance log for sensitive operational changes.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| creator_id | fk creators.id | indexed |
| channel_id | fk creator_channels.id | nullable |
| operator_id | fk operators.id | nullable |
| event_type | enum | assignment_created, assignment_revoked, access_mode_changed, consent_changed, channel_paused, channel_flagged, password_rotation_confirmed, 2fa_changed |
| notes | text | nullable |
| created_at | timestamptz | |

## Relationships

- one creator has many channels
- one creator may have many connection cards
- one channel may be linked to many connection cards
- one operator may own many assignments and be assigned many connection cards
- one connection card may have many handoffs
- one connection card may have many acknowledgements over time
- one connection card may have many connection events
- creator materials support workspace context for creators

## Hard system rules and constraints

1. `creators.status = active` requires `consent_status = active`
2. operators may only act within active assignment + valid scope
3. channel access and policy constraints must be visible before action
4. CreatorWorkboard must not store creator or channel passwords
5. a connection card must always belong to a valid creator
6. `paywall_state` and `routing_state` must be explicit on connection cards
7. acknowledgement must never be treated as approval or completion
8. a blocked or policy-blocked card must visibly communicate that state before action
9. a connection card may reference an external thread, but the external thread is not required to be stored in full
10. admin users can override broadly, operators cannot override scope or policy constraints outside their permissions

## Authorization model

### Admin

- full read/write on all records
- can manage creators, channels, assignments, connection cards, handoffs, acknowledgements and governance-related fields
- can deactivate/reactivate assignments
- can view all routing states and stalled work

### Operator

- access only within active assignment
- scope still matters:
  - `full_management`: full operational actions within assigned creator scope
  - `posting_only`: operational follow-up and channel/workspace actions where explicitly allowed
  - `draft_only`: limited drafting or context updates only where product rules allow it
  - `analytics_only`: read-only access where intended; no routing, no handoff writes, no operational acknowledgement that implies execution responsibility

Authorization check sequence:

1. if admin, allow
2. else resolve operator from user
3. check active assignment for creator within valid date range
4. check scope against requested action
5. enforce creator/channel/policy blocking rules

## Workflow

### Operational workflow in the corrected product

1. creator and channel context exist
2. operator assignment exists
3. connection card is created or referenced from an external route
4. source context is visible
5. handoff is visible
6. acknowledgement is recorded where needed
7. routing state is updated
8. operator takes action in the appropriate environment
9. next action and handoff are left clearly for the next step

### Route logic

The core route is:

- outside-paywall → transition → inside-paywall

The system must make this route visible and manageable without pretending to own every message.

## Screens

### Primary screen model

1. Operator Home / Queue
2. Creator Detail / Creator Work Page
3. Channel Detail
4. Workspace
5. Assignments
6. Supporting admin flows

### 1. Operator Home / Queue

Purpose:

- show what requires attention now
- reduce search time
- show routing state and next action

Should show:

- assigned cards
- paywall state
- routing state
- creator/channel
- risk/policy indicators
- latest handoff presence
- acknowledgement state
- next action

### 2. Creator Detail / Creator Work Page

Purpose:

- show creator context as operational truth
- show channels, materials, assignments and entry points into active work

Should show:

- creator status
- consent status
- primary operator
- channels
- active work entry points
- creator materials
- workspace links

### 3. Channel Detail

Purpose:

- show channel-level access and policy context
- serve as a bridge to workspace and creator context

Should show:

- channel status
- access mode
- credential state
- handoff state
- acknowledgement state
- policy and risk context
- workspace entry

### 4. Workspace

Purpose:

- bring together handoff, acknowledgement, policy, source and quick actions before execution

Should show:

- latest handoff
- acknowledgement state
- creator/channel context
- risk flags
- access policy
- source context
- quick actions into external systems

### 5. Assignments

Purpose:

- manage explicit operational ownership

Should support:

- create
- update
- deactivate
- reactivate
- summary of active/inactive assignments

## Operational metrics

In the corrected product, the first metrics are operational, not dashboard vanity metrics.

Primary operational measures:

- missing handoff count
- missing acknowledgement count
- blocked work count
- stalled queue count
- average time from new to ready-for-operator
- average handoff freshness
- open cards by route and assignee

Economic or broader revenue metrics may return later, but they are no longer the defining product core for phase 1.

## Security rules from day 1

Required:

- no creator or channel passwords stored
- consent status required for active creators
- access mode required per channel
- operators only see assigned creators/channels/cards
- policy and risk visible before action
- governance-sensitive changes lightly logged
- acknowledgement meaning stays narrow and honest

## Implementation

### Build order in 8 steps

1. users + auth + operators
2. creators + creator detail
3. channels + channel policy/access context
4. operator assignments
5. workspace context and handoff
6. acknowledgement layer
7. connection card model + queue + routing state
8. external thread reference + lightweight connection events + governance hardening

### Current live slices that remain valid

The following already-built or current-direction slices remain valid and useful:

- creator materials
- assignment management
- workspace access control
- handoff save flow
- acknowledgement direction
- creator/channel/workspace discoverability

They should now be interpreted as parts of the connection-board machine, not as proof that the old marketing-monitor framing should continue unchanged.

### Absolute minimum v0.1 in this corrected direction

If the product must stay very small, v0.1 contains:

- login
- creators
- channels
- assignments
- workspace
- handoff
- acknowledgement
- basic routing state
- external thread reference on connection cards

## Milestones

### Milestone 1 — Foundation

- auth and operator roles work
- creators, channels and assignments work
- scoped access works

### Milestone 2 — Control layer backbone

- workspaces are usable
- handoff is writable and visible
- acknowledgement is usable
- channel access/policy context is visible

### Milestone 3 — Connection-board core

- connection cards exist
- routing state exists
- outside-paywall / inside-paywall state exists
- operator queue is usable

### Milestone 4 — Connector and workflow hardening

- external thread references are usable
- lightweight connection events exist
- blocked/stalled work becomes visible
- legacy chat operations are measurably better organized

### Milestone 5 — Route expansion

- same model starts supporting narrower paywall creator workflows
- feeder and intake logic improve
- assisted AI enrichment can be added cautiously

## Gathering results

The corrected product is successful when the following can be answered without reconstructing the truth from scattered chats:

- who owns this work?
- which creator and channel does it belong to?
- is this outside or inside paywall?
- what is the routing state?
- what is the latest handoff?
- was the context acknowledged?
- what is the next action?
- what is blocked, stalled or missing?

### Primary success criteria

1. Less context loss  
2. Better handoff quality  
3. Faster next-action clarity  
4. More stable operator collaboration  
5. Cleaner outside-paywall to inside-paywall routing  
6. Better operational control over the existing revenue machine  

### Scope control after live usage

New feature requests are accepted only if they directly improve:

- context quality
- routing clarity
- handoff quality
- assignment clarity
- acknowledgement discipline
- connection-board usefulness

Everything else moves to later.

## Document hierarchy

For CreatorWorkboard the following now applies:

- The Startdocument is leading for product goal, scope, out-of-scope, users and success definition.
- The strategic correction document is leading for product identity and framing.
- This SPEC is leading for technical modeling and implementation constraints only after alignment to that corrected identity.

### Conflict rule

- If there is a conflict about scope or product identity, the Startdocument wins.
- If there is a conflict about the corrected strategic direction, the strategic correction document wins over the older framing.
- If there is a conflict about technical modeling after alignment, this SPEC wins.

## One-sentence summary

CreatorWorkboard is technically modeled as a human-controlled connection-board that owns context, routing, handoff and acknowledgement around conversation-driven conversion work, while external chat systems still own transport in the current phase.
