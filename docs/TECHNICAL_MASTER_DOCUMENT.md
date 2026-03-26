# TECHNICAL MASTER DOCUMENT — CREATORWORKBOARD / MARKETING MACHINE / BACKOFFICE VISION

## Datum
23 maart 2026

## Status
Levend masterdocument voor:
- projectcontext
- technische architectuur
- productvisie
- roadmap
- deploymentstatus
- werkprincipes
- beslisregels

---

# 1. Executive summary

CreatorWorkboard is gestart als een interne Django operations tool voor creators, channels en operators.

De tool ontwikkelt zich in drie logische productfasen:

1. **Interne operations cockpit**
2. **Conversation / routing layer**
3. **Backoffice / monetization engine**

De strategische kern is:

- eerst een interne tool bouwen die aantoonbaar productiviteitswinst oplevert
- die tool uitvoerig gebruiken met eigen creators en operators
- bugs en ontbrekende functies uit de praktijk halen
- pas daarna een productlaag overwegen voor agencies / SaaS

De commerciële visie is uiteindelijk groter dan alleen een dashboard.

Het systeem moet op termijn kunnen functioneren als een:

**creator revenue operations system**

met twee motoren:

- **Marketing machine**  
  trekt mensen van social media naar een bestaande chat of premium omgeving

- **Backoffice machine**  
  ondersteunt creators aan de achterkant in premium omgevingen zoals OnlyFans en Fansly

De huidige focus blijft echter bewust:

**eerst interne waarde, eerst dagelijkse bruikbaarheid, eerst productiviteitswinst.**

---

# 2. Productdefinitie

## 2.1 Huidige productdefinitie
Een interne operations cockpit voor:
- creators
- channels
- operators
- assignments
- access policy
- handoff
- content source
- dagelijkse werkcontext
- operator workspace per channel
- launch-first platformflow voor menselijk werk

De app is in fase 1 niet bedoeld als volledige vervanger van Instagram, TikTok, Reddit of Snapchat.

De app is wel bedoeld als:
- contextlaag
- policylaag
- handofflaag
- content-prep laag
- operator workspace
- veilige startplek voor platformwerk

Kernidee:
de operator start vanuit CreatorWorkboard, ziet direct alle relevante context, heeft content en instructie klaarstaan, opent daarna het juiste platform in een korte flow, voert het werk handmatig uit, en legt daarna resultaat en handoff vast.

## 2.2 Toekomstige productdefinitie
Niet enkel:
- social tool
- CRM
- chattool

Maar:

**een creator revenue operations system**

dat later kan uitgroeien naar:
- acquisition machine
- conversation OS
- backoffice routing layer
- whale escalation system
- AI-assisted operator cockpit

---

Extra operationeel doel in fase 1:
- operators sneller laten starten met werk op social platforms
- platformwerk structureren zonder platformen te proberen overnemen
- content vooraf klaarzetten in dashboard
- menselijke plaatsing en lichte engagement in één workflow ondersteunen
- minder tijd verliezen tussen dashboard, telefoon, platform en losse notities

Kernformules:

## 3.1 Front-office route
**Marketing machine → bestaande chat → omzet**

## 3.2 Back-office route
**Marketing machine → OF/Fansly backoffice → creator / high-value conversion**

---

# 4. Huidige technische stack

## Framework
- Django monolith
- server-rendered templates
- standaard Django auth
- standaard Django admin

## Database
- SQLite in huidige interne fase
- later waarschijnlijk PostgreSQL

## Deployment
- Docker
- Gunicorn
- Traefik als reverse proxy
- app draait op VPS onder:
  - `/opt/commandcenter/apps/creatorworkboard-ops`

## Domein
- `creatorworkboard.com`
- ops-omgeving:
  - `ops.creatorworkboard.com`

## Proxy / infra
- Docker network:
  - `cc_public`
- Traefik TLS certresolver:
  - `le`
- middleware bevestigd:
  - `security-headers@file`
  - auth laag bevestigd op huidige VPS-setup

---

# 5. Huidige werkende deploymentstatus

