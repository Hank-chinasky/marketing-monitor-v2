# Rollback note — Buddy draft service boundary

## Status

Rollback completed and verified.

## Date

2026-05-30

## Final live commit

2c6c0c1

## Rolled back from

bbcad8e

## Scope

This note documents the rollback after the attempted app-only deploy of PR #65: Add buddy reply draft service boundary.

## Current live state

- ConversationMessage read-only panel: live
- Buddy draft service boundary: not live
- VPS/app state: stable

## Verification

- container healthy
- Django check OK
- makemigrations --check clean
- internal health with Host + X-Forwarded-Proto headers returned 200
- public Traefik route returned expected auth behavior
- browser status OK on https://ops.creatorworkboard.com/healthz/

## Smoke check note

Do not use naive localhost /healthz/ without proxy headers as a deploy smoke check.

It redirects to HTTPS and can produce misleading results.

Use internal health checks with the correct Host and X-Forwarded-Proto headers, plus the public browser check.

## Impact

No negative impact remains visible.

The VPS is back in a safe known state on 2c6c0c1.

## Open question before retry

Before attempting a new deploy to bbcad8e, determine whether the rollback was triggered by:

- real functional problem
- UI/rendering issue
- Buddy draft panel issue
- smoke-check misunderstanding
- healthcheck/proxy-header confusion
- other deploy/runtime issue

## Guardrails

No further VPS action should be taken from this note.

A new deploy attempt requires a fresh app-only deploy gate.
