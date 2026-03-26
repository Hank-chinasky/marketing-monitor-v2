# ROADMAP 6 MAANDEN — CREATORWORKBOARD OPS
## Periode
23 maart 2026 t/m 30 september 2026  
Beslismoment SaaS: oktober 2026

---

# 1. Doel van deze roadmap

De komende 6 maanden gebruiken we CreatorWorkboard eerst als **interne operations tool**.

De volgorde is bewust:

1. intern productief worden
2. praktijkbugs eruit halen
3. workflows verbeteren op basis van echte operators en echte creators
4. pas daarna beslissen of het product SaaS-waardig is

Dit betekent:
- **geen premature SaaS-bouw**
- **geen grote scope-explosie**
- **eerst cashflow en productiviteitswinst**
- **later pas platformisering**

---

# 2. Strategische uitgangspunten

## Wat nu het doel is
De tool moet eerst:
- tijd besparen
- contextverlies verminderen
- operators sneller laten werken
- onboarding makkelijker maken
- overdracht verbeteren
- fouten rond access/policy/login verminderen
- operators sneller laten starten op social platforms
- content en instructie klaarzetten vóór platformwerk
- menselijke plaatsing en lichte engagement in één workflow ondersteunen

## Wat nu nadrukkelijk niet het doel is
Nog niet bouwen als primaire focus:
- SaaS billing
- multitenancy breed uitrollen
- calendar/planning suite
- realtime teamchat
- eigen paid chat engine
- AI-autopilot
- diepe OnlyFans/Fansly integraties

## Hoofdvraag voor elke feature
**Levert dit in de komende 2 weken direct productiviteitswinst op voor het team?**

Als het antwoord nee is:
- op backlog
- niet nu

---

# 3. Succesdefinitie na 6 maanden

Na 6 maanden moet duidelijk zijn:

## Productmatig
- werkt het team hier dagelijks mee
- wil niemand meer terug naar losse notities/chaos
- zijn de kernworkflows stabiel
- is duidelijk welke features echt waardevol zijn

## Operationeel
- kan een andere persoon binnen de organisatie dagelijks beheer doen
- ben jij niet meer de bottleneck
- zijn operators sneller inzetbaar
- is overdracht merkbaar beter

## Zakelijk
- is productiviteitswinst zichtbaar
- kun je meer creators per operator aan
- is duidelijk of dit richting SaaS kansrijk is
- weet je waar de echte commerciële hefboom zit

---

# 4. Fase-overzicht

## Fase A — MVP live in praktijk
Periode: 23 maart t/m 3 april 2026

Doel:
- interne MVP echt gebruiken
- blockers direct fixen
- eerste echte records draaien

## Fase B — Stabilisatie en beheersbaarheid
Periode: april 2026

Doel:
- admin- en operatorflows afmaken
- bugs en UX-frictie eruit
- dagelijkse inzet betrouwbaar maken

## Fase C — Productiviteitsfase
Periode: mei 2026

Doel:
- bewijzen dat de tool echt tijd wint
- operator-output verhogen
- onboarding simpeler maken

## Fase D — Structuurversterking
Periode: juni 2026

Doel:
- systemen klaarzetten voor teamgroei
- eerste fundamenten voor agency/membership denken
- maar nog zonder brede SaaS-explosie

## Fase E — Conversation model voorbereiding
Periode: juli 2026

Doel:
- lead / source / destination denken voorbereiden
- niet full chat bouwen, wel slim modelleren

## Fase F — Evaluatie en SaaS-besluitvoorbereiding
Periode: augustus–september 2026

Doel:
- praktijkdata verzamelen
- bepalen of product richting SaaS moet
- roadmap voor fase 2/3 klaarzetten

---

# 5. Detailplanning per periode

---

## april 2026 — 23 maart t/m 27 maart 2026
## Intensieve MVP-week
Beschikbaarheid: 10 uur per dag

### Doel
Deze week moet de tool intern bruikbaar worden als MVP.

### Must-have output
- creators, channels, operators en assignments volledig via UI
- edit flows zichtbaar en bruikbaar
- save-feedback en formulieren logisch
- live deployment stabiel
- login, CSRF, healthcheck en routing betrouwbaar
- eerste echte records in productie
- eerste operatorflow volledig doorlopen
- eerste channel workspace bruikbaar
- operator kan sessie starten vanuit dashboard
- operator ziet policy, content en laatste update vóór platformactie
- launch-first flow voor minimaal Instagram en TikTok conceptueel goed neergezet