## Bevestigd werkend
- Git-based deployment naar VPS
- Docker build werkt
- container start
- migrations draaien
- static files worden verzameld
- Gunicorn draait
- `/healthz/` werkt
- container wordt healthy
- Traefik routing werkt
- Basic auth werkt
- Django login werkt
- CSRF werkt
- app is operationeel bruikbaar

## Bekende nuance
`check --deploy` gaf HSTS-waarschuwingen op Django-niveau, terwijl een deel van de security headers via Traefik wordt afgehandeld.

Dat is nu geen blocker voor interne livegang.

---

# 6. Runtime-architectuur

## Werkende app-locatie
De runtime-app leeft in repo root:

- `manage.py`
- `marketing_monitor/`
- `core/`
- `templates/`

## Reference-laag
`reference/` is geen runtime-app, maar frozen / canon / referentie.

---

# 7. Huidig datamodel

## 7.1 User
Django-auth user voor login.

## 7.2 Operator
Business / operations profiel gekoppeld aan een Django user.

Doel:
- operationele identiteit
- niet alleen technische login

## 7.3 Creator
Representeert een creatorprofiel.

Belangrijke velden:
- `display_name`
- `legal_name`
- `status`
- `consent_status`
- `primary_operator`
- `notes`
- `content_source_type`
- `content_source_url`
- `content_source_notes`
- `content_ready_status`

## 7.4 CreatorChannel
Representeert een platformaccount van een creator.

Belangrijke velden:
- `platform`
- `handle`
- `profile_url`
- `status`
- `access_mode`
- `recovery_owner`
- `login_identifier`
- `credential_status`
- `access_notes`
- `last_access_check_at`
- `two_factor_enabled`

VPN / policy:
- `vpn_required`
- `approved_egress_ip`
- `approved_ip_label`
- `approved_access_region`
- `access_profile_notes`
- `last_ip_check_at`

Handoff / context:
- `last_operator_update`
- `last_operator_update_at`

## 7.5 OperatorAssignment
Bepaalt operationele scope.

Velden:
- `operator`
- `creator`
- `scope`
- `starts_at`
- `ends_at`
- `active`

## 7.6 Richting voor channel workspace en platformflow

In fase 1 ligt de nadruk niet op diepe platformintegraties, maar op een uniforme operator-workspace.

Per creator-channel moet de operator vanuit het dashboard kunnen:
- de juiste accountcontext zien
- policy en accessvoorwaarden zien
- voorbereide content zien
- sessie starten
- snel naar het juiste platform gaan
- handmatig content plaatsen
- waar passend lichte handmatige engagement uitvoeren
- terugkomen in de app voor handoff en logging

Belangrijke nuance:
“via het dashboard inloggen” betekent in deze fase vooral:
- dashboard als startpunt
- launch-first toegang
- context en content vooraf klaar
- geen fragiele platform-clone
- geen diepe automation als basisidentiteit

De app wordt dus geen social network client, maar een:
**human-in-the-loop operator workspace**
---

# 8. Huidige rolstructuur

## 8.1 Superadmin
Volledige systeemcontrole.

## 8.2 Admin / platform admin
Beheert:
- operators
- creators
- channels
- assignments

## 8.3 Operator
Uitvoerende rol binnen toegewezen scope.

## 8.4 Creator
Nu nog business object, geen volwaardige app-loginrol.

---

# 9. Huidige scope- en permissielogica

Belangrijke regels:
- zichtbaarheid mag niet alleen op `primary_operator` leunen
- operationele scope komt uit assignments
- admin doet structureel beheer
- operator werkt in scope
- delete blijft vooral admin-domein

Belangrijke richting later:
- agency-scope + assignment-scope combineren

---

# 10. Huidige UI-lagen

## Werkend aanwezig
- login/logout
- operations dashboard
- creator list/detail
- channel list/detail
- creator network view
- assignment flows
- operator list/create
- admin-achtige create flows in normale app-UI

## UX-richting
- context-first
- policy zichtbaar vóór actie
- minder shell / minder losse notities
- minder admin-only gedoe
- gewone beheerflows in app

