## 2026-03-23 — creatorworkboard-ops deploy herstel en live validatie

### Samenvatting
De `creatorworkboard-ops` app is live hersteld op de VPS en end-to-end gevalideerd achter Docker en Traefik.

### Uitgevoerd
- repository geplaatst onder `/opt/commandcenter/apps/creatorworkboard-ops`
- Docker image gebouwd en app-container gestart
- migrations uitgevoerd
- static files verzameld
- Gunicorn startup bevestigd
- healthcheck aangepast zodat `/healthz/` correct werkt achter HTTPS redirect en Traefik
- containerstatus bevestigd als `healthy`
- Traefik routing voor `ops.creatorworkboard.com` hersteld
- Traefik basic auth opnieuw ingesteld en getest
- Django loginprobleem onderzocht
- CSRF-fout herleid naar Traefik `referrerPolicy: "no-referrer"`
- Traefik referrer policy aangepast zodat browser-login weer werkt
- superuser aangemaakt
- operator logins aangemaakt
- bijbehorende `Operator` records aangemaakt
- eerste `Creator` aangemaakt
- creator gekoppeld aan `operator_manoel`

### Bevestigd werkend
- Docker deployment
- healthy container
- Traefik routing
- Traefik basic auth
- Django login
- CSRF flow onder HTTPS
- `Operator` records
- eerste `Creator` record in database

### Open vervolg
- echte creators invoeren
- channels toevoegen
- operator-wachtwoorden opnieuw zetten
- nieuwe credentials vastleggen in password manager
- documentatie verder opschonen