### Taken
- operator beheren verbeteren
- creator bewerken vanaf logische plekken
- wachtwoord reset-flow toevoegen of voorbereiden
- channel/edit UX gladstrijken
- assignments flow goed laten landen
- eerste echte creators/channels/operators invoeren
- live bugs meteen oplossen
- secrets en wachtwoorden opschonen
- backup-procedure vastleggen
- channel workspace eerste versie bouwen
- sessie start/stop flow bouwen
- handoff na sessie afdwingen
- content-ready en work notes zichtbaar maken in channelflow
- launch-buttons en platform quick actions toevoegen

### Definition of Done
- het team kan er deze week echt in werken
- shell is niet meer nodig voor normaal beheer
- grootste irritaties zijn bekend en deels opgelost

---

## PERIODE 2 — 30 maart t/m 10 april 2026
## Stabilisatie + echte testweken
Beschikbaarheid: 8 uur per dag in week 2, daarna teruglopend

### Doel
Van werkende MVP naar dagelijks bruikbare interne tool.

### Focus
- elke dag echt gebruiken
- bugs noteren
- direct fixen wat het werk blokkeert
- beheer deels overdraagbaar maken

### Must-have output
- operator-edit en password-reset in de app
- duidelijke admin-beheerlaag
- consistente knoppen, save states, terugflows
- echte creators/channels/assignments volledig gevuld
- handoff/update consequent gebruikt

### Taken
- operatorbeheer afmaken
- creatorbeheer netter maken
- operatorlijst, creatorlijst en channellijst verbeteren
- rol- en scopetests uitvoeren
- documentatie voor dagelijks gebruik afmaken
- iemand intern laten meelopen met beheer

### KPI’s
- tijd om nieuwe creator in te richten
- aantal handmatige workarounds buiten app
- aantal bugs per dag
- aantal keren dat iemand iets “niet kan vinden”

### Definition of Done
- tool is intern dagelijks inzetbaar
- beheerstromen zijn duidelijk
- een tweede persoon kan mee beheren

---

## APRIL 2026
## Stabilisatie en basisdiscipline

### Doel
April is de maand waarin de tool van “werkt” naar “betrouwbaar genoeg” moet gaan.

### Prioriteiten
1. dagelijkse frictie verwijderen
2. data kwaliteit omhoog
3. teamgedrag in de tool krijgen
4. afhankelijkheid van jou verlagen
5. operator workspace stabiel krijgen
### Features
- edit/reset/adminflows volledig bruikbaar
- betere lijstpagina’s
- filters en zoekverbeteringen waar nodig
- duidelijke statusvelden
- handoff/UI polish
- backuplogica en beheerafspraken
- rolhandleidingen en interne werkinstructies
- channel workspace polish
- sessielogica per channel
- launch-first workflows per platform
- content prep beter zichtbaar maken
- handoff direct na platformwerk afdwingen

### Processen
- operators moeten alles in de tool registreren wat operationeel van waarde is
- admins moeten creators/channels/assignments netjes inrichten
- dagelijkse feedback moet in backlog landen

### KPI’s
- aantal actieve creators in tool
- aantal actieve channels in tool
- aantal policy-gaps
- aantal creators zonder assignment
- gemiddelde tijd om iemand in te werken

### Definition of Done eind april
- tool is geen experiment meer
- tool levert merkbaar minder chaos op
- dagelijks beheer kan door iemand anders gedaan worden
- jij zit meer op keuzes dan op brandjes blussen

---

## MEI 2026
## Productiviteitsmaand

### Doel
Mei moet aantonen dat de tool **echt productieverhoging** oplevert.

### Kernvraag
Kunnen operators met deze tool:
- sneller werken
- meer creators aan
- betere overdracht doen
- minder fouten maken

### Prioriteiten
- workflows meten
- frictie systematisch reduceren
- operator-output begrijpen
- managementinformatie simpeler zichtbaar maken
- operator-starttijd op platformwerk verkorten
- throughput per operator verhogen via betere workspace
- minder wissels tussen losse tools en notities

### Features
- kleine analytics / samenvattende KPI’s
- statusoverzichten
- verbeterde alerts
- snellere creator/channel overgangen
- operationele notities slimmer inzetten

