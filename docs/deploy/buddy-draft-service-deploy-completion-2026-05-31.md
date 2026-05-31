# Deploy completion — Buddy draft service boundary

## Status

Deploy completed and functionally accepted.

## Date

2026-05-31

## Final live commit

961a0ef

## Rollback anchor

2c6c0c1

## Scope

This note documents the accepted app-only redeploy of PR #65: Add buddy reply draft service boundary.

## Result

- Deployment to 961a0ef completed.
- No database migration was required.
- Migrations through core.0017 are applied.
- Container is healthy.
- Django check OK.
- makemigrations --check clean.
- Internal health with proxy headers returned 200.
- Public Traefik route returned expected Basic Auth behavior.
- Logs clean: no tracebacks and no 500s.
- Browser smoke checks passed.
- No rollback required.

## Functional smoke

- healthz OK
- basic auth OK
- Django login OK
- /chats/ OK
- Berichtcontext visible
- Buddy draft visible read-only
- no send/reply/post visible
- /conversations/ OK
- /conversations/create/ OK
- /feeder/ OK

## Scope confirmed

- Buddy draft service boundary is live.
- ConversationMessage read-only panel remains live.
- Buddy draft output is read-only.
- No send/reply/post/autopilot action is visible or executable.
- No external AI/API call was added.
- No training/vector/import flow was added.
- No model or migration change was deployed.
- No Traefik/.env/Docker/Compose config change was made.

## Conclusion

Deploy accepted as live and stable.

No further VPS actions now.
