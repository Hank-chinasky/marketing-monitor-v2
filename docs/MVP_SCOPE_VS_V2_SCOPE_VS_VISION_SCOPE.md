# MVP SCOPE vs V2 SCOPE vs VISION SCOPE

## Doel
Dit document voorkomt dat het project vervuilt door ideeën die inhoudelijk goed zijn, maar nog niet in de juiste fase thuishoren.

De regel is:

- **MVP Scope** = moet nu of zeer binnenkort, omdat het directe interne productiviteitswinst oplevert
- **V2 Scope** = logisch na interne validatie en stabilisatie
- **Vision Scope** = strategisch waardevol, maar pas later zinvol

---

# 1. MVP SCOPE

## Doel van MVP
Een interne tool die deze week en komende weken echt gebruikt kan worden voor:
- eigen creators
- eigen operators
- eigen social workflows
- handoff
- context
- policy
- dagelijkse operatie

## MVP betekent
Niet:
- mooi
- volledig
- SaaS-ready
- platform-ready

Wel:
- bruikbaar
- stabiel genoeg
- productiviteitsverhogend
- direct inzetbaar

## MVP-kernfunctionaliteit

### Core data
- creators aanmaken
- creators bewerken
- channels aanmaken
- channels bewerken
- operators aanmaken
- operators bewerken
- operators wachtwoord resetten
- assignments aanmaken
- assignments bewerken

### Operations context
- last operator update / handoff
- access policy per channel
- VPN / approved region / IP label / egress IP
- content source per creator
- content ready status
- open issue / work note per channel

### Operator workspace
- uniforme channel workspace per platform
- operator ziet context vóór actie
- platform openen vanuit dashboard
- sessie starten en afsluiten
- handoff verplicht na sessie
- voorbereide content en captions klaar in dashboard
- launch-first flow naar Instagram / TikTok / Reddit / Snapchat
- lichte menselijke engagement-taken kunnen ondersteunen binnen policy
  - bijvoorbeeld liken of kleine handmatige platformacties
- geen diepe platform-clone nodig voor dagelijkse winst

### Toegang en gebruik
- login werkt
- adminflow werkt
- operatorflow werkt
- dashboard werkt
- knoppen en editflows zichtbaar
- save feedback duidelijk
- datumvelden logisch
- operator kan sneller van context naar platformwerk

### Stability / ops
- deployment stabiel
- healthcheck stabiel
- backup basis aanwezig
- secrets opgeschoond
- dagelijkse beheerflow mogelijk zonder shell

## MVP meetlat
MVP is gehaald als:
- het team er dagelijks mee kan werken
- normale invoer niet meer via shell hoeft
- operators minder context verliezen
- admins sneller records kunnen beheren
- de tool direct tijd bespaart
- operator kan vanuit dashboard snel starten op een creator-channel
- content staat klaar vóór publicatie of handmatige actie
- minder wisselen tussen losse notities, telefoon en platform
- platformwerk eindigt met duidelijke handoff
---

# 2. V2 SCOPE

## Doel van V2
De tool gaat van interne cockpit naar een meer volwassen operations platform.

Dit begint pas nadat:
- MVP dagelijks gebruikt wordt
- de echte frictie uit de praktijk boven tafel is
- productiviteitswinst zichtbaar is
- jij niet meer de dagelijkse bottleneck bent

## V2-kern

### Structuurversterking
- Agency model
- AgencyMembership model
- workspace context per sessie
- basis multitenant-denken
- scope op agency + assignment

### Teamstructuur
- meerdere operators per creator
- lead operator / backup operator / teamrollen
- betere toewijzing en zichtbaarheid

### Conversation voorbereiding
- lead status
- source platform
- destination platform
- simpele funnelstatus
- interne thread/commentlaag
- creator- of channelgerichte teamnotities

### Extra operationslaag
- betere KPI-overzichten
- operator workload inzicht
- meer filters en queue-logica
- eerste high-priority workflows

## V2 meetlat
V2 is gehaald als:
- de tool niet meer alleen intern bruikbaar is, maar ook structureel schaalbaar begint te worden
- meerdere teamleden ermee kunnen werken zonder afhankelijk te zijn van mondelinge context
- source/destination denken in het systeem past
- agency-denken technisch voorbereid of deels actief is

### Channel connection voorbereiding
- ChannelConnection model
- nette scheiding tussen channel-context en verbindingsstatus
- capability-mapping centraliseren
- één platform kiezen voor eerste echte connected actie
- reconnect status en foutstatus netter maken
---

# 3. VISION SCOPE

## Doel van Vision Scope
Dit zijn de grote productlagen die commercieel interessant kunnen zijn, maar pas zinvol zijn als MVP en V2 zich in de praktijk bewezen hebben.

## Vision-lagen

### Acquisition machine
- social lead routing
- operators als conversion layer
- source → destination management
- performance per bronkanaal