### Operationeel
- nieuwe operator via de tool inwerken
- vergelijking maken tussen werken met en zonder tool
- productiviteitswinst in uren of fouten gaan schatten

### KPI’s
- creators per operator
- tijd per creator per dag/week
- aantal overdrachtsfouten
- aantal contextvragen (“waar staat dit?”)
- aantal incomplete channel records
- tijd van workspace openen tot platformactie
- aantal platformwerksessies met volledige handoff
- aantal keren dat content vooraf klaarstaat

### Definition of Done eind mei
- productiviteitswinst is niet meer gevoelsmatig maar zichtbaar
- team wil er actief mee blijven werken
- duidelijk is welke ontbrekende functies echt waarde hebben

---

## JUNI 2026
## Structuurversterking

### Doel
De tool klaarzetten voor serieuzere organisatiegroei zonder nu al SaaS te bouwen.

### Prioriteiten
- technische schuld beperken
- modellen netter maken
- uitbreidrichting bepalen
- voorbereiden op agency/membership denken

### Mogelijke bouwblokken
Let op: alleen starten als fase 1 intern echt stabiel is.

- Agency model verkennen
- membership-architectuur uitwerken
- scope-laag herzien
- voorbereidende migratiekeuzes ontwerpen
- geen volledige agency-uitrol als dat live gebruik remt
- ChannelConnection model verkennen
- capability mapping centraliseren
- bepalen welk platform als eerste echte connected actie krijgt
- geen brede integratielaag bouwen als workspace nog niet bewezen is

### Waarom deze maand belangrijk is
Zonder deze stap wordt latere uitbreiding richting:
- meerdere agencies
- meerdere operators per creator
- teamstructuren
een rommeltje.

### Definition of Done eind juni
- duidelijk technisch plan voor agency/membership
- geen grote datastructuur-paniek meer later
- huidige tool blijft stabiel tijdens voorbereiding

---

## JULI 2026
## Conversation layer voorbereiding

### Doel
Nog geen complete chat bouwen, maar wel de eerste slimme conversatielaag voorbereiden.

### Wat dit betekent
Niet meteen realtime chat.

Wel nadenken over:
- lead status
- source platform
- destination platform
- interne thread/commentlaag
- handoff op gespreksniveau

### Strategische lijn
De tool moet voorbereid worden op:

**source → team context → destination**

waarbij source bijvoorbeeld is:
- TikTok
- Instagram

en destination later kan zijn:
- eigen paid chat
- OnlyFans
- Fansly

### Features
Alleen als intern gebruik daar klaar voor is:
- lead/funnel statusmodel
- eenvoudige thread/commentlaag
- bron- en bestemmingsveld op relevant niveau
- interne notities per creator/channel/thread

### Definition of Done eind juli
- eerste conversation model staat conceptueel of licht technisch klaar
- geen scope-implosie
- basis blijft overeind

---

## AUGUSTUS 2026
## Praktijkvalidatie en commerciële lens

### Doel
Niet meer alleen kijken naar “kan het”, maar:
- maakt het geld vrij
- maakt het team schaalbaarder
- wordt de waarde duidelijk

### Focus
- waar zit de meeste outputwinst
- wat gebruiken operators echt
- welke velden zijn bullshit
- welke schermen zijn cruciaal
- waar ontstaat omzetimpact

### Zakelijke vragen
- hoeveel creators kan 1 operator aan met de tool
- wat scheelt het in onboardingtijd
- wat scheelt het in miscommunicatie
- wat zou een agency hiervoor logisch vinden om te betalen
- welke functies zijn premium en welke niet

### Definition of Done eind augustus
- duidelijke lijst met bewezen waarde
- duidelijke lijst met onzin/overbodige features
- eerste commerciële hypotheses scherper

---

## SEPTEMBER 2026
## Besluitvoorbereiding richting SaaS

### Doel
Niet meteen SaaS bouwen, maar beslissen of het zinnig is.

### Wat je in september moet weten
- werkt de tool intern echt stabiel
- is er aantoonbare productiviteitswinst
- zijn operators afhankelijk geworden van de tool
- is agency/membership architectuur logisch genoeg
- welke roadmap heeft commercieel potentieel
- waar hoort OnlyFans/Fansly in de architectuur

### Belangrijke productkeuze
Als jullie doorgaan richting SaaS, moet het product worden gepositioneerd als:

