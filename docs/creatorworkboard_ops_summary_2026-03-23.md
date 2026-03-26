# Creator Workboard Ops — herstelverslag en changelog
Datum: 2026-03-23  
Omgeving: VPS / Docker / Traefik  
App: `creatorworkboard-ops`  
Pad: `/opt/commandcenter/apps/creatorworkboard-ops`

---

## 1. Samenvatting

De `creatorworkboard-ops` applicatie is succesvol live hersteld en gevalideerd op de VPS.

Werkend bevestigd:
- Docker deployment
- gezonde app-container (`healthy`)
- Traefik routing voor `ops.creatorworkboard.com`
- Traefik basic auth
- Django login
- CSRF-flow onder HTTPS
- superusers en operator logins
- `Operator` records in de app
- eerste `Creator` record in de database

Belangrijkste oorzaken van de storing:
1. de Docker healthcheck was ongeschikt voor een setup met HTTPS redirect achter Traefik
2. de Traefik `Referrer-Policy: no-referrer` brak Django CSRF-validatie op browser-login
3. er was verwarring tussen Django `User` accounts en het aparte `Operator` model in de app

---

## 2. Eindstatus

### Live URL
- `https://ops.creatorworkboard.com/`

### Beschermingslagen
1. Traefik basic auth
2. Django loginformulier

### Huidige werkende flow
1. gebruiker opent `https://ops.creatorworkboard.com/`
2. Traefik vraagt basic auth
3. na juiste Traefik credentials wordt doorgestuurd naar Django
4. Django login werkt
5. app is bereikbaar

---

## 3. Wat er is gedaan

### 3.1 Repository en live locatie
De applicatie is live geplaatst onder:

`/opt/commandcenter/apps/creatorworkboard-ops`

Repository herkend als:
- Git remote op GitHub
- deployment via Docker Compose

### 3.2 App build en startup bevestigd
Bevestigd werkend:
- image build
- migrations
- `collectstatic`
- Gunicorn startup
- app luistert op poort `8000`

### 3.3 Healthcheck-probleem opgelost
Probleem:
- container bleef eerst `starting` / `unhealthy`
- `/healthz/` kreeg intern een redirect
- de oude healthcheck volgde die redirect verkeerd

Oplossing:
- compose-healthcheck aangepast
- healthcheck gebruikt nu een request met:
  - host `ops.creatorworkboard.com`
  - `X-Forwarded-Proto: https`
- container werd daarna correct `healthy`

Resultaat:
- `docker compose ps` toont gezonde container
- `/healthz/` geeft intern `200`

### 3.4 Traefik-routering hersteld
Bevestigd:
- correcte labels op de app-container
- container gekoppeld aan `cc_public`
- Traefik ziet de service correct
- lokale routing test via `curl --resolve` werkte

### 3.5 Traefik basic auth hersteld
Probleem:
- oude wachtwoorden waren verloren gegaan
- toegang tot protected routes hing af van `traefik-auth@docker`

Gevonden:
- Traefik auth kwam uit:
  - `TRAEFIK_DASHBOARD_AUTH`
  - bestand: `/opt/commandcenter/edge/traefik/.env`

Oplossing:
- nieuw basic auth wachtwoord gegenereerd
- `.env` bijgewerkt
- Traefik herstart
- bevestigd:
  - zonder credentials: `401`
  - met credentials: request komt door naar Django

### 3.6 Django login en CSRF-probleem opgelost
Probleem:
- Django credentials werkten server-side
- browser login gaf toch `403 CSRF-verificatie mislukt`

Analyse:
- Django instellingen waren uiteindelijk correct:
  - `USE_X_FORWARDED_HOST = True`
  - `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`
  - juiste `CSRF_TRUSTED_ORIGINS`
- `curl` login met expliciete `Origin` en `Referer` werkte
- browser login faalde
- logs toonden POST requests zonder geldige referer
- oorzaak bleek Traefik header in `dynamic.yml`:
  - `referrerPolicy: "no-referrer"`

Waarom dit fout ging:
- Django CSRF voor HTTPS-login verwacht een geldige `Origin` of `Referer`
- Traefik dwong browsers om geen referer mee te sturen
- daardoor werd login-POST afgewezen

