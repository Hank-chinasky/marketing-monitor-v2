# Deploy History

## 2026-03-28 — CreatorWorkboard ops app stabilized after opportunity rollout

### Samenvatting
De ops-app is op de VPS gestabiliseerd na de introductie van de V1 opportunity layer.

### Uitgevoerd
- Docker build en restart van `creatorworkboard-ops` bevestigd
- Traefik routing voor `ops.creatorworkboard.com` hersteld
- basic auth voor de ops-omgeving hersteld
- reverse-proxy loginflow hersteld
- healthcheck werkend gemaakt achter Traefik en HTTPS-redirectgedrag
- ongeldige import in `core/urls.py` verwijderd om container restart loop te stoppen
- live toegang tot `/opportunities/` bevestigd
- queue pagination live bevestigd

### Gevalideerd
- migrations draaien
- static collection draait
- Gunicorn start goed op
- container wordt healthy
- login werkt achter Traefik
- protected access chain werkt:
  - Traefik auth
  - Django login
  - app access

### Resultaat
De ops-omgeving is stabiel genoeg om de huidige control layer live te testen.

---

## 2026-03-25 — Assignment-scoped operational access

### Samenvatting
Operationele toegang is centraal gekoppeld aan `OperatorAssignment`.

### Uitgevoerd
- scope helpers toegevoegd in `core/services/scope.py`
- creator list/detail/edit scoped gemaakt
- channel list/detail/edit scoped gemaakt
- dashboard scoped gemaakt
- `primary_operator` verwijderd uit autorisatielogica

### Resultaat
Structurele toegang werkt vanuit assignments in plaats van losse oude velden.

---

## 2026-03-22 — Ops deployment stabilized

### Samenvatting
De deploymentbasis voor de ops-app is live gestabiliseerd.

### Uitgevoerd
- compose drift verwijderd
- container healthcheck gefixt
- Traefik routing bevestigd
- Traefik auth hersteld
- main op VPS gelijkgetrokken

### Resultaat
De basis voor verdere live iteraties stond weer goed.

---

## 2026-03-18 — Creator materials MVP deployed and validated

### Samenvatting
De eerste interne materials-slice is toegevoegd en lokaal gevalideerd.

### Uitgevoerd
- `CreatorMaterial` toegevoegd
- scoped zichtbaarheid voor operators
- app-controlled material open/download route
- preview-first UX
- multi-upload
- migration dependency gefixt

### Resultaat
Een eerste werkende interne ops-slice voor materials stond live klaar als precedent voor verdere interne layers.

---

## Huidige deploymentstatus

### Live basis
- Docker
- Traefik
- Django
- Gunicorn
- VPS deployment

### Huidige productlaag live
- assignment-scoped operational access
- creator materials
- V1 opportunity control layer
- admin-seeded intake via Django admin
- queue + detail + scoring + outcome

### Volgende deploymentdoel
Niet breder deployen, maar:
- de huidige layer live bewijzen in Mara
- alleen bugs en operationele frictie oplossen
- geen scope-uitbreiding tijdens de proof sprint
