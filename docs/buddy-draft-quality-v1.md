# Buddy draft quality v1 — scope lock

## Status

Docs-only decision lock. No code, no migration, no deploy.

## Problem

Buddy draft service boundary is live, but the current draft is still conservative and limited.

Mara needs a more useful reply proposal based on the selected thread, visible messages, guardrails and context.

## Decision

V1 improves reply draft quality inside the existing Buddy service boundary.

The service remains internal, read-only and operator-controlled.

## Product rules

- Default UI/product language is English.
- Buddy reply language follows the latest inbound customer message language.
- Dutch customer message -> Dutch reply draft.
- German customer message -> German reply draft.
- English customer message -> English reply draft.
- If language is unclear, Buddy should signal uncertainty and default conservatively.

## Allowed input context

Buddy may use:

- selected ConversationThread
- visible ConversationMessages for the selected thread
- latest inbound customer message
- creator display name
- customer_stage
- thread_summary
- open_loop
- guardrails
- risk_flags
- last_handoff_note
- completeness alerts
- policy/context block
- latest BuddyDraft status/summary only if already visible in selected thread context

## Output

Buddy may produce:

- reply_text
- language
- source
- requires_human_review
- safety_note
- missing_context_note
- tone_note

## Quality target

Draft should be:

- short enough for operator review
- in the customer message language
- polite and context-aware
- not overpromising
- not inventing facts
- not escalating sexually/commercially without context
- aligned with guardrails
- clearly marked as a draft

## Human control

Mara/operator must:

- review the draft
- edit where needed
- copy/paste outside the Workboard
- remain responsible for the final message

## Not in V1

- no auto-send
- no reply/post action
- no external chat integration
- no livechat API
- no webhook
- no background worker
- no autonomous AI action
- no approval bypass
- no operatorless mode
- no training pipeline
- no vector memory
- no fine-tune
- no import of historical chat data
- no provider registry
- no customer/tenant module switching
- no settings/env changes
- no model changes
- no migrations

## Implementation direction for later code-slice

Preferred:

- improve core/services/buddy_reply.py only
- keep ChatHubView orchestration small
- keep template read-only
- add/adjust tests for service quality cases
- add tests for Dutch, German and English draft language behavior
- add tests for missing context and human review requirement

## Acceptance before code

Code-slice may only start after Architect + Stack Guardian approve:

- input context contract
- output shape
- language behavior
- safety behavior
- tests
- no-send enforcement
- no API/provider/training work
