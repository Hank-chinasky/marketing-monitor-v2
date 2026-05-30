# Buddy draft reply v1 — scope lock

## Status

Docs-only decision lock. No code, no migration, no deploy.

## Problem

Chats Workspace now has selected thread context and read-only message context, but Mara still has to manually compose every reply.

Buddy can reduce operator time by drafting a reply proposal, while Mara remains responsible for reviewing, editing and sending outside the Workboard.

## Decision

V1 introduces operator-controlled Buddy reply drafts.

Buddy may draft a suggested reply based on the selected conversation thread and visible message context.

Buddy must not send, post, approve or execute any external action.

## Product rule

Default UI/product language is English.

Buddy reply language follows the customer message language.

Examples:
- Dutch customer message -> Dutch reply draft
- German customer message -> German reply draft
- English customer message -> English reply draft

If the language is unclear, Buddy should default to English or signal that the operator should choose.

## Allowed context

Buddy may use:
- selected ConversationThread
- visible ConversationMessages for the selected thread
- creator display name
- customer_stage
- thread_summary
- open_loop
- guardrails
- risk_flags
- last_handoff_note
- existing thread context and visible prior approved drafts if already available in the selected thread context
- completeness alerts
- policy/context block

## Output

Buddy may produce:
- reply draft
- short rationale / context note
- missing context warning
- risk warning
- suggested next step

## Human control

Mara/operator must:
- read the draft
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
- no message create/update flow for operators

## Data/training note

Historical chat data may be valuable later, but is explicitly outside V1.

Before using historical data for training, retrieval or evaluation, a separate legal/data review is required.

## Acceptance before code

Code-slice may only start after Architect + Stack Guardian approve:

- prompt/context contract
- output shape
- UI location
- whether drafts are stored or generated only for display
- tests
- safety/guardrail behavior
- no-send enforcement
- language behavior
