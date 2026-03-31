# CreatorWorkboard — Roadmap 6 Maanden 2026

## Hoofdrichting

CreatorWorkboard wordt niet tegelijk gebouwd als:

- interne operations cockpit
- social intake product
- CRM
- SaaS-platform
- analyticslaag
- AI-suite

De vaste volgorde blijft:

1. interne operations cockpit
2. routing / conversation layer
3. backoffice / monetization layer
4. pas daarna SaaS / productisering

---

## Roadmapdoel voor deze 6 maanden

Binnen 6 maanden moet CreatorWorkboard:

- intern dagelijks bruikbaar zijn
- contextverlies aantoonbaar verlagen
- handoff structureel verbeteren
- live bewijs leveren in een echte chatomgeving
- een eerste smalle betaalde wedge geloofwaardig kunnen ondersteunen
- intern de sociale intake-route blijven ondersteunen voor cashflow

Niet meer.

---

## Fase 1 — Fundament en scopebasis

### Status
Gereed

### Bereikt
- assignment-scoped operational access via `OperatorAssignment`
- central scope helpers
- admin breadth behouden via bestaande staff/superuser semantics
- creator/channel toegang consistent gemaakt
- operations dashboard scoped gemaakt
- tests op scopegedrag toegevoegd

### Resultaat
De basis voor veilige en eenvoudige operationele toegang staat.

---

## Fase 2 — Ops deployment en stabilisatie

### Status
Gereed

### Bereikt
- Docker deployment werkend
- Traefik routing werkend
- basic auth werkend
- CSRF/login achter reverse proxy hersteld
- healthcheck stabiel
- Gunicorn + collectstatic + migrations bevestigd
- protected access chain gevalideerd

### Resultaat
De ops-app draait stabiel live op de VPS.

---

## Fase 3 — Eerste ops-slices in productie

### Status
Gedeeltelijk gereed

### Bereikt
- creator materials slice gebouwd
- scoped operator visibility op materials
- preview-first materials UX
- bulk delete route hersteld
- `ProfileOpportunity` toegevoegd
- `OutcomeEntry` toegevoegd
- queue + detail views toegevoegd
- server-side scoring service toegevoegd
- queue pagination toegevoegd
- V1 kansen kunnen via admin worden aangemaakt

### Productgrens
De app is nog geen brede operations suite.  
De control layer bestaat, maar moet zich nu bewijzen in echt gebruik.

---

## Fase 4 — Live proof sprint in Mara

### Status
Nu aan de beurt

### Doel
De bestaande control layer testen in live operatorflow.

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

### Resultaat dat nodig is
Niet “mooie demo”, maar:
- aantoonbaar strakkere operatorflow
- minder contextverlies
- duidelijkere handoff
- betere next action discipline

---

## Fase 5 — Product aanscherpen op live gebruik

### Periode
Na de Mara proof sprint

### Doel
Niet verbreden, maar versimpelen.

### Focus
- queue compacter maken
- detailflow strakker maken
- velden schrappen die niet helpen
- scoring voorspelbaar houden
- override uitzonderlijk houden
- operatorfrictie verlagen

### Resultaat
Een pilotwaardige Route 1 Control Layer.

---

## Fase 6 — Eerste commerciële wedge testen

### Periode
Na live bewijs

### Propositie
**CreatorWorkboard – Route 1 Control Layer**

### Belofte
**We vervangen je chats niet. We maken je operatorflow bestuurbaar.**

### Wel verkopen
- operator queue
- context
- handoff
- next action
- scoring / prioritization
- outcome discipline
- recommendation light

### Niet verkopen
- social intake adapter
- inbox replacement
- payout logic
- analytics suite
- creator-facing tools
- brede integrations

### Doel
Valideren of teams met meerdere operators deze control layer herkennen als direct bruikbaar en betaalbaar.

---

## Parallelle interne route

Naast de wedge blijft intern belangrijk:

- social intake adapter
- intake capture
- human-in-the-loop routing
- eigen cashflow verhogen

Belangrijk:
dit hoort **wel** bij de interne route, maar **niet** bij de eerste betaalde wedge.

---

## Modulevolgorde

## Eerst
- scope
- deployment stabiliteit
- workflow core
- handoff
- queue
- context
- outcome discipline

## Dan
- live proof
- product aanscherpen
- commerciële pilot

## Pas daarna
- intake adapters als add-on
- beperkte operational metrics
- creator-facing tools
- integrations
- bredere productisering

---

## Risicoregels voor de roadmap

### Grootste risico’s
- tijdens live test alsnog verbreden
- social intake te vroeg meeverkopen
- prestaties claimen zonder meetdiscipline
- ICP te breed kiezen
- seat-based SaaS-logica te vroeg forceren
- intern nuttige modules verwarren met extern verkoopbare modules

### Harde route
Bouw intern de hele route.  
Verkoop extern eerst alleen het veiligste, bewezen deel daarvan.

---

## Samenvatting

De komende 6 maanden draaien niet om een brede launch.

Ze draaien om:

- interne bruikbaarheid
- live bewijs
- cashflow-ondersteuning intern
- smalle commerciële wedge
- beperkte commerciële validatie

Dat is de juiste volgorde.
