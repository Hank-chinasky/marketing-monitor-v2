# Deploy Gate — Django app op gedeelde VPS achter Traefik

Deze checklist is verplicht vóór elke eerste live deploy, elke wijziging aan compose/ingress/security, en elke wijziging aan startup/runtime-gedrag.

Gebruik deze checklist vóór elke live push.  
Alleen **GO** als alle verplichte punten waar zijn.

---

## 1. Netwerk en ingress

- [ ] Alleen de **webservice** hangt aan `cc_public`
- [ ] Geen `db`, `redis`, `worker`, `beat` of andere interne services hangen aan `cc_public`
- [ ] Er zijn **geen extra hostpoortbindings** voor de app-container
- [ ] Routing loopt uitsluitend via **Traefik labels**
- [ ] Hostname in Traefik labels klopt exact met het bedoelde domein/subdomein
- [ ] Als andere werkende services op deze VPS een verplichte `certresolver` gebruiken, dan gebruikt deze service die ook

**NO-GO als:**
- een interne service publiek bereikbaar is
- er naast Traefik nog een hostpoort openstaat
- labels afwijken van de bestaande VPS-conventie

---

## 2. Container hygiene

- [ ] Container draait **non-root**
- [ ] `.dockerignore` is aanwezig en correct
- [ ] Runtime image bevat geen onnodige development-only tooling
- [ ] `restart` policy staat correct
- [ ] Compose bevat geen verouderde of verwarrende drift

**NO-GO als:**
- de container als root draait zonder noodzaak
- deploy afhankelijk is van handmatige live fixes
- Compose rommelig of historisch vervuild is

---

## 3. Django security baseline

- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` is expliciet en correct
- [ ] `CSRF_TRUSTED_ORIGINS` is expliciet en correct
- [ ] `SECURE_PROXY_SSL_HEADER` staat correct achter Traefik
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECRET_KEY` komt uit environment en **faalt hard** als die ontbreekt
- [ ] `SECURE_HSTS_SECONDS` staat aan
- [ ] `SECURE_REFERRER_POLICY` is gezet

**Alleen indien nodig:**
- [ ] `SECURE_SSL_REDIRECT = True`
  - verplicht als Traefik **niet aantoonbaar** al centraal HTTP→HTTPS redirect afdwingt
  - niet verplicht als die redirect al centraal en bewezen actief is

**Bewuste default op deze VPS:**
- [ ] `SECURE_HSTS_INCLUDE_SUBDOMAINS = False`
- [ ] `SECURE_HSTS_PRELOAD = False`

**NO-GO als:**
- er een fallback secret in productie mogelijk is
- HTTPS-awareness achter proxy niet correct staat
- HSTS volledig ontbreekt

---

## 4. Health en startup

- [ ] Er is een expliciete **`/healthz`** endpoint
- [ ] Healthcheck test alleen app-gezondheid, niet login/admin/auth/template-flow
- [ ] Healthcheck gebruikt lokaal containerverkeer (`127.0.0.1`)
- [ ] Healthcheck heeft redelijke `timeout`, `retries` en `start_period`

**NO-GO als:**
- healthcheck op `/login/`, `/admin/` of een andere functionele route hangt
- healthcheck afhankelijk is van template-rendering of auth-state
- container tijdens normale startup onterecht unhealthy wordt

---

## 5. Static files en app-serving

- [ ] `WhiteNoiseMiddleware` staat correct in de middleware stack
- [ ] productie static storage staat correct
- [ ] `collectstatic` draait succesvol
- [ ] static delivery werkt zonder handmatige server-fixes

**NO-GO als:**
- static files alleen “toevallig” werken
- `collectstatic` stilzwijgend faalt
- WhiteNoise-config half af is

---

## 6. Database en persistentie

Voor deze single-instance setup met SQLite:

- [ ] SQLite staat op een **persistent volume**
- [ ] volume mount is stabiel en bewust gekozen
- [ ] Gunicorn worker count is conservatief
- [ ] er is geen impliciete aanname van multi-replica gedrag

**NO-GO als:**
- SQLite op ephemeral container filesystem staat
- meerdere replicas worden ingezet alsof dit Postgres is
- concurrency agressiever is dan de opslaglaag toelaat

---

## 7. Deploy flow

- [ ] `migrate` draait gecontroleerd en voorspelbaar
- [ ] `collectstatic` draait gecontroleerd en voorspelbaar
- [ ] startup script is klein en begrijpelijk
- [ ] containerstart schrijft alleen naar bedoelde volumes
- [ ] deploy vereist geen handmatige nabehandeling

**NO-GO als:**
- deploy alleen werkt na SSH-hotfixes
- startup shell-logica fragiel is
- migraties/race-achtige startup-problemen mogelijk zijn

---

## 8. Shared-host discipline

- [ ] de app respecteert bestaande naming- en netwerkconventies
- [ ] de app introduceert geen nieuwe publieke surface buiten Traefik
- [ ] de app raakt geen andere stacks, volumes of services
- [ ] secrets staan niet hardcoded in image of Compose
- [ ] er staan geen debug endpoints, testpoorten of tijdelijke uitzonderingen live

**NO-GO als:**
- de stack zich gedraagt alsof dit een dedicated host is
- wijzigingen impact kunnen hebben op andere apps achter dezelfde ingress
- live Compose nog tijdelijke uitzonderingen bevat

---

## 9. Repo / deployment drift

- [ ] de live VPS draait exact wat in git staat
- [ ] er zijn geen handmatige live edits in `settings.py`, `compose.yml`, `entrypoint.sh` of vergelijkbare deploybestanden
- [ ] environment-only verschillen zitten in `.env` of secret management
- [ ] afwijkingen van repo zijn expliciet gedocumenteerd

**NO-GO als:**
- live config afwijkt van repo zonder documentatie
- deploy afhangt van “bekende handmatige serverstaat”
- de echte productieconfig niet meer uit git te reconstrueren is

---

# HSTS rollout-notitie

Voor deze gedeelde VPS:

- begin desnoods met een **lage tijdelijke `SECURE_HSTS_SECONDS`** tijdens eerste live validatie
- verhoog pas daarna naar een lange waarde zoals `31536000`
- zet `INCLUDE_SUBDOMAINS` pas aan als het hele subdomeinlandschap gecontroleerd HTTPS-only is
- zet `PRELOAD` pas aan als dat bewust, permanent en volledig gevalideerd is

---

# GO-regel

Alleen **GO** als dit allemaal waar is:

- [ ] alleen web op `cc_public`
- [ ] geen extra hostpoortbindings
- [ ] `/healthz` aanwezig en gebruikt
- [ ] `SECRET_KEY` hard-failt
- [ ] proxy/HTTPS settings correct
- [ ] HSTS staat aan
- [ ] `INCLUDE_SUBDOMAINS` en `PRELOAD` bewust nog uit, tenzij expliciet gevalideerd
- [ ] non-root container
- [ ] static/WhiteNoise correct
- [ ] SQLite persistent volume correct
- [ ] Compose schoon
- [ ] live config = repo config

**Als één van deze punten faalt: NO-GO.**
