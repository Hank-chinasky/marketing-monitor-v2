# MVP_SCOPE_VS_V2_SCOPE_VS_VISION_SCOPE.md

## CreatorWorkboard — MVP vs V2 vs Vision Scope

**Status:** Actief  
**Laatste update:** 2026-03-28

---

## 1. Doel van dit document

Dit document bewaakt de scope.

Het voorkomt dat:
- visie als backlog wordt behandeld
- V2-ideeën als MVP worden gebouwd
- publieke of commerciële lagen te vroeg de basis vervuilen

De hoofdregel blijft:

**eerst een machine die intern echt werkt, pas daarna een machine die groot kan worden.**

---

## 2. Scope-definities

## MVP Scope
Wat minimaal nodig is om de interne operations machine echt bruikbaar te maken.

## V2 Scope
Wat logisch wordt nadat de basis stabiel en bruikbaar is, maar nog steeds dicht op de interne operatie ligt.

## Vision Scope
Wat richting geeft voor later, maar nu niet gebouwd moet worden.

---

## 3. MVP Scope

## Doel
Een bruikbare interne creator operations cockpit die dagelijks werkt.

## In scope
- creators
- channels
- operators
- assignments
- access policy
- handoff / workspace context
- duidelijke roles/scopes
- stabiele deployment
- operationeel bruikbare interface
- minder contextverlies

## Toegestane supportlaag
Een kleine publieke root-site is toegestaan binnen MVP/NOW, zolang die:

- klein blijft
- operationeel goedkoop blijft
- los staat van de ops-stack
- niet wordt behandeld als hoofdproduct

Dat betekent:
- simpele statische site
- enkele uitlegpagina’s
- basis contactpad
- routed via Traefik
- eigen stack

## Expliciet niet in MVP
- customer portal
- account-system
- multitenancy
- complexe billing
- brede marketing automation
- full chat-platform
- zware AI-laag
- tweetalige site-infrastructuur
- publieke site koppelen aan de interne app
- CMS-architectuur

---

## 4. V2 Scope

## Doel
De operationele machine verbreden zonder de basis te breken.

## Mogelijk in V2
- routing / conversation layer
- sterkere workspace-context
- betere intake-naar-operatie flow
- eenvoudige backoffice / monetization hooks
- logische rapportages
- beperkte extra beheerfuncties

## Voorwaarden
V2 mag pas wanneer:
- de operations cockpit dagelijks betrouwbaar is
- handoff bruikbaar is
- scope/ownership helder is
- deployment stabiel is
- de basis niet meer voortdurend verschuift

## Niet automatisch V2
Niet elk goed idee hoort automatisch in V2.
Als het geen directe operationele winst geeft, hoort het vaak nog steeds niet in de volgende fase.

---

## 5. Vision Scope

## Doel
Richting geven, niet bouwen.

## Vision kan bevatten
- customer portal
- account subdomain
- SaaS productisering
- multitenancy
- bredere monetization structuren
- grotere automation-lagen
- uitgebreidere AI-ondersteuning
- meertalige public presence
- grotere sales/marketingmachine

## Belangrijke regel
Vision is geen backlog.

Het bestaan van een vision-feature is geen reden om die nu al architectonisch te “reserveren”.

---

## 6. Public root-site scope-positie

## Wat de public site nu is
De publieke root-site is een kleine frontdoor voor:

- uitleg
- positionering
- contact

## Wat de public site nu niet is
- geen product surface
- geen app layer
- geen portal
- geen klantomgeving
- geen core roadmap-drijver

## Huidige toegestane scope
Wel:
- `creatorworkboard.com`
- `www.creatorworkboard.com`
- paar statische pagina’s
- contactformulier-shell
- Traefik routing
- losse stack

Niet:
- multilingual infra
- CMS
- form automation jungle
- koppeling aan interne ops-modellen
- publieke user accounts

---

## 7. Scope-beslisregels

Een item hoort alleen in MVP als het sterk helpt op minimaal drie van deze vier vragen:

1. helpt dit de huidige operatie direct?
2. verlaagt dit frictie of fouten?
3. maakt dit de basis sterker?
4. verhoogt dit complexiteit te vroeg?

Als vraag 1 t/m 3 niet duidelijk ja zijn, hoort het meestal niet in MVP.

---

## 8. Voorbeelden

## Hoort in MVP
- betere channel governance
- assignments verduidelijken
- workspace/handoff sterker maken
- operator flow verbeteren
- materials/download issues oplossen
- stabiele deploystructuur
- kleine public root-site als supportlaag

## Hoort eerder in V2
- routing / conversation layer
- eenvoudige backoffice hooks
- intake-context beter laten landen
- beperkte business reporting

## Hoort in Vision / niet nu
- portal
- account layer
- multitenancy
- breed AI-platform
- tweetalige marketingmachine
- customer self-service omgeving
- zware SaaS abstraction

---

## 9. Samenvatting

MVP is:
- interne bruikbaarheid
- duidelijke scope
- minder contextverlies
- betere handoff
- stabiele operatie

V2 is:
- verbreden van de machine zonder de basis te vervuilen

Vision is:
- richting voor later, niet de backlog van nu
