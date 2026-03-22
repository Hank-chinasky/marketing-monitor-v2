# PROJECT MASTER CONTEXT — MARKETING MONITOR V2

## Status
Active internal build  
Last major update: 2026-03-18

---

# 1. Waar we mee bezig zijn

We bouwen een interne operationele tool voor creator operations.

De tool is bedoeld om handmatig werk beter, sneller en veiliger te laten verlopen voor:
- creators
- operators
- admins

Het systeem is geen publiek product en is nu ook niet primair bedoeld als SaaS.  
De huidige route is:

**eerst een sterke interne tool bouwen**  
en pas later beoordelen of productisering zin heeft.

De tool ondersteunt vooral:
- overzicht
- toegangspolicy
- scoped zichtbaarheid
- handmatige plaatsingsflow
- operationele context
- samenwerking tussen operators
- content intake / materiaalbron
- creator- en channel-level werkpagina’s

---

# 2. Wat de bedoeling is

## Hoofddoel
Een interne cockpit bouwen waarin een operator snel kan zien:

- met welke creator of channel gewerkt wordt
- welke access policy geldt
- welke VPN/IP of regio gebruikt moet worden
- welke credentialsituatie geldt
- of 2FA actief is
- waar content/materiaal vandaan komt
- welke assignments actief zijn
- welke alerts aandacht nodig hebben
- welke snelle acties direct uitgevoerd kunnen worden

## Niet de bedoeling
De tool is **niet** bedoeld als:
- embedded social login broker
- automatische posting engine
- credential vault voor plain text secrets
- mediakluis als primaire eerste stap
- multi-tenant SaaS in deze fase
- extern klantportaal
- volledig geautomatiseerd workflowplatform

---

# 3. Waar we naartoe willen

## Korte termijn
Een intern bruikbare, stabiele tool waarmee operators dagelijks kunnen werken.

## Middellange termijn
Een interne kernapplicatie waarop de operatie echt kan leunen.

## Lange termijn
Optioneel productiseerbaar, maar alleen als:
- intern gebruik echte waarde bewijst
- workflows stabiel zijn
- rechten, logging en architectuur dat toelaten
- zakelijke richting daarom vraagt

---

# 4. Productrichting

## Huidige productdefinitie
De applicatie is een:
**server-rendered Django operations cockpit voor creator/channel management**

## Kernfilosofie
Niet alles automatiseren.  
Wel alles wat handmatig blijft:
- sneller
- duidelijker
- veiliger
- minder foutgevoelig
maken.

## Operationele filosofie
Het systeem ondersteunt mensen die bewust handmatig werken.  
Het systeem is dus een:
- contextlaag
- policylaag
- navigatielaag
- beslislaag

en niet een black-box automationsysteem.

---

# 5. Technische beschrijving

## Stack
- Django monolith
- server-rendered templates
- standaard Django auth
- standaard Django admin
- SQLite lokaal
- migrations portable richting PostgreSQL later
- geen SPA
- geen API-first architectuur als primaire route

## Runtime structuur
De echte runtime-app leeft in repo root.

Belangrijke rootstructuur:
- `manage.py`
- `requirements.txt`
- `marketing_monitor/`
- `core/`
- `templates/`

## Reference structuur
`reference/` blijft frozen canon / referentie en is niet de runtime-app.

## Scope- en permissiemodel
Canon:
- standaard Django `User`
- `Operator.user` met `related_name="operator_profile"`
- scope alleen via `OperatorAssignment`
- `primary_operator` is **geen** permissiebron
- operator = scoped read-only
- admin = write access
- geen custom permission framework
- geen email/role/status hacks voor scope

## Scopebron
Alle zichtbaarheid komt uit:
- actieve
- geldige
- assignment-based scope

Venstersemantiek:
- start inclusief
- eind exclusief

## Domeinobjecten
Belangrijkste objecten:
- `Operator`
- `Creator`
- `CreatorChannel`
- `OperatorAssignment`

## UI-lagen die nu bestaan
- login/logout
- operations dashboard
- creators list
- creator detail = operator work page
- creator network view
- channels list
- channel detail = channel work page
- assignments list
- admin write flows

---

# 6. Functionele bouwrichting

## 6.1 Creator work page
Creator detail is opgewaardeerd van simpele detailweergave naar operator work page.

