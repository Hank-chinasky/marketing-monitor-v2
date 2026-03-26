# Deploymentverslag — creatorworkboard-ops

## Samenvatting
De deployment van `creatorworkboard-ops` op de VPS is werkend opgeleverd. Daarna zijn de eerste gebruikers en businessdata ingericht en is de volledige toegangsflow end-to-end gevalideerd.

De live applicatie draait nu onder:

`/opt/commandcenter/apps/creatorworkboard-ops`

## Uitgevoerde werkzaamheden

### 1. Applicatie opnieuw geplaatst op de VPS
De applicatie is opnieuw vanaf GitHub op de VPS uitgerold in:

`/opt/commandcenter/apps/creatorworkboard-ops`

Daarna is de Docker deployment opgebouwd en gestart. De app kwam correct online:
- migrations draaiden succesvol
- static files werden verzameld
- Gunicorn startte correct

### 2. Healthcheck-probleem opgelost
Na de eerste deploy bleek de container unhealthy te blijven.

**Oorzaak**
De Docker healthcheck faalde door een HTTP → HTTPS redirect op `/healthz/`, waardoor de containerstatus onterecht op `unhealthy` bleef staan.

**Oplossing**
De compose healthcheck is aangepast zodat de applicatie correct wordt gecontroleerd in combinatie met Traefik en HTTPS-redirect gedrag.

**Resultaat**
De app-container wordt nu correct als `healthy` gemarkeerd.

### 3. Traefik-routering hersteld
De Traefik-routering voor `ops.creatorworkboard.com` is hersteld en gevalideerd.

Bevestigd is dat:
- de container gekoppeld is aan `cc_public`
- de Traefik-labels actief en correct zijn
- de router zowel lokaal als extern correct matcht

### 4. Traefik basic auth hersteld
De eerste beschermlaag via Traefik basic auth werkte niet correct en is opnieuw ingericht.

**Uitgevoerd**
- nieuw wachtwoord gezet voor `traefik-auth@docker`

**Resultaat**
De eerste auth-laag voor de interne ops-omgeving werkt weer correct.

### 5. Django login- en CSRF-probleem opgelost
De Django user-authenticatie zelf werkte, maar browser-login faalde op CSRF-validatie.

**Oorzaak**
Niet Django zelf, maar de Traefik security header:

`Referrer-Policy: no-referrer`

Deze policy brak de CSRF-validatie tijdens login via HTTPS.

**Oplossing**
De referrer policy is aangepast naar een bruikbare variant die compatibel is met Django CSRF-beveiliging achter Traefik.

**Resultaat**
Login via de browser werkt nu correct.

### 6. Gebruikers ingericht
Na herstel van de loginflow zijn de eerste gebruikers ingericht:

- superuser `Superadmin`
- bestaande admin bevestigd
- operator-users als Django users aangemaakt

### 7. Operator- en creator-data ingericht
Tijdens validatie bleek dat creators niet direct aan Django `User` gekoppeld zijn, maar aan een apart `Operator` model.

Daarom zijn de volgende stappen uitgevoerd:
- echte `Operator` records aangemaakt voor de operator-users
- eerste `Creator` record aangemaakt
- creator gekoppeld aan `operator_manoel`

## Bevestigde eindstatus
Hiermee is bevestigd dat:

- de deployment werkt
- de healthcheck werkt
- de Traefik-routering werkt
- de Traefik basic auth werkt
- de Django login werkt
- de CSRF-validatie werkt
- operator/businessdata correct werkt
- het eerste creatorrecord correct is opgeslagen

## Belangrijk eindresultaat
De omgeving is nu operationeel met:

- werkende Docker deployment
- gezonde app-container
- werkende Traefik-bescherming
- werkende Django login
- functionerende operators en creators in de database

## Aanbevolen vervolgstappen
- echte creators en channels invoeren
- operator-wachtwoorden opnieuw zetten, omdat eerder wachtwoorden in shell/chat zijn gebruikt
- het nieuwe Traefik basic auth wachtwoord vastleggen in een password manager
- changelog en deploymentdocumentatie bijwerken
- admin/UI uitbreiden als creators/operators nog niet via alle gewenste schermen te beheren zijn

# Today Progress Report — 26 maart 2026

## Samenvatting
Vandaag is de eerste werkende `Creator Materials` MVP-slice toegevoegd aan CreatorWorkboard.

De focus lag bewust op directe interne operationele winst:
- materiaal direct op creator-niveau beschikbaar maken
- upload mogelijk maken vanuit de interne cockpit
- operator binnen scope materiaal laten zien en openen
- beheer en uitvoering strakker scheiden

## Wat is opgeleverd
- `CreatorMaterial` model toegevoegd
- materials-sectie toegevoegd op creator detail
- admin/superadmin kan materiaal uploaden
- operator binnen scope kan materiaal zien
- operator binnen scope kan materiaal openen
- migration-keten hersteld
- creator/channel edit flows naar admin-only gebracht
- test-suite weer volledig groen gekregen

## Belangrijke productbeslissing
Operator mag:
- detail zien binnen scope

Operator mag niet:
- full creator edit openen
- full channel edit openen

Beheer blijft admin-domein.  
Operator-uitvoering hoort later in een beperkte handoff/workspace-flow.

## Resultaat
- migrations groen
- test-suite groen
- handmatige runtime-validatie geslaagd
- upload werkt
- operator-zichtbaarheid werkt

## Belangrijkste feedback uit live test
De materials-flow werkt functioneel goed, maar de huidige UX is nog te link-gebaseerd.

Gewenste verbetering:
- thumbnails/previews voor foto en video
- simpeler herkennen welk materiaal juist is
- viewer in plaats van alleen openen in kale tab

## Volgende stap
Kleine UX-upgrade voor materials:
- preview-first weergave voor image/video

# Next Actions — na Creator Materials MVP

## Eerstvolgende kleine stap
Preview-first materials-weergave voor beeldmateriaal.

## Concreet
- thumbnails voor afbeeldingen
- video preview / player
- klik opent nette viewer in plaats van kale losse tab
- eenvoudige typeherkenning: image / video / other

## Waarom nu
De materials-flow werkt functioneel, maar de operator moet materiaal sneller visueel herkennen.

## Bewuste grens
Niet nu:
- mappen
- grote media library
- creator portal
- Dropbox/Drive
- rechtklik blokkeren
## Update — preview-first materials + multi-upload
Na de eerste werkende Creator Materials MVP is de materials-lijst verbeterd naar preview-first gedrag voor afbeeldingen en video’s.

Toegevoegd:
- image thumbnail preview
- video preview
- eenvoudige viewer/modal voor grotere weergave
- multi-select upload in één submit

Resultaat:
- materiaal is sneller visueel herkenbaar
- minder klikwerk nodig
- meerdere bestanden kunnen in één keer aan dezelfde creator worden gekoppeld
- operators blijven materiaal binnen scope zien en gebruiken

Bewuste grens:
- geen mappen
- geen zwaar mediabeheer
- geen right-click blokkering
- geen portal of externe integraties
