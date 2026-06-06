# Connected Chat Intake v1 — scope lock

## Status

Docs-only decision lock. No code, no migration, no deploy.

## Problem

Chats Workspace v1 and Buddy draft quality v1 are live, but Mara still does not receive real chat messages from the existing external chat platforms inside `/chats/`.

The current workflow proves the workspace, assignment scope, message context and Buddy-slot, but it is not yet a real MVP until actual source-system messages flow into the Workboard.

## Decision

V1 introduces the scope for connecting one existing Mara-owned Django chat platform as the first inbound source.

The goal is to import real inbound messages into the existing internal `ConversationThread` and `ConversationMessage` flow so Mara can see them in `/chats/`.

This is not a connector product, connectorboard, SaaS layer or multi-platform inbox.

## Product rule

Mara-first, connector-ready.

Build the first integration for Mara, but do not hardcode it in a way that prevents future adapters for other chat systems.

The internal pattern should be:

source adapter -> normalized message payload -> internal import/upsert service -> ConversationThread / ConversationMessage -> /chats/ -> Buddy-slot

## V1 source

V1 targets one existing Django source platform.

The source is expected to provide enough data to identify:

- source system
- source site/platform
- source thread/conversation
- source message
- customer/user identity or label if available
- message direction
- message body
- message timestamp

## In V1

Connected Chat Intake v1 may include:

- one Django source adapter
- normalized source payload shape
- internal import/upsert service
- idempotent inbound import
- creation or update of internal `ConversationThread`
- creation of internal `ConversationMessage`
- dedupe by source identity
- chronological message ordering by source timestamp
- platform/site visibility in `/chats/`
- source label visible for Mara/admin
- Buddy-slot using the latest imported inbound message
- tests for import idempotency, ordering and scoped visibility

## Not in V1

- no reply/send from ops
- no outgoing message sync
- no auto-answer
- no autopilot
- no external AI/API
- no provider registry
- no connectorboard UI
- no connector marketplace
- no Fansly adapter
- no OnlyFans adapter
- no ManyVids adapter
- no multi-platform operator routing engine
- no operator pool logic
- no SaaS/multitenancy product layer
- no background worker unless separately approved
- no webhook unless separately approved
- no training/vector/import of historical bulk data
- no autonomous AI action
- no customer/source masking toggle yet

## Data model expectation

A code-slice may require a migration-aware review if the current models do not support source identity and dedupe.

Likely required or to be confirmed:

- `ConversationThread.source_system`
- `ConversationThread.source_thread_id`
- `ConversationMessage.source_message_id` or equivalent
- optional source site/platform label
- `ConversationMessage.occurred_at`
- `ConversationMessage.direction`
- `ConversationMessage.body`

If `ConversationMessage` lacks source message identity, adding it is acceptable only as a small migration-aware slice because reliable dedupe is required.

## Visibility rule

For Mara v1, the platform/source may be visible in `/chats/`.

Later, for external customers or large chat operations, admin-controlled source visibility may be considered.

That toggle is not part of V1.

## Human control

V1 is inbound-only.

Mara may read imported messages and use the Buddy-slot draft proposal, but replying still happens outside the Workboard until a later Operator Reply v1 slice.

## Source access and credential rule

V1 must not introduce unsafe source-system access.

Before code, confirm:

- how the source Django platform will expose messages
- whether access is read-only
- where credentials are stored
- no source credentials in Git
- no direct writes to the source platform
- no production database access without explicit approval
- no broad source data import beyond the needed inbound message window
- no historical bulk import in V1

The first integration should prefer the smallest safe source access path that can reliably provide current inbound messages.


## Acceptance before code

Code may only start after Architect + Stack Guardian approve:

- source adapter contract
- normalized payload shape
- source identity fields
- dedupe strategy
- migration need or no-migration proof
- tests
- no reply/send enforcement
- no connectorboard/product-layer expansion
- VPS/deploy risk
