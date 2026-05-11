# Buddy Assist v1 — scope lock

## Status

Buddy is strategically important for CreatorWorkboard, but in the current Mara Ops phase Buddy remains a small assist layer inside the existing Chats and Feeder workflows.

Buddy is not the main product layer in NOW.

## NOW

Buddy Assist v1 may:

- show existing creator/channel/thread context as prefill
- reduce repeated name/profile/persona input for operators
- summarize selected context
- signal missing context fields
- propose a next step
- prepare a compact session brief
- condense handoff context
- optionally prepare a draft suggestion for human review

## LATER

A trained Buddy may later:

- use historical conversations
- learn creator/customer patterns
- improve answer suggestions
- use a controlled memory or retrieval layer
- support prompt/versioning/audit
- support operator feedback loops
- become a stronger CreatorWorkboard value layer

## NOT NOW

Buddy Assist v1 must not:

- send messages
- post content
- execute external actions
- decide approvals
- take over workflow ownership
- run autonomous actions
- become a multi-agent system
- introduce deep integrations
- introduce a CRM/persona database
- introduce a memory/vector/training pipeline
- ingest years of conversations without a separate privacy and architecture decision

## Decision rule

Build only Buddy changes that directly reduce repeated input or speed up context scanning inside existing Chats or Feeder workflows.

If the change requires new memory, autonomous action, external integration, or a new product layer, it is not part of NOW.