## 10.1 Nieuwe UI-richting: Channel Workspace

Per channel komt een uniforme operator workspace waarin zichtbaar is:
- platform
- handle
- profiel-URL
- access mode
- login/contextinformatie
- 2FA-status
- VPN / regio / IP policy
- content source
- content ready status
- open issues
- laatste operator update
- quick actions

Quick actions in fase 1:
- sessie starten
- platform openen
- profiel openen
- content bekijken
- caption / instructie kopiëren
- handoff opslaan
- issue markeren

Deze workspace ondersteunt:
- Instagram
- TikTok
- Reddit
- Snapchat
- later meer

Belangrijk:
de workflow is uniform, ook als platforms onderliggend verschillen.
---

# 11. Wat nu al live gebruikt moet worden

De tool moet eerst intern echte waarde bewijzen.

Dus:
- eigen creators invoeren
- eigen operators invoeren
- echte channels invoeren
- echte assignments gebruiken
- dagelijks vanuit de app werken
- bugs uit dagelijkse operatie halen

Doel:
- tijdswinst
- minder contextverlies
- minder fouten
- betere handoff
- snellere onboarding

---

# 12. Productvisie in 3 fasen

---

## Fase 1 — Interne operations cockpit

### Doel
Dagelijkse productiviteitswinst leveren.

### Wat het product is
Een interne cockpit voor:
- creators
- channels
- operators
- assignments
- access policy
- handoff
- content source
- operator workspace per channel
- launch-first platformflow
- menselijk social werk met minder contextverlies

### Kernbelofte
“Een operator kan sneller, veiliger en met minder contextverlies werken.”

### Succescriteria
- dagelijks gebruikt
- shell niet meer nodig voor normale beheerflows
- duidelijke productiviteitswinst
- andere persoon binnen organisatie kan beheer overnemen
- operator kan vanuit dashboard sneller een socialwerksessie starten
- platformcontext, policy en content staan klaar vóór actie
- contentplaatsing en lichte engagement verlopen via één menselijke workflow
- handoff na platformwerk is consequent vastgelegd
---

## Fase 2 — Conversation / acquisition layer

### Doel
Het systeem voorbereiden op social → destination routing.

### Wat het product wordt
Een conversation- en leadcontextlaag bovenop de operations cockpit.

### Eerste bouwstenen
- lead status
- source platform
- destination platform
- team notes / thread comments
- handoff op lead/conversation-niveau

### Bronkanalen
- TikTok
- Instagram
- later meer

### Bestemmingskanalen
- bestaande chat
- later OnlyFans / Fansly / eigen premium omgeving

### Kernbelofte
“Het team kan social leads beter coördineren en met minder verlies richting een betaalde omgeving sturen.”

---

## Fase 3 — Backoffice / monetization / revenue layer

### Doel
De tool wordt niet alleen een routingtool, maar een omzetversterker.

### Toepassing
- OF/Fansly DM-context
- supportvragen afvangen
- lage-waarde vragen uitfilteren
- whales sneller herkennen
- high-value klanten sneller escaleren
- creators ontlasten

### Later mogelijke elementen
- paid chat module
- coins / time / bundles / memberships
- whale scoring
- AI assist
- afspraakplanning voor 1-op-1

### Kernbelofte
“Meer omzet per lead en per operatoruur, met minder belasting voor de creator.”

---

# 13. Visuele systeemarchitectuur in tekst

```text
[ Social Sources ]
TikTok / Instagram / later others
        |
        v
[ Marketing Machine / Front Office ]
operator outreach
context
handoff
routing
        |
        v
[ Core Ops Cockpit / CreatorWorkboard ]
creators
channels
operators
assignments
policy
content source
handoff
        |
   --------------------------
   |                        |
   v                        v
[ Existing Chat ]     [ Premium Destinations ]
huidige chat          OnlyFans / Fansly / later others
   |                        |
   v                        v
[ Backoffice / Revenue Layer ]
support
filtering
priority
whale flagging
escalation
1-on-1 routing
        |
        v
[ Owner / Management ]
KPI's
team output
creator output
roadmap
profitability