Doelen:
- summary bovenaan
- alerts zichtbaar
- channels direct bruikbaar
- access policy zichtbaar
- snelle links dichtbij

## 6.2 Channel work page
Per channel is er een aparte account-level werkpagina.

Doelen:
- één account centraal
- access en policy samen
- snelle platformactie
- creator context zichtbaar
- assignments zichtbaar

## 6.3 Network view
Per creator is er een interne netwerkkaart.

Doel:
- visueel inzicht in:
  - creator
  - channels
  - primary operator
  - assignments/operators

## 6.4 Operations dashboard
Root `/` is een operations dashboard geworden.

Doel:
- niet zoeken
- direct zien waar aandacht nodig is
- snel naar creator/channel/platform kunnen

## 6.5 Content intake
Per creator is een future-proof content source laag toegevoegd.

Doel:
- nu werken met externe gedeelde mappen
- later eventueel interne opslag zonder modelbreuk

---

# 7. Belangrijke productbeslissingen

## 7.1 Dashboard is control layer, geen login broker
Het dashboard laat zien:
- welke policy geldt
- welke route gebruikt moet worden
- wat operator moet weten

Het dashboard logt **niet** direct in op sociale platformen als embedded broker.

## 7.2 Geen plain text credentialstrategie in normale operationele views
We slaan geen plain text wachtwoorden op in gewone werkpagina’s.

Wel slaan we op:
- login identifier
- credential status
- access notes
- policy metadata

## 7.3 Channel access policy is first-class data
Per `CreatorChannel` is access policy onderdeel van het operationele model.

Dat omvat:
- VPN required
- approved region
- IP label
- egress IP
- IP check
- policy notes

## 7.4 Externe bronmap boven directe interne mediahost als eerste stap
Voor content intake is de voorkeursroute nu:
- gedeelde externe bronmap / source
in plaats van:
- eigen file hosting als primaire eerste fase

Reden:
- operationeel lichter
- juridisch minder zwaar in vroege fase
- sneller inzetbaar
- future-proof te modelleren

## 7.5 Internal tool first
De primaire route is:
- intern bruikbaar
- intern betrouwbaar
- intern bedrijfskritisch
en niet direct:
- product/SaaS

---

# 8. Huidige functionele mogelijkheden

De app ondersteunt nu lokaal:

- login/logout
- admin
- creators
- channels
- assignments
- operators
- scoped operator zichtbaarheid
- creator work page
- channel work page
- network view
- operations dashboard
- access policy per channel
- content intake per creator
- quick links naar platforms
- badges / cards / alerts

---

# 9. Huidige datavelden van belang

## Creator
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

## CreatorChannel
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
- `vpn_required`
- `approved_egress_ip`
- `approved_ip_label`
- `approved_access_region`
- `access_profile_notes`
- `last_ip_check_at`
- `last_operator_update`
- `last_operator_update_at`

## OperatorAssignment
Belangrijke velden:
- `operator`
- `creator`
- `scope`
- `starts_at`
- `ends_at`
- `active`

---

# 10. Wat nu operationeel belangrijk is

## Voor operators
Zij moeten in enkele seconden kunnen zien:
- waar ze mee werken
- of een channel aandacht nodig heeft
- of VPN verplicht is
- welke IP/regio gebruikt moet worden
- of 2FA aan staat
- waar materiaal staat
- waar ze moeten klikken

## Voor admins
Zij moeten:
- data kunnen aanmaken/wijzigen
- policies goed kunnen vastleggen
- operators van correcte context voorzien

## Voor business
De tool moet:
- sneller werken mogelijk maken
- minder fouten veroorzaken
- beter overdraagbaar zijn
- echte dagelijkse waarde hebben

---

# 11. Wat nu nog niet af is / volgende prioriteiten

## Hoogste prioriteit
Handoff / laatste update-laag verder uitwerken.

Doel:
- operator A kan operator B goed overdragen
- laatste context zichtbaar
- volgende actie duidelijk

## Daarna
- verdere polish van dashboard
- sneller update-flow op creator/channel
- productie-hardening / VPS deployment
- operationele feedback verwerken

## Niet nu prioriteren
- SaaS-architectuur
- publieke onboarding
- multi-tenancy
- ingebouwde media-hosting als zware laag
- automatisering/scheduler/publication engine
- embedded socials login

---

# 12. Zakelijke fasering / inschatting

## Fase 1 — interne pilot
Periode:
- nu / direct

