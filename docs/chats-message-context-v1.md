# Chats Workspace v1 — message context scope lock

## Status

Docs-only decision lock. No code, no migration, no deploy.

## Problem

Chats Workspace has manual conversation intake and thread context, but the middle pane does not yet show the actual message context.

Without message context, operators still need to look outside the Workboard or rely on summaries and handoff notes.

## Decision

V1 introduces read-only message context for selected `ConversationThread`.

The goal is to show relevant messages in the Chats middle pane.

V1 does not send messages, sync live chat, or embed an external chat client.

## Preferred model direction

Use a separate `ConversationMessage` model later, linked to `ConversationThread`.

Do not use one large transcript text field as V1 direction.

Reason:
- messages need ordering
- messages need sender/direction
- messages may later be imported
- messages must remain scanable
- Buddy can later summarize from structured context without owning the workflow

## Candidate fields for later code-slice

```text
thread
direction
sender_label
body
sent_at
source_message_id
created_at
```

## Scope for later V1 code

Allowed later:
- add `ConversationMessage`
- show messages read-only in Chats middle pane
- scope messages through existing `ConversationThread` access
- allow admin/manual seed or admin management
- tests for scoped visibility and ordering

Not allowed in V1:
- sending messages
- external livechat API
- realtime sync
- embedded livechat client
- autonomous Buddy replies
- Buddy deciding or posting
- memory/vector/training layer
- multi-agent orchestration

## Buddy rules

Buddy may only:
- summarize visible messages
- signal missing context
- suggest next step
- condense handoff/session brief

Buddy must not:
- send replies
- decide status
- execute external actions
- replace operator review

## Privacy and scope

Messages must only be visible through existing scoped `ConversationThread` access.

Operators must not see messages for creators outside their assignment scope.

Unsupported authenticated accounts must not gain message access.

## Acceptance before code

Code-slice may only start after Architect + Stack Guardian approve:

- model choice
- fields
- migration plan
- admin/manual intake approach
- UI location in Chats middle pane
- tests
- deploy/migration gate
