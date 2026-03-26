# NOW / LATER / NOT NOW — CREATORWORKBOARD OPS

## Doel
Dit document beschermt de roadmap tegen scope creep.

De regel is simpel:
- wat direct productiviteitswinst geeft = nu
- wat logisch is maar nog niet nodig = later
- wat visionair klinkt maar nu vooral afleidt = niet nu

---

# NOW

## Direct nodig voor interne waarde
- creators volledig via UI beheren
- channels volledig via UI beheren
- operators volledig via UI beheren
- assignments volledig via UI beheren
- duidelijke edit flows
- password reset / operator beheer
- save feedback en nette formulieren
- access policy per channel goed invulbaar maken
- handoff / laatste operator update bruikbaar maken
- content source per creator goed gebruiken
- dashboard bruikbaar houden voor dagelijkse operatie
- echte creators/channels/operators invoeren
- dagelijkse live test uitvoeren
- bugs uit praktijk direct fixen
- secrets en wachtwoorden opschonen
- backup en restore basis regelen
- rollen en scope hard testen
- documentatie voor admin/operator gebruik op orde brengen
- dagelijkse beheerrol overdraagbaar maken aan iemand anders in de organisatie

## Extra NOW-focus: operator workspace
- uniforme channel workspace bouwen
- platformcontext tonen vóór actie
- quick launch naar platform vanuit dashboard
- sessie starten en afsluiten per channel
- handoff verplicht na sessie
- content klaarzetten vóór platformwerk
- captions / instructies / work notes klaar in dashboard
- launch-first flow voor Instagram, TikTok, Reddit en Snapchat
- lichte handmatige engagement ondersteunen binnen policy
- minder wisselen tussen dashboard, notities en platform

## Meetbaar doel
- minder zoeken
- minder fouten
- snellere onboarding
- betere overdracht
- meer output per operatoruur
- snellere start van platformwerk
- minder contextverlies tussen voorbereiding en uitvoering

---


# LATER

# LATER

## Belangrijk, maar pas nadat fase 1 stabiel draait
- Agency model
- AgencyMembership model
- actieve agency-workspace per sessie
- meerdere operators per creator als nette teamstructuur
- lead status / funnelstatus
- source platform model
- destination platform model
- interne thread/commentlaag naast creators of channels
- betere management-KPI’s
- voorbereidende architectuur voor multitenancy
- voorbereidende architectuur voor SaaS
- voorbereidende architectuur voor OnlyFans / Fansly als destination platforms
- eenvoudige planningblokken / shifts
- operator workload zichtbaarheid
- presence / actieve workspace signalering
- basis AI assist voor samenvatten of reply suggesties

## Platformwerk later verfijnen
- ChannelConnection model
- gecentraliseerde capability mapping
- eerste echte connected actie voor één platform
- reconnect UX verbeteren
- eenvoudige connector health checks
- approval flow voor gevoelige channels
- session presence / locking

---

# NOT NOW
# NOT NOW

## Klinkt interessant, maar remt nu de echte voortgang
- volledige SaaS-uitrol
- billing engine
- seat management
- abonnementenlogica
- full multitenancy breed uitrollen
- realtime teamchat
- full paid chat platform
- coins economy
- timed session monetization
- deep OnlyFans integraties
- deep Fansly integraties
- full calendar suite
- creator login-portaal
- complex veldniveau-permissiesysteem
- AI autopilot replies
- automatische AI-beeldgeneratie in operatorflow
- “alles in één” mega-platform bouwen
- mooie maar niet-essentiële dashboards
- features bouwen zonder bewezen praktijkprobleem

## Ook expliciet niet nu
- vier echte social platformintegraties tegelijk
- diepe OAuth/token-architectuur voor alle providers tegelijk
- rich provider adapters voor Instagram, TikTok, Reddit en Snapchat tegelijk
- een social platform-clone binnen CreatorWorkboard
- inbox/comment management als brede laag
- realtime sync/status polling
- fragiele browser- of sessiehacks als kernarchitectuur
- automation-first social product bouwen terwijl operator-workspace nog centraal moet staan

---

# Beslisregel

Bij elke nieuwe feature eerst deze vraag:

**Helpt dit ons binnen 2 weken aantoonbaar productiever te werken in de interne operatie?**

## Als ja
Dan kan het in NOW.

## Als misschien / later nuttig
Dan gaat het in LATER.

## Als het vooral visionair klinkt maar nu niet direct helpt
Dan gaat het in NOT NOW.

---

# Extra regel

We bouwen nu geen droommachine.

We bouwen nu een systeem dat:
- vandaag gebruikt wordt
- deze week tijd bespaart
- deze maand rust geeft
- over 6 maanden pas bewijst wat het commercieel waard is
