# Deploy History

## 2026-03-22 — Eerste deploy-hardening voor `ops.creatorworkboard.com`

### Doel
De Django-app deploy-safe maken voor een gedeelde VPS achter Traefik, met nadruk op:
- shared-host discipline
- voorspelbare startup
- expliciete healthchecks
- strakkere Django security-instellingen
- minimale deployment drift

---

### Samenvatting
De stack is aangescherpt van “werkt waarschijnlijk” naar “verantwoord deploybaar”, met een focus op:
- alleen publieke toegang via Traefik
- geen speculatieve Traefik-config
- hard-fail gedrag voor secrets
- expliciete `/healthz` healthcheck
- HSTS en veilige cookie/proxy-instellingen
- non-root container en nette runtime-defaults

---

### Belangrijkste technische keuzes

#### Traefik / ingress
- Gekozen voor `docker-compose.yml` als bestandsnaam
- Publieke router op:
  - host: `ops.creatorworkboard.com`
  - network: `cc_public`
  - entrypoint: `websecure`
  - TLS: ingeschakeld
  - certresolver: `le`
- Gekozen middleware-set:
  - `traefik-auth@docker`
  - `security-headers@file`

#### Waarom deze middleware-keuze
Deze keuze is bewust gemaakt op basis van wat op de VPS daadwerkelijk is bevestigd:
- `cc_public` is bevestigd
- `le` is bevestigd
- `security-headers@file` is bevestigd
- `traefik-auth@docker` is bevestigd
- `apps-auth@file` is **niet** bevestigd en wordt daarom bewust **niet** gebruikt

Deze keuze is dus gebaseerd op bewezen bestaande infrastructuur, niet op aannames.

--- 28-03-2026

### Aangebrachte wijzigingen

#### 1. Container / Docker
- `Dockerfile` gebruikt `python:3.13-slim`
- container draait als non-root gebruiker (`appuser`)
- `PYTHONDONTWRITEBYTECODE=1`
- `PYTHONUNBUFFERED=1`
- `PIP_NO_CACHE_DIR=1`
- `/app/data` en `/app/staticfiles` worden expliciet aangemaakt
- `entrypoint.sh` wordt executable gemaakt
- runtime start via `/app/entrypoint.sh`

#### 2. Startup flow
- `entrypoint.sh` gebruikt `set -eu`
- startup maakt benodigde directories aan
- migrations draaien automatisch bij containerstart
- `collectstatic` draait automatisch bij containerstart
- Gunicorn draait met:
  - bind `0.0.0.0:8000`
  - `workers=1`
  - `timeout=60`
  - logging naar stdout/stderr

#### 3. Docker Compose
- compose-bestand heet `docker-compose.yml`
- webservice expose’t alleen poort `8000` intern
- geen extra hostpoortbindings toegevoegd
- persistent volume:
  - `creatorworkboard_data:/app/data`
- network:
  - alleen `cc_public`
- healthcheck gebruikt:
  - `http://127.0.0.1:8000/healthz/`

#### 4. Django security
- `SECRET_KEY` faalt hard als `DJANGO_SECRET_KEY` ontbreekt
- `DEBUG` default staat veilig op `False`
- `ALLOWED_HOSTS` komt expliciet uit environment
- `CSRF_TRUSTED_ORIGINS` komt expliciet uit environment
- `SECURE_PROXY_SSL_HEADER` staat aan voor reverse proxy use-case
- `SECURE_SSL_REDIRECT` staat standaard aan
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SESSION_COOKIE_HTTPONLY=True`
- `SECURE_HSTS_SECONDS` staat aan
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=False`
- `SECURE_HSTS_PRELOAD=False`
- `SECURE_REFERRER_POLICY="strict-origin-when-cross-origin"`
- `SECURE_CONTENT_TYPE_NOSNIFF=True`
- `X_FRAME_OPTIONS="DENY"`

#### 5. Static files
- WhiteNoise staat actief in middleware
- `CompressedManifestStaticFilesStorage` wordt gebruikt
- `STATIC_ROOT` is expliciet ingesteld op `/app/staticfiles`

#### 6. Health endpoint
- expliciete `HealthzView` toegevoegd
- route `/healthz/` toegevoegd
- healthcheck hangt dus niet meer aan `/login/` of andere functionele routes

#### 7. Repo hygiene
- `.dockerignore` toegevoegd / aangescherpt
- `.env.example` toegevoegd
- deployment-instellingen verplaatst naar expliciete environment-variabelen
- deploy-besluiten vastgelegd in repo-documentatie in plaats van alleen chat/notities

---

### Bestanden die hierbij horen
- `Dockerfile`
- `entrypoint.sh`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`
- `marketing_monitor/settings.py`
- `marketing_monitor/urls.py`
- `core/urls.py`
- `core/views.py`

---

### Belangrijke deploy-besluiten
- Alleen de webservice mag publiek aan Traefik hangen
- Geen db/worker/redis op `cc_public`
- Geen extra hostpoortbindings
- Geen onbewezen Traefik middleware-namen gebruiken
- Geen fallback secret in productie
- HSTS wel aan, maar:
  - `INCLUDE_SUBDOMAINS` uit
  - `PRELOAD` uit
- SQLite blijft toegestaan voor deze single-instance setup, mits op persistent volume en met conservatieve worker-count

---

### Openstaande externe checks
Deze punten vallen buiten de repo en moeten op de VPS zelf kloppen:
- `cc_public` bestaat echt
- DNS van `ops.creatorworkboard.com` wijst correct
- Traefik resolver `le` bestaat echt
- `security-headers@file` bestaat echt
- `traefik-auth@docker` bestaat echt
- er is geen router/conflict met dezelfde hostregel

---

### Reden van deze aanpak
Deze app draait op een gedeelde VPS. Daarom wegen deze twee even zwaar:
1. Django security
2. shared-host discipline

De gekozen configuratie is bewust conservatief gehouden, zodat de eerste live deploy:
- voorspelbaar is
- weinig verborgen aannames bevat
- aansluit op de bestaande Traefik-infrastructuur
- later nog verder verfijnd kan worden zonder nu onnodig risico te nemen
## 2026-03-28 — Public root-site deployed for `creatorworkboard.com`

### Summary
A separate public root-site stack was deployed for:

- `creatorworkboard.com`
- `www.creatorworkboard.com`

This stack is intentionally separate from `creatorworkboard-ops`, which remains the owner of:

- `ops.creatorworkboard.com`

### What changed
- Added a new public stack: `creatorworkboard-site`
- Added Traefik router for:
  - `creatorworkboard.com`
  - `www.creatorworkboard.com`
- Served the public site through an Nginx container on `cc_public`
- Kept `creatorworkboard-ops` unchanged and isolated
- Removed old Dutch duplicate pages from the public site and kept the English page set

### Validation
Validated locally through Traefik with:

- `curl -k --resolve creatorworkboard.com:443:127.0.0.1 https://creatorworkboard.com/ -I`
- `curl -k --resolve www.creatorworkboard.com:443:127.0.0.1 https://www.creatorworkboard.com/ -I`

Result:
- `HTTP/2 200` on both apex and `www`

### Notes
- Contact form UI is present, but not yet connected to a live endpoint
- `www` and apex currently both serve the site; canonical redirect can be added later
- This public site is intentionally minimal and not coupled to the internal ops application