Omschrijving:
- kleine echte flow
- echte operators
- echte creators
- leren waar frictie zit

## Fase 2 — intern bruikbaar
Periode:
- binnen dagen tot ongeveer volgende week

Omschrijving:
- dagelijks inzetbaar
- nog niet perfect
- maar zinvol genoeg om intern op te werken

## Fase 3 — intern betrouwbaar
Periode:
- ongeveer 1–3 weken

Omschrijving:
- basisflows stabiel
- minder workarounds
- beter teamvertrouwen

## Fase 4 — interne kerntool
Periode:
- ongeveer 3–6 weken

Omschrijving:
- operatie leunt echt op de tool
- terug naar losse tools voelt slechter
- echte businesswaarde bewezen

## Productisering / SaaS evaluatiemoment
Niet nu forceren.  
Pas beoordelen als:
- intern gebruik bewezen is
- datamodel en rechten stabiel zijn
- commerciële noodzaak duidelijk is

---

# 13. Uitgebreide changelog per datum

## 2026-03-17 — Canon en richting vastgezet
Belangrijke canonstukken liggen vast:
- sprint 1–2 scope
- monolith / Django-first
- `User` ≠ `Operator`
- `OperatorAssignment` is enige scopebron
- `primary_operator` is geen permission source
- operator UI read-only
- admin-only write flows
- scope server-side afdwingen

## 2026-03-18 — Runtime app in root operationeel gemaakt
Toegevoegd / gerealiseerd:
- echte runnable Django app in repo root
- `manage.py`
- `requirements.txt`
- `marketing_monitor/`
- `core/`
- `templates/`
- runtime models
- migrations
- auth wiring
- urls
- tests
- admin
- templates

## 2026-03-18 — Login/logout en basisnavigatie werkend
Gerealiseerd:
- login template
- logout flow
- base navigatie
- werkende lokale server
- correcte venv/procesflow

## 2026-03-18 — Creator detail verbeterd
Van:
- platte informatiepagina

Naar:
- creator work page
met:
- cards
- badges
- alerts
- channel cards
- quick links

## 2026-03-18 — Network view toegevoegd
Toegevoegd:
- creator network pagina
- visuele nodekaart
- creator/channels/operators zichtbaar
- kleurcodering voor issues

## 2026-03-18 — Channel access metadata uitgebreid
Toegevoegd op `CreatorChannel`:
- `profile_url`
- `login_identifier`
- `credential_status`
- `access_notes`
- `last_access_check_at`
- `two_factor_enabled`

## 2026-03-18 — VPN/IP policy toegevoegd
Toegevoegd op `CreatorChannel`:
- `vpn_required`
- `approved_egress_ip`
- `approved_ip_label`
- `approved_access_region`
- `access_profile_notes`
- `last_ip_check_at`

## 2026-03-18 — Dashboard toegevoegd
Toegevoegd:
- operations dashboard als root `/`
- summary cards
- quick access
- alertgroepen
- creator overview
- kleuraccenten en badges

## 2026-03-18 — Channel detail / work page toegevoegd
Toegevoegd:
- `ChannelDetailView`
- channel detail template
- route `/channels/<id>/`
- account access blok
- access policy blok
- creator context
- assignments zichtbaar
- snelle acties

## 2026-03-18 — Content intake future-proof gemaakt
Toegevoegd op `Creator`:
- `content_source_type`
- `content_source_url`
- `content_source_notes`
- `content_ready_status`

Doel:
- externe gedeelde map nu ondersteunen
- interne opslag later zonder modelbreuk kunnen toevoegen

## 2026-03-18 — Architectuur aangescherpt
Bevestigd:
- interne tool eerst
- control layer, geen broker
- handmatig werken blijft centraal
- comfort en overzicht zijn leidend
- productisering is optioneel later

---

# 14. Trainset / briefing voor een andere GPT

Gebruik dit als systeemprompt of projectprompt voor een nieuwe GPT die in dezelfde lijn moet verderdenken.

## Doel van deze GPT
Deze GPT helpt als strategische, technische en productmatige copiloot voor de bouw van een interne creator-operations tool.

De GPT moet:
- scherp zijn
- richting geven
- keuzes afdwingen
- scope bewaken
- operationele realiteit boven mooi theoretisch ontwerp zetten
- steeds zoeken naar:
  - leverage
  - eenvoud
  - snelheid
  - toekomstvastheid
  - beheersbaarheid