**creator conversation operations system**

Niet alleen:
- dashboard
- niet alleen chat
- niet alleen CRM

Maar:
- operations
- context
- lead routing
- destination management
- later monetization
- later AI assist

### Definition of Done eind september
- Go / No-Go richting SaaS
- duidelijke fase-2 roadmap
- heldere technische fundamentkeuzes
- jij werkt niet meer dagelijks als beheerder

---

# 6. Prioriteitenmatrix

## Altijd prioriteit
- alles wat dagelijkse productiviteit verhoogt
- alles wat contextverlies verlaagt
- alles wat beheer overdraagbaar maakt
- alles wat operators sneller inzetbaar maakt
- alles wat operator-starttijd op platformwerk verlaagt
- alles wat content en context vóór actie beter klaarzet

## Middelmatige prioriteit
- nette polish
- rapportages
- extra filters
- prettige dashboarddetails

## Lage prioriteit tot nader order
- deep AI
- realtime chat
- calendar
- SaaS billing
- hard multitenancy
- OnlyFans/Fansly integraties op uitvoerend niveau
- brede social connectorlaag
- diepe platformintegraties op meerdere netwerken tegelijk
- social platform cloning
---

# 7. OnlyFans / Fansly positie in deze roadmap

## Nu
Nog niet diep integreren.

## In de roadmap
Ze horen later thuis als:
- **destination platforms**
- later mogelijk als **connector platforms**
- nog later als **monetization data sources**

## Strategische regel
Nooit de hele kern bouwen rond één specifiek extern platform.

Beter:
- generiek source/destination model
- platform adapters later
- eerst interne waarde, dan connectorwaarde
  Dezelfde regel geldt voor social platforms:
- eerst uniforme operator workspace
- daarna pas selectieve connectorwaarde
- nooit de hele kern bouwen rond één provider of één diepe integratie
---

# 8. KPI’s die vanaf nu wekelijks gevolgd moeten worden

## Operatie
- aantal actieve creators
- aantal actieve channels
- aantal actieve operators
- aantal assignments
- aantal policy-gaps
- aantal creators zonder assignment

## Productiviteit
- tijd om nieuwe creator volledig in te richten
- tijd om nieuwe operator bruikbaar te maken
- aantal contextvragen / zoekmomenten
- aantal overdrachtsproblemen
- aantal buiten-tool workarounds

## Zakelijk
- creators per operator
- geschatte tijdswinst per operator
- fouten of vertragingen door ontbrekende context
- momenten waarop tool direct werk versnelt

---

# 9. Capaciteitsmodel

## Week 1
10 uur per dag  
Focus: forceren naar bruikbare MVP

## Week 2
8 uur per dag  
Focus: stabiliseren en productiviteitsfrictie verwijderen

## Daarna
4 uur per dag  
Focus:
- roadmap
- review
- keuzes
- bugs prioriteren
- niet meer dagelijks beheer

## Interne overdracht
Zo snel mogelijk iemand binnen de organisatie laten overnemen voor:
- dagelijks beheer
- invoer
- testen
- terugkoppeling
- eerste support

---

# 10. Go / No-Go criteria richting oktober 2026

## GO richting SaaS-verkenning als:
- interne tool dagelijks gebruikt wordt
- productiviteitswinst duidelijk is
- beheeroverdracht gelukt is
- operatoroutput aantoonbaar beter is
- roadmap voor agency/membership logisch is
- er echte vraag of commerciële tractie zichtbaar is

## NO-GO richting SaaS als:
- jij nog steeds alles zelf moet doen
- team de tool half gebruikt
- context niet betrouwbaar is
- productiviteitswinst niet zichtbaar is
- scope nog te rommelig is
- het product nog vooral “interne chaos op een scherm” is

---

# 11. Eindoordeel

De komende 6 maanden zijn geen sprint naar SaaS.

Ze zijn een gecontroleerde route naar:
- interne dominantie
- echte productiviteitswinst
- minder afhankelijkheid van jou
- scherp zicht op wat later commercieel echt waarde heeft

## Kort samengevat
- maart/april: MVP + stabilisatie
- mei: productiviteit bewijzen
- juni: structuur versterken
- juli: conversation layer voorbereiden
- augustus: praktijk en waarde valideren
- september: SaaS-besluit voorbereiden
- oktober: beslissen
