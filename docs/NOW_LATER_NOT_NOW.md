# CreatorWorkboard — NOW / NEXT / LATER / NIET NU

## Kernregel

**Intern bouwen we de hele route.  
Extern verkopen we eerst alleen de bewezen control layer.**

Dus:

- intern: social intake → routing → operatorflow → handoff → outcome
- extern NOW: workflow control layer bovenop bestaande chats

---

## Huidige stand

De volgende basis staat nu technisch:

- assignment-scoped operational access via `OperatorAssignment`
- deployed ops-app achter Docker + Traefik
- werkende loginflow achter reverse proxy
- creator materials als interne ops-slice
- admin-seeded V1 opportunity queue
- `ProfileOpportunity`
- `OutcomeEntry`
- server-side scoring service
- opportunity queue + detail views
- pagination
- tests op scoring, visibility, ordering en pagination

Belangrijke productgrens nu:

- opportunity creation blijft in V1 buiten app-flow
- records worden in V1 via Django admin aangemaakt
- de eerste wedge blijft de **control layer**
- social intake blijft intern

---

## NOW

## 1. Route 1 Control Layer stabiliseren in live gebruik

De control layer is niet meer alleen plan.  
Nu moet die zich bewijzen in echte operatorflow.

### Focus NOW
- queue
- context
- handoff
- next action
- scoring
- outcome discipline
- lichte recommendation support
- duidelijke operatorflow in echte chatsituatie

### Niet doen in NOW
- nieuwe modules toevoegen
- extra relaties toevoegen
- intake productiseren
- dashboards bouwen
- analyticslaag toevoegen

---

## 2. Live proof sprint in Mara

### Doel
Bewijzen dat de control layer in live operatorflow frictie verlaagt.

### Omgeving
- Mara chat 1
- Mara chat 2
- naast bestaande chats
- naast bestaande chat buddy

### Hoofdmetric
- tijd van handoff naar hervatting / eerste juiste actie

### Steunmetrics
- items zonder owner / next step
- stalled items
- outcome logging %
- tijd van nieuw item naar eerste actie

### Harde regel
Tijdens deze sprint zo min mogelijk andere variabelen veranderen.

Dus:
- geen grote buddy-wijzigingen
- geen payout-logica
- geen analyticsbouw
- geen extra workflowlagen

---

## 3. Internal social intake doorontwikkelen voor cashflow

De social intake is intern nog steeds relevant.

### Waarom
- verhoogt eigen cashflow
- voedt de operatorflow
- helpt de interne route

### Productgrens
Deze intake is **niet** onderdeel van de eerste betaalde wedge.

---

## 4. Eerste verkoopbare wedge scherp houden

### Wat we NOW verkopen
**CreatorWorkboard – Route 1 Control Layer**

### Wel
- operator queue
- context
- handoff
- next action
- scoring / prioritization
- risk/policy visibility light
- outcome log
- recommendation light

### Niet
- social intake adapter
- inbox replacement
- payout logic
- lead ownership logic
- analytics suite
- creator-facing tools
- brede integrations

---

## NEXT

## 1. Pilot proof sheet maken

Na de Mara-sprint:

- baseline-periode
- testperiode
- hoofdmetric
- steunmetrics
- 3 verdwenen fricties
- 3 resterende fricties
- 1 voorzichtige claim

Geen groot onderzoeksrapport.  
Wel één bruikbare pilot-proof sheet.

---

## 2. Commerciële validatie starten

Pas na live bewijs:

- ICP gebruiken in gesprekken
- qualification sheet gebruiken
- pilot offer gebruiken
- pricing als gespreksrange gebruiken
- alleen de control layer verkopen

### Saleszin
**We vervangen je chats niet. We maken je operatorflow bestuurbaar.**

---

## 3. V1-appflow gericht verbeteren

Op basis van live gebruik:

- queue simpeler maken
- detailflow scherper maken
- velden schrappen die niet gebruikt worden
- override alleen als uitzondering houden
- outcome discipline verbeteren

---

## LATER

## 1. Intake adapter als add-on

Pas later commercieel, nadat intern bewezen is dat de intake stabiel en rendabel genoeg is.

## 2. Beperkte operationele metrics

Later mogelijk:
- queue age
- stalled work
- missing handoff
- discipline in outcome logging

Niet als BI-suite.  
Wel als operationeel hulpmiddel.

## 3. AI suggestion layer verdiepen

Later mogelijk:
- betere scorevoorstellen
- compactere handoff
- betere recommended approach
- outcome label suggestie

AI blijft assisterend.  
Niet leidend.

## 4. Creator-facing tools en beperkte integraties

Alleen later, na bewijs en na stabiele workflow core.

---

## NIET NU

Niet bouwen of verkopen in deze fase:

- social intake als betaalde wedge
- inbox replacement
- CRM-verbreding
- payout logic
- lead attribution logic
- analytics dashboard
- BI
- governance suite
- creator-facing productlaag
- multitenancy
- brede SaaS-productisering
- AI-autopilot
- full social media beheerboard

---

## Harde beslisregel

Een onderdeel hoort alleen in NOW als het direct helpt bij:

- prioritering
- operatorhandeling
- handoff
- next action clarity
- stalled/blocking visibility
- outcome discipline

Alles daarbuiten is:
- intern
- later
- of helemaal niet

---

## Samenvatting

NOW is niet meer “een MVP bedenken”.

NOW is:

- de bestaande control layer live bewijzen
- de interne route voeden
- de commerciële wedge smal houden

Dat is de juiste fase.