Oplossing:
- Traefik `dynamic.yml` aangepast:
  - van `referrerPolicy: "no-referrer"`
  - naar `referrerPolicy: "same-origin"`
- Traefik herstart
- browser login werkte daarna correct

### 3.7 Superusers en users ingericht
Bevestigd aanwezig:
- `Superadmin`
- `admin`
- `operator1`

Later toegevoegd:
- `operator_manoel`
- `operator_mara`

### 3.8 Verschil tussen `User` en `Operator` vastgesteld
Belangrijk inzicht:
- `Creator.primary_operator` verwacht **geen** Django `User`
- `Creator.primary_operator` verwacht een record uit model `Operator`

Gevonden modelstructuur:
- `Operator`
  - `id`
  - `user` → `OneToOneField` naar Django `User`

Daarom werkte dit niet:
- direct een `User` koppelen aan `Creator.primary_operator`

Oplossing:
- eerst echte `Operator` records aangemaakt voor de operator users
- daarna creator gekoppeld aan een `Operator`

### 3.9 Eerste app-data aangemaakt
Aangemaakt:
- eerste `Creator`
- gekoppeld aan `operator_manoel`

---

## 4. Huidige data

### Django users
Bevestigd aanwezig:
- `Superadmin`
- `admin`
- `operator1`
- `operator_manoel`
- `operator_mara`

### Operators
Aangemaakt:
- `operator1`
- `operator_manoel`
- `operator_mara`

### Creators
Aangemaakt:
- `Creator Test`
- gekoppeld aan `operator_manoel`

---

## 5. Belangrijke technische details

### Live app locatie
- `/opt/commandcenter/apps/creatorworkboard-ops`

### Traefik locatie
- `/opt/commandcenter/edge/traefik`

### Belangrijke bestanden
- `/opt/commandcenter/apps/creatorworkboard-ops/docker-compose.yml`
- `/opt/commandcenter/apps/creatorworkboard-ops/.env`
- `/opt/commandcenter/apps/creatorworkboard-ops/marketing_monitor/settings.py`
- `/opt/commandcenter/edge/traefik/docker-compose.yml`
- `/opt/commandcenter/edge/traefik/.env`
- `/opt/commandcenter/edge/traefik/dynamic.yml`

### Relevante Django instellingen
Bevestigd:
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`
- `USE_X_FORWARDED_HOST = True`
- `CSRF_TRUSTED_ORIGINS = ['https://ops.creatorworkboard.com']`
- `SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"`

### Relevante Traefik aanpassing
In `dynamic.yml`:
- `referrerPolicy: "no-referrer"` → `referrerPolicy: "same-origin"`

### Relevante compose wijziging
De healthcheck is aangepast zodat de app achter Traefik correct als healthy wordt gezien.

---

## 6. Security-opmerking

Tijdens troubleshooting zijn meerdere wachtwoorden handmatig gebruikt in shell en chat.

Daarom moeten de volgende wachtwoorden opnieuw gezet worden:
- `operator1`
- `operator_manoel`
- `operator_mara`
- `admin`
- `Superadmin`
- Traefik basic auth wachtwoord moet veilig worden opgeslagen in password manager

Aanbevolen:
- alle gedeelde/gebruikte tijdelijke wachtwoorden roteren
- nieuwe credentials vastleggen in Bitwarden / 1Password / KeePassXC
- shell history eventueel opschonen indien gewenst

---

## 7. Open vervolgwerk

### Direct praktisch
- echte creators invoeren
- echte channels invoeren
- operator-wachtwoorden opnieuw zetten
- nieuwe Traefik credentials documenteren

### App functioneel
- controleren welke schermen in de UI al bestaan voor:
  - creators
  - channels
  - operators
- eventueel `core/admin.py` uitbreiden als modellen niet via Django admin beschikbaar zijn

### Infra / ops
- wijzigingen committen/documenteren
- changelog bijwerken
- deployment history bijwerken
- backups van relevante config veilig bewaren

---

## 8. Handige commando’s

### Containerstatus
```bash
cd /opt/commandcenter/apps/creatorworkboard-ops
docker compose ps
docker compose logs --tail=100
