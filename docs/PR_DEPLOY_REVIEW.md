# PR Deploy Review — Shared VPS / Traefik

## Core gate
- [ ] Alleen web op `cc_public`
- [ ] Geen extra hostpoortbindings
- [ ] `/healthz` aanwezig en correct gebruikt
- [ ] `SECRET_KEY` hard-failt
- [ ] Proxy / HTTPS settings correct
- [ ] Non-root container
- [ ] Static / WhiteNoise correct
- [ ] Persistent storage correct
- [ ] Compose schoon en zonder tijdelijke uitzonderingen
- [ ] Live config blijft reconstrueerbaar uit git

## Security gate
- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` correct
- [ ] `CSRF_TRUSTED_ORIGINS` correct
- [ ] `SECURE_PROXY_SSL_HEADER` correct
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] HSTS staat aan
- [ ] `INCLUDE_SUBDOMAINS` / `PRELOAD` alleen indien expliciet gevalideerd

## Runtime gate
- [ ] Healthcheck hangt niet aan login/admin/functionele route
- [ ] Startup flow is klein en voorspelbaar
- [ ] `migrate` en `collectstatic` gedragen zich gecontroleerd
- [ ] Geen handmatige live fixes nodig

## Drift gate
- [ ] Geen live-only wijzigingen buiten `.env` / secrets
- [ ] Geen verborgen serverstaat nodig om deploy te laten werken

**GO alleen als alles hierboven waar is.**
