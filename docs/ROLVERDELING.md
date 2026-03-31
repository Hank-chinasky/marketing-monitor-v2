# CreatorWorkboard — Rolverdeling

## Kernregel

CreatorWorkboard wordt gebouwd met duidelijke rolgrenzen.

Niet iedereen beslist over alles.  
Niet iedereen bouwt tegelijk aan visie, operatie, product en verkoop.

---

## 1. Founder / Product Owner

### Verantwoordelijk voor
- scope bewaken
- fasekeuzes maken
- prioriteiten bepalen
- live testomgeving organiseren
- commerciële positionering bepalen
- beslissen wat NOW / NEXT / LATER / NIET NU is

### Concreet in deze fase
- de control layer smal houden
- social intake intern houden
- live proof sprint in Mara aansturen
- claims pas doen op basis van gemeten bewijs
- de eerste wedge niet vervuilen met intake, payout of analytics

### Niet doen
- tijdens de sprint scope uitbreiden
- losse ideeën meteen als backlog behandelen
- social intake meeverkopen in de eerste wedge
- een harde performanceclaim doen zonder bewijs

---

## 2. Coder / Builder

### Verantwoordelijk voor
- stabiel bouwen binnen de afgesproken scope
- server-side implementatie
- tests toevoegen en draaiend houden
- simpele en betrouwbare uitvoering
- geen premature architectuur

### Concreet in deze fase
- opportunity layer in `core/` onderhouden en aanscherpen
- queue, detailflow, scoring en outcomes stabiel houden
- bugs oplossen die live gebruik blokkeren
- kleine UX-verbeteringen doen op basis van echte operatorflow
- deployment veilig houden binnen bestaande Docker/Traefik setup

### Niet doen
- creator/channel-relaties toevoegen “voor later”
- analytics bouwen
- intake adapter productiseren
- AI-laag verbreden
- brede refactors doen zonder directe operationele winst

---

## 3. Operator / Tester

### Verantwoordelijk voor
- echte dagelijkse flow gebruiken
- handoff discipline volgen
- outcomes consistent loggen
- frictie teruggeven uit echt gebruik
- signaleren waar context nog lekt

### Concreet in deze fase
- werken in Mara’s chatomgeving
- beide chatflows testen
- echte items gebruiken
- owner / next step discipline volgen
- feedback geven op queue, detail en handoff

### Niet doen
- workflow buiten het testkader zwaar veranderen
- nieuwe wensen direct als feature pushen
- zonder logging conclusies trekken

---

## 4. AI-assistent

### Verantwoordelijk voor
- coder helpen met uitwerken
- documentatie schrijven en bijwerken
- scorelogica vertalen naar code
- tests en templates versnellen
- scope scherp houden in voorstellen

### Mag wel
- boilerplate schrijven
- docs structureren
- refactors voorstellen
- testcases uitschrijven
- UI-copy versimpelen
- changelog en strategische docs gelijktrekken

### Mag niet
- scope bepalen buiten productgrenzen
- productgrenzen verbreden
- vision-features als MVP presenteren
- commerciële claims verzinnen zonder bewijs

---

## 5. Live proof owner

### Verantwoordelijk voor
- baseline vastleggen
- metrics bijhouden
- proof sprint structureren
- pilot proof sheet opstellen

### Hoofdmetric
- tijd van handoff naar hervatting / eerste juiste actie

### Steunmetrics
- items zonder owner / next step
- stalled items
- outcome logging %
- tijd van nieuw item naar eerste actie

### Niet doen
- meetmethode veranderen midden in sprint
- meerdere grote variabelen tegelijk aanpassen
- buddy + layer + proces tegelijk zwaar wijzigen
- harde claims trekken zonder meetbasis

---

## 6. Commerciële rol

### Verantwoordelijk voor
- ICP bewaken
- prospectkwalificatie
- pilotgesprekken
- offer positionering
- wedge klein houden

### Eerste verkoopbare belofte
**We vervangen je chats niet. We maken je operatorflow bestuurbaar.**

### Niet verkopen
- social intake adapter
- payout logic
- lead ownership logic
- inbox replacement
- analytics suite
- AI-autopilot

---

## 7. Internal cashflow route owner

### Verantwoordelijk voor
- interne social intake-route bewaken
- zorgen dat de interne route cashflow ondersteunt
- onderscheid bewaken tussen intern nuttig en extern verkoopbaar

### Concreet in deze fase
- social intake intern doorontwikkelen waar dat direct geld ondersteunt
- human-in-the-loop intake blijven testen
- routing naar de operatorflow bruikbaar houden

### Niet doen
- deze intake automatisch in de betaalde wedge trekken
- regelzware intake-logica verkopen voordat die hard bewezen is

---

## Beslisvolgorde

Elke nieuwe vraag of feature gaat langs deze volgorde:

1. helpt dit de huidige operatie direct?
2. verlaagt dit frictie of fouten?
3. maakt dit de basis sterker?
4. verhoogt dit complexiteit te vroeg?

Als 1–3 niet sterk ja zijn:
**niet in NOW.**

---

## Samenvatting

### Founder
bewaakt scope, bewijs en commerciële grens

### Coder
stabiliseert en versimpelt de bestaande control layer

### Operator
test in echt werk

### AI
versnelt en structureert, maar bepaalt de richting niet

### Live proof owner
meet strak en voorkomt bewijsvervuiling

### Commercie
verkoopt alleen de control layer

### Internal route owner
houdt social intake intern nuttig, maar extern buiten de wedge

Dat is de juiste rolverdeling voor deze fase.
