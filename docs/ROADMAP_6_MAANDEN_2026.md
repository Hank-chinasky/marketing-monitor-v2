# ROADMAP_6_MAANDEN_2026.md

## CreatorWorkboard — 6 maanden roadmap 2026

**Status:** Actief  
**Laatste update:** 2026-03-28

---

## 1. Doel van deze roadmap

Deze roadmap beschrijft de volgorde waarin CreatorWorkboard technisch en operationeel wordt uitgebouwd.

Belangrijk:
- dit is geen vision-backlog
- dit is geen productwenslijst
- dit is een scope-document voor wat de komende 6 maanden echt logisch is

De vaste volgorde blijft:

1. interne operations cockpit
2. routing / conversation layer
3. backoffice / monetization layer
4. pas daarna SaaS / productisering

---

## 2. Waar we nu staan

Huidige status:

- de interne ops-app draait op `ops.creatorworkboard.com`
- de publieke root-site draait op:
  - `creatorworkboard.com`
  - `www.creatorworkboard.com`
- publieke site is een kleine supportlaag, geen productsurface
- publieke site is bewust los van `creatorworkboard-ops`
- contactformulier UI staat klaar, maar is nog niet gekoppeld aan een live endpoint

Belangrijk:
de echte productkern is nog steeds de interne operations machine.

---

## 3. Principes voor de komende 6 maanden

### 3.1 Eerst operatie
Alles wat directe operationele winst geeft krijgt voorrang.

### 3.2 Geen premature productisering
SaaS, multitenancy en brede klantlagen horen niet in de huidige fase.

### 3.3 Publieke site blijft klein
De publieke site ondersteunt uitleg, positionering en contact.
De publieke site is niet de hoofdbacklog.

### 3.4 Roles, scopes en handoff zijn kern
De belangrijkste winst blijft komen uit:
- minder contextverlies
- betere overdracht
- heldere verantwoordelijkheid
- stabiele dagelijkse uitvoering

---

## 4. Roadmap-overzicht

## Fase 1 — Stabiliseren van de interne operations cockpit
**Periode:** nu / eerst

### Doel
De interne machine dagelijks betrouwbaar en bruikbaar maken.

### Focus
- creators
- channels
- operators
- assignments
- access policy
- handoff / workspace context

### Resultaat
- minder zoeken
- minder fouten
- betere operationele overdracht
- duidelijkere scope per operator

### Concreet
- creators/kanalen/operators verder aanscherpen
- assignment-flow logisch en stabiel maken
- channel governance duidelijker maken
- workspace/handoff bruikbaar maken
- download/materials issues oplossen
- deployment stabiel houden

---

## Fase 2 — Routing / conversation layer
**Periode:** na stabilisatie van de cockpit

### Doel
Inkomende communicatie en context beter laten landen in de operationele flow.

### Focus
- routeerbare gesprekken
- minder contextverlies tussen contact en uitvoering
- betere intake naar operationele context
- duidelijke scheiding tussen ruis en relevante signalen

### Resultaat
- minder losse context buiten het systeem
- betere overdracht van gesprek naar actie
- duidelijker wie iets oppakt

### Concreet
- logische conversation / routing objecten
- intake-context die bruikbaar is voor operators
- minimale AI alleen waar directe operationele winst duidelijk is
- geen full chat-platform bouwen

---

## Fase 3 — Backoffice / monetization layer
**Periode:** pas ná routinglaag

### Doel
Interne operatie koppelen aan businesswaarde zonder de basis te vervuilen.

### Focus
- backoffice-logica
- klantwaarde zichtbaar maken
- eenvoudige monetization hooks
- operationeel bruikbare rapportage

### Resultaat
- duidelijker zicht op waarde
- betere interne controle
- voorbereiding op omzetversnelling

### Concreet
- eenvoudige backoffice-surface
- basis voor pricing / packaging
- logische rapportages
- geen zware portal of account-systeem te vroeg

---

## Fase 4 — Pas daarna SaaS / productisering
**Periode:** alleen als fase 1 t/m 3 echt staan

### Doel
Productiseren wat intern bewezen heeft gewerkt.

### Focus
- hardening
- abstraheren
- productverpakking
- schaalbare ownership-modellen

### Resultaat
- pas dan nadenken over:
  - multitenancy
  - customer portal
  - account-layer
  - bredere productsurface

### Belangrijke regel
Visie is richting, geen backlog.

---

## 5. NOW / NEXT / LATER

## NOW
- interne operations cockpit verder versterken
- channel governance/workspace/handoff bruikbaar maken
- materials/download issues oplossen
- dagelijkse bruikbaarheid verhogen
- publieke root-site klein en stabiel houden
- contactformulier later technisch aansluiten, maar niet als hoofdwerk

## NEXT
- routing / conversation layer
- intake en contextoverdracht logischer maken
- minimale business/backoffice fundering voorbereiden
- publieke site copy later aanscherpen wanneer positionering scherper is

## LATER
- backoffice / monetization layer
- customer portal
- account subdomain
- SaaS-abstractie
- multitenancy
- bredere marketingmachine

---

## 6. Wat expliciet niet in NOW hoort

Niet in NOW:

- premature SaaS
- premature multitenancy
- full chat te vroeg
- zware AI te vroeg
- grote integraties zonder directe noodzaak
- CMS-gedreven public site
- tweetalige site-infrastructuur
- brede marketing- en automation-stack
- public site koppelen aan ops-logica

---

## 7. Publieke root-site binnen deze roadmap

De publieke root-site is nu live en toegestaan als kleine supportlaag.

### Doel van de public site
- uitleggen wat CreatorWorkboard is
- laten zien voor wie het bedoeld is
- contact mogelijk maken
- geloofwaardige publieke frontdoor vormen

### Belangrijke beperking
De public site is:
- niet het product
- niet de MVP
- niet de hoofdroadmap
- niet de plek waar complexiteit naartoe mag lekken

### Huidige status
- apex en `www` live
- Engelse page set actief
- contactformulier nog niet gekoppeld aan een live endpoint

---

## 8. Beslisregel voor nieuwe ideeën

Een idee hoort alleen in NOW als het sterk helpt op minimaal deze punten:

1. helpt dit de huidige operatie direct?
2. verlaagt dit frictie of fouten?
3. maakt dit de basis sterker?
4. verhoogt dit complexiteit te vroeg?

Als vraag 1 t/m 3 niet sterk met ja worden beantwoord, hoort het meestal niet in NOW.

---

## 9. Samenvatting

De komende 6 maanden draaien niet om een mooie brede productlaag.

Ze draaien om:
- interne bruikbaarheid
- minder contextverlies
- betere handoff
- duidelijke roles/scopes
- stabiele deployment
- simpele en veilige operatie

De public site mag bestaan.
De interne machine blijft de prioriteit.