### Destination / premium layer
- bestaande chat als destination
- OnlyFans als destination
- Fansly als destination
- andere premium omgevingen later

### Backoffice machine
- DM support flows
- standaardvragen afvangen
- low-value filtering
- whale-flagging
- human escalation
- creator ontlasting
- 1-op-1 planning voor high-value klanten

### Monetization engine
- coins
- timed sessions
- bundles
- memberships
- spend tracking
- value per lead
- value per operatoruur

### AI assist layer
- reply suggestions
- tone matching
- context summaries
- whale signalering
- prioritization
- follow-up prompts
- later evt. beeldsuggesties of creatieve support

### SaaS / productization
- agency onboarding
- seat logic
- plan logic
- billing
- feature gating
- supportable multitenancy
- auditability
- customer-facing productlaag

## Vision meetlat
Vision Scope is pas serieus zodra:
- de interne tool bewezen heeft dat hij dagelijks gebruikt wordt
- productiviteitswinst meetbaar is
- operator-output aantoonbaar stijgt
- creators of agencies dit logisch zouden willen afnemen
- de interne organisatie er niet op stukloopt

---

# 4. Concreet overzicht per thema

## Creators / Channels / Operators / Assignments
- MVP: ja
- V2: verfijnen
- Vision: niet kernvernieuwend, maar blijft belangrijk

## Agency model
- MVP: nee
- V2: ja
- Vision: onderdeel van SaaS-fundament

## Meerdere operators per creator
- MVP: nee
- V2: ja
- Vision: ja, als teamstructuurlaag

## Source platform / destination platform
- MVP: nee
- V2: ja, licht
- Vision: ja, zwaar

## OnlyFans / Fansly ondersteuning
- MVP: nee
- V2: alleen conceptueel als destination model
- Vision: ja, als destination/backoffice/connectorlaag

## Realtime chat
- MVP: nee
- V2: nee
- Vision: eventueel, maar pas laat

## Thread/commentlaag
- MVP: nee
- V2: ja
- Vision: basis voor richer team communication

## Whale-detectie
- MVP: nee
- V2: misschien simpele flags later
- Vision: ja

## Kalender / planning
- MVP: nee
- V2: misschien simpele shift blocks
- Vision: ja, indien nodig

## AI assist
- MVP: nee
- V2: heel licht eventueel samenvatten/suggesties
- Vision: ja

## Billing / coins / monetization engine
- MVP: nee
- V2: nee
- Vision: ja

## Full SaaS
- MVP: nee
- V2: technisch voorbereiden
- Vision: ja

## Operator workspace per channel
- MVP: ja
- V2: verfijnen
- Vision: blijft kern van operatoruitvoering

## Launch-first platformflow
- MVP: ja
- V2: ja, met eerste connected acties
- Vision: onderdeel van bredere connectorlaag

## Content prep vóór platformactie
- MVP: ja
- V2: verder structureren
- Vision: koppelbaar aan routing en monetizationlagen

## Handmatige engagement support
- MVP: licht, menselijk en policy-first
- V2: verfijnen
- Vision: alleen als operationeel echt waardevol
---

# 5. Beslisregels

## Feature hoort in MVP als:
- het direct helpt om intern dagelijks te werken
- het deze of volgende week tijd bespaart
- het admins/operators minder frictie geeft
- het direct contextverlies of fouten vermindert

## Feature hoort in V2 als:
- het logisch is na eerste interne validatie
- het schaalbaarheid of teamstructuur verbetert
- het nog niet nodig is om vandaag te kunnen werken
- het voortbouwt op echte praktijkproblemen

## Feature hoort in Vision als:
- het commercieel sterk is
- het product later veel groter kan maken
- het nu nog te zwaar, te vroeg of te speculatief is
- het afhankelijk is van bewezen interne waarde

---

# 6. Harde waarschuwing

## Grootste fout
Een Vision-feature behandelen alsof het MVP is.

Voorbeelden:
- agency multitenancy nu
- full chat nu
- OnlyFans/Fansly integraties nu
- billing nu
- AI-autopilot nu

Dat voelt strategisch, maar breekt de executie.

## Juiste discipline
Eerst:
- werkende kern
- echte praktijk
- meetbare productiviteitswinst

Dan:
- structuur
- routing
- schaal

Pas daarna:
- monetization platform
- AI layer
- SaaS

- vier echte social platformintegraties tegelijk bouwen
- een social platform-clone in dashboard bouwen
- diepe automation bouwen terwijl operator-workspace nog niet bewezen is
---

# 7. Samenvatting in één regel

## MVP
**Operations cockpit met channel workspace die vandaag tijd wint**

## V2
**Ops-platform dat schaal en teamcontext aankan**

## Vision
**Creator revenue operations system met acquisition, backoffice, destination routing en AI assist**
