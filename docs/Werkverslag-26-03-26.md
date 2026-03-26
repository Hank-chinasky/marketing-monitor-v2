# Werkverslag — 26 maart 2026

## Onderwerp
Creator Materials MVP-slice + autorisatie-aanscherping

## Doel van vandaag
De interne operations cockpit bruikbaarder maken door materiaal direct op creator-niveau beschikbaar te maken voor operators, zonder meteen een creator portal of externe integraties te bouwen.

## Wat is gedaan

### 1. Runtime en werkomgeving bevestigd
We hebben eerst bevestigd waar de code draait en waar lokaal gewerkt wordt.

- Lokale runtime-repo:
  - `/home/jan/projects/marketing-monitor-v2`
- Live VPS runtime:
  - `/opt/commandcenter/apps/creatorworkboard-ops`

Daarna is verder gewerkt op de lokale repo en op een feature branch.

### 2. Feature branch gebruikt
Er is gewerkt op:

- `feature/creator-materials-commit1`

### 3. Creator Materials MVP gebouwd
Er is een eerste werkende materials-slice toegevoegd zodat materiaal direct aan een creator gekoppeld kan worden.

Toegevoegd:
- model `CreatorMaterial`
- uploadformulier voor materiaal
- admin-registratie
- materials-sectie op creator detailpagina
- beveiligde open/download route via de app
- migration voor `CreatorMaterial`

Functioneel resultaat:
- superadmin/admin kan materiaal uploaden op creator detail
- operator binnen scope kan materiaal zien
- operator binnen scope kan materiaal openen
- materiaal hangt aan de creator, niet aan een channel of losse notitie

### 4. Migration-conflict opgelost
Bij eerste run ontstond een migration-conflict doordat de materials-migration aan een oude migration-keten hing.

Oplossing:
- dependency van de materials-migration aangepast zodat deze volgt op:
  - `0009_creatorchannel_account_email_and_more`

Daarna:
- migrations liepen schoon
- testdatabase kon weer opbouwen

### 5. Autorisatie aangescherpt
Tijdens het testen bleek dat de codebase en tests niet meer consistent waren rond edit-permissies.

Er is daarom expliciet gekozen voor:
- creator/channel **detail** binnen scope zichtbaar voor operator
- creator/channel **edit** alleen voor admin

Doorgevoerd:
- `creator-update` admin-only
- `channel-update` admin-only

Reden:
- beheer en uitvoering moeten gescheiden blijven
- operator hoort later via een beperkte handoff/workspace-flow te werken
- full edit door operator vervaagt roles/scopes te vroeg

### 6. Tests in lijn gebracht met de productkeuze
De test-suite bevatte tegenstrijdige verwachtingen:
- sommige tests verwachtten dat operators edit mochten openen
- andere tests verwachtten admin-only gedrag

Dit is rechtgetrokken in lijn met de gekozen productregel:
- operator mag detail zien binnen scope
- operator mag edit niet openen

### 7. Lokale runtime succesvol gevalideerd
Na het oplossen van:
- migration conflict
- autorisatieconflict
- tegenstrijdige tests
- lokale `ALLOWED_HOSTS` / `CSRF` dev-setup
- bezette lokale poort
- ontbreken van lokale superadmin-login

is de branch lokaal succesvol gevalideerd.

Bevestigd:
- migrations draaien
- test-suite is groen
- superadmin kan inloggen
- materiaal kan geüpload worden
- operator ziet geüpload materiaal
- openen van materiaal werkt

## Observaties uit handmatige test

### Wat werkt goed
- uploadflow werkt
- operator ziet materiaal direct
- de basis is operationeel bruikbaar

### Directe UX-feedback
Huidige materials-weergave toont vooral links.
Dat werkt technisch, maar is nog niet optimaal voor dagelijkse operatie.

Opmerkingen uit test:
- creator en operator zien nu vooral een link
- bij klikken opent een afbeelding in een losse tab
- er is behoefte aan thumbnails / previews
- vooral voor foto’s en video’s is visuele herkenning nuttig

## Besluit op feedback

### NOW
- thumbnails / preview voor afbeeldingen en video’s
- eenvoudige viewer voor image/video in de app of overlay

### LATER
- lichte groepering of filtering op type
- eventueel albums/sets als praktijkgebruik dat echt vraagt

### NIET NU
- zware mapstructuren
- uitgebreid DAM/media-systeem
- rechtklik blokkeren als “beveiliging”

## Waarom
Deze slice levert directe operationele winst op:
- minder zoeken
- minder contextverlies
- sneller starten met werk
- materiaal op de juiste plek in de cockpit
- operator-first bruikbaarheid

## Belangrijke productkeuze
We bouwen hier:
- **wel** een interne materials-laag
- **niet** meteen een creator portal
- **niet** meteen Dropbox/Drive-integraties
- **niet** meteen een extern uploadplatform

## Huidige status
Branch technisch gezond.

Bevestigd:
- migrations groen
- tests groen
- handmatige uploadtest geslaagd
- operator-zichtbaarheid geslaagd

## Volgende stap
Volgende logische kleine verbetering:

- preview-first materials-weergave voor afbeeldingen en video’s
