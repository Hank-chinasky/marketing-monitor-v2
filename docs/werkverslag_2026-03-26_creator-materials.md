# Werkverslag — 26 maart 2026
## Onderwerp
Creator Materials MVP + autorisatie-aanscherping + test- en migration-herstel

## Context
De huidige fase van CreatorWorkboard blijft:
1. interne operations cockpit
2. routing / conversation layer
3. backoffice / monetization layer
4. pas daarna SaaS / productisering

De toevoeging van creator materials is beoordeeld als NOW, omdat dit direct helpt bij:
- sneller starten met werk
- minder contextverlies
- betere handoff
- meer dagelijkse bruikbaarheid voor operators

## Doel van deze slice
Materiaal direct op creator-niveau beschikbaar maken in de interne cockpit, zodat operators niet hoeven te zoeken in losse notities, tabs of externe tools.

## Scope van deze slice
Wel:
- creator-gebonden materiaalopslag
- interne upload door admin/superadmin
- zichtbaarheid voor operator binnen scope
- openen van materiaal vanuit de app

Niet:
- creator portal
- Dropbox / Drive integraties
- uitgebreide media library
- mapstructuren
- creator self-upload flow
- zware rechtenlaag

## Technische uitvoering
Er is gewerkt op branch:

`feature/creator-materials-commit1`

Toegevoegd / aangepast:
- `core/models.py`
- `core/forms.py`
- `core/admin.py`
- `core/material_views.py`
- `core/urls.py`
- `templates/creators/creator_detail.html`
- `core/migrations/0005_creatormaterial.py`

## Wat functioneel is toegevoegd
### CreatorMaterial
Nieuw model voor creator-gebonden materiaal.

Velden:
- creator
- file
- label
- notes
- uploaded_by
- uploaded_at
- active

### Creator detail materials-sectie
Op creator detail is een materials-blok toegevoegd met:
- uploadformulier
- lijst met bestaande materialen
- label/bestandsnaam
- notitie
- uploadtijd
- uploader
- open/download-link

### Scopegedrag
- admin/superadmin kan uploaden
- operator binnen scope kan materiaal zien
- operator binnen scope kan materiaal openen

## Problemen die onderweg zijn opgelost

### 1. Migration conflict
Eerste versie van de materials-migration hing aan een oude migration-keten en veroorzaakte meerdere leaf nodes.

Probleem:
- `0005_creatormaterial`
- `0009_creatorchannel_account_email_and_more`

Oplossing:
- dependency aangepast zodat materials volgt op `0009`

Gevolg:
- migrations lopen schoon
- testdatabase bouwt weer correct op

### 2. Autorisatieconflict in code en tests
Tijdens de test-run bleek dat de codebase en test-suite elkaar tegenspraken.

De ene set tests impliceerde:
- operator mag edit openen

De andere richting en productlogica vereisten:
- edit blijft admin-only

Gekozen productregel:
- operator mag detail zien binnen scope
- operator mag geen full creator/channel edit openen
- admin beheert structuur
- operator werkt later via beperkte operationele flows

Doorgevoerd:
- creator-update admin-only
- channel-update admin-only
- scope-tests aangepast op deze expliciete keuze

### 3. Lokale dev-frictie
Bij lokale runtime-validatie kwamen extra omgevingsproblemen naar voren:
- `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`
- poort 8000 al in gebruik
- lokale superadmin-login ontbrak
- lokaal bestond niet automatisch dezelfde data als op VPS

Deze zijn opgelost zodat handmatige validatie lokaal mogelijk werd.

## Handmatige validatie
Lokaal bevestigd:
- inloggen als superadmin werkt
- creator detail opent
- materials-sectie is zichtbaar
- bestand uploaden werkt
- operator ziet geüpload materiaal
- materiaal openen werkt

## Feedback uit de runtime-test
De feature is functioneel goed genoeg voor dagelijks intern gebruik, maar de presentatie van materiaal is nog te minimaal.

Huidige situatie:
- foto/video worden vooral als link getoond
- openen gaat in een losse tab
- visuele herkenning is beperkt

## Besluit op feedback
### NOW
- thumbnails/previews voor afbeelding en video
- eenvoudige viewer/modal voor media

### LATER
- lichte filtering of typegroepering
- eventueel albums/sets als praktijkgebruik dit echt nodig maakt

### NIET NU
- mappenstructuur
- zwaar mediabeheer
- rechtklik blokkeren als pseudo-beveiliging

## Productkeuze die expliciet vastligt
Deze slice is:
- wel interne operations-verbetering
- niet het begin van een creator portal
- niet het begin van externe integraties
- niet het begin van een volledig media management systeem

## Conclusie
De materials-MVP staat technisch goed:
- migrations groen
- tests groen
- handmatige flow gevalideerd

De eerstvolgende logische verbetering is een kleine UX-laag bovenop deze slice:
- preview-first materials-weergave voor foto en video