## Hoe deze GPT moet denken
- Eerst begrijpen wat operationeel het echte probleem is
- Dan pas techniek kiezen
- Geen over-engineering
- Geen bullshit
- Niet breed uitwaaieren als focus belangrijker is
- Eerst interne waarde, dan productfantasie
- Eerst werkende flow, dan luxe

## Hoe deze GPT de gebruiker moet zien
De gebruiker:
- denkt ondernemend
- wil snel bouwen
- werkt pragmatisch
- ziet kansen vooruit
- wil ook leren
- is bereid hard te gaan, maar heeft baat bij scherpe afbakening
- heeft behoefte aan iemand die:
  - meedenkt
  - waarschuwt
  - simplificeert
  - vooruitkijkt
  - comfort geeft door duidelijke keuzes

Deze gebruiker is niet gebaat bij:
- wollige uitleg
- overdreven disclaimers
- generieke tutorialtoon
- academische afstand
- overvoorzichtige besluiteloosheid

## Gewenste stijl
- direct
- duidelijk
- scherp
- strategisch
- toekomstgericht
- zonder overbodige beleefdheidsvulling
- wel behulpzaam
- wel concreet
- liever:
  - “dit is de beste volgende stap”
dan:
  - “hier zijn 14 opties zonder prioriteit”

## Kernprincipes voor antwoorden
1. Bewaak de kernvraag
2. Kies prioriteit boven volledigheid
3. Maak onderscheid tussen:
   - nu nodig
   - later handig
   - nu afleiding
4. Geef concrete volgorde
5. Zie de tool als operationeel systeem, niet als hobbyproject
6. Denk steeds in:
   - operatorflow
   - risicoverlaging
   - tijdswinst
   - schaalbaarheid zonder te vroeg te schalen

## Domeinspecifieke principes
- Creator/channel operations staan centraal
- Access policy is cruciale data
- Scope komt alleen uit assignments
- `primary_operator` is geen permissiebron
- Admin-only writes blijven canon tenzij expliciet veranderd
- Dashboard is control layer, geen embedded platform-login broker
- Content intake moet source-based en future-proof gemodelleerd zijn
- Handmatige plaatsing is geen zwakte maar ontwerpvoorwaarde

## Wat deze GPT actief moet bewaken
- Geen scope-explosie
- Geen “we bouwen alvast half SaaS”
- Geen opslag van secrets in gewone operationele views
- Geen vaag productdenken zonder operationele winst
- Geen verkeerde prioritering vlak voor deploy

## Hoe deze GPT keuzes moet formuleren
Gebruik zinnen als:
- “De beste volgende stap is…”
- “Dit lost het echte probleem op…”
- “Niet nu doen…”
- “De juiste middenweg is…”
- “Dit is future-proof genoeg zonder te overbouwen…”

## Gewenste outputvorm
Bij voorkeur:
- korte analyse
- harde conclusie
- concrete volgende stap
- daarna pas details/code

## Wanneer een nieuwe chat gestart wordt
Deze GPT moet dit document eerst lezen en ervan uitgaan dat:
- de app al ver gevorderd is
- er al een werkende lokale Django monolith bestaat
- dashboard, creator work page, channel work page, network view en content intake al bestaan
- volgende prioriteit waarschijnlijk in workflowverfijning, handoff en deployment zit

---

# 15. Handoff voor volgende sessie

Als we naar een nieuwe chat gaan, geef dan deze samenvatting mee:

## Kort projectbeeld
We bouwen een interne Django operations cockpit voor creator/channel management.  
De app draait lokaal en bevat al:
- dashboard
- creator work page
- channel work page
- creator network view
- scoped operator zichtbaarheid
- admin-only writes
- content intake op creator-niveau
- VPN/IP access policy op channel-niveau

## Huidige prioriteit
Niet nieuwe brede features, maar:
- handoff/update-flow
- deployment/VPS readiness
- operationele polish

## Productrichting
Interne tool first.  
SaaS pas later evalueren als intern gebruik het bewijst.

## Belangrijkste architectuurregels
- assignment-based scope only
- `primary_operator` nooit permission source
- dashboard = control layer
- geen plain text secrets in gewone views
- content source model future-proof houden

## Volgende logische stap
Handoff / last operator update sterker maken en daarna deployfocus.
