# Deploy preflight — Mara Ops main bundle — 2026-05-09

## Status

Deploy status: NO-GO

This document prepares the deploy gate only.  
It does not approve deploy.

This is local repository evidence only.  
It does not prove the current VPS runtime state.

## Local source state

Repository: marketing-monitor-v2  
Branch: main  
Target commit: ef3aec8  
Target commit description: Merge pull request #46 from Hank-chinasky/fix/operator-list-scope-hardening

Local state:

```text
## main...origin/main
```

Conclusion:

```text
main is clean
main equals origin/main
no local diff
```

## Included recent changes

Current main includes:

```text
ef3aec8 Merge pull request #46 from Hank-chinasky/fix/operator-list-scope-hardening
2f3fa97 Scope operator list for non-admin operators
0ed9359 Polish chats next step fallback
9975838 Polish feeder fallback text
7697f6e Fix operator list access for operator profiles
d3cbaec Merge pull request #41 from Hank-chinasky/feature/templates-v1-small
20d18c6 docs: lock templates v1 acceptance scope
ec58b8a Merge pull request #40 from Hank-chinasky/feature/buddy-assist-v1-small
1545481 docs: lock buddy assist v1 acceptance scope
83ccebe Merge pull request #39 from Hank-chinasky/docs/feeder-workspace-v1-live-note
```

Note:

```text
Earlier local inspection suggested operator list scope hardening was already present.
Current target main now includes PR #46 / commit 2f3fa97 for operator list scoping.
This preflight treats ef3aec8 as the target source-of-truth commit and does not infer live state.
```

## Local test evidence

Command:

```bash
DJANGO_SECRET_KEY=local-test-secret \
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver \
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1,http://testserver \
python manage.py test
```

Result:

```text
Found 208 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
Ran 208 tests in 60.016s
OK
Destroying test database for alias 'default'...
```

Note:

```text
UserWarning: No directory at: /home/jan/projects/marketing-monitor-v2/staticfiles/
```

This warning is not treated as a deploy blocker for local test evidence.

## Migration check

Command:

```bash
DJANGO_SECRET_KEY=local-test-secret \
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver \
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1,http://testserver \
python manage.py makemigrations --check --dry-run
```

Result:

```text
No changes detected
```

Conclusion:

```text
No migration changes detected locally.
No migration plan required from current local state.
```

## Docker / Compose / VPS / env impact

Current local evidence:

```text
No local diff before creating this document.
No deploy action performed.
No VPS action performed.
No Traefik action performed.
No Docker/Compose action performed.
No .env action performed.
No migrations created.
```

## Live commit

Current live commit: TODO — must be verified from VPS in a separate read-only server preflight.

Important:

```text
The commit range to deploy is not proven until the current live commit is verified.
```

## Required before deploy GO

Deploy remains blocked until the following are documented:

```text
- current live commit from VPS
- read-only VPS verification of current live git commit
- read-only VPS verification of current working tree cleanliness
- confirmation whether live runtime uses the expected compose path
- confirmation that no live-only drift exists before deploy
- target commit confirmed as ef3aec8 or newer approved commit
- exact commit range from live commit to target commit
- rollback command/path
- server preflight evidence
- post-deploy smoke checks
- container/app healthcheck after deploy
- final Stack Guardian GO
```

Optional TODO:

```text
- run Django deploy/system checks in the deploy-equivalent environment if available
```

## Proposed rollback principle

Rollback must be commit-anchored.

Expected principle:

```text
git checkout <previous_live_commit>
rebuild/restart using existing deploy procedure
verify smoke checks
```

Exact rollback command/path must be confirmed from the live VPS deploy setup before deploy.

## Proposed post-deploy smoke checks

After deploy, verify at minimum:

```text
- /login/ reachable
- authenticated admin can access /operators/
- authenticated non-admin operator can access /operators/
- non-admin operator sees only own Operator record
- plain user gets 403 on /operators/
- anonymous user gets redirect / no 200
- /chats/ loads
- /feeder/ loads
- no obvious 500 in app logs
```

## Final preflight conclusion

Local deploy-preflight evidence is clean.

However:

```text
Deploy remains NO-GO.
```

Reason:

```text
The current live commit and exact deploy range are not yet proven from VPS.
Server preflight and rollback path are not yet documented.
```
