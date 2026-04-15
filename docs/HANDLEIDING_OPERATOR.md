# Handleiding Operator — Mara Ops Workboard v1

## Doel
Mara Ops Workboard helpt je sneller en rustiger werken in twee plekken:
- Chats Workspace
- Feeder Workspace

De tool is nu geen groot platform. Het doel is:
- minder contextverlies
- snellere start van werk
- duidelijkere handoff
- minder fouten
- beter zien wat nu aandacht nodig heeft

## Waar kijk je altijd eerst
Voor je iets doet, scan je altijd in deze volgorde:
1. **Mag ik hier werken?**
2. **Policy vóór actie**
3. **Context**
4. **Completeness alerts**
5. **Laatste handoff / run log**

Als basiscontext ontbreekt, werk je niet blind door.

## Chats Workspace
In Chats zie je:
- threadselectie
- policy en guardrails
- account/context
- actieve thread
- handoff-afsluiting
- volgende stap
- approvals
- buddy draft / run log / issues

Gebruik Chats om:
- een thread te beoordelen
- context te lezen
- een sessie af te sluiten
- een volgende stap vast te leggen
- te zien of goedkeuring nodig is

## Feeder Workspace
In Feeder zie je:
- creatorselectie
- wat live moet
- wat aandacht nodig heeft
- doorzet naar Chats
- ritme / opvolging
- approvals
- run log / signalen / quick actions

Gebruik Feeder om:
- te bepalen wat live aandacht nodig heeft
- opvolging te bewaken
- te zien wat door moet naar Chats
- creator-level approvals te beheren in context

## Approvals v1
Approvals v1 is klein en praktisch. Je gebruikt het om te zien of iets direct door mag of eerst goedgekeurd moet worden.

### Types
- **Content approval**
- **Action approval**
- **Access exception**

### Statussen
- **Not required** = geen approval nodig
- **Pending** = wacht op beoordeling
- **Approved** = mag door
- **Rejected** = niet doorzetten in huidige vorm
- **Expired** = verlopen, niet meer geldig

### Wat jij als operator doet
1. Kijk of er een approval op de thread of creator staat.
2. Zie je **Pending**, werk dan niet door alsof alles al akkoord is.
3. Zie je **Approved**, ga verder binnen de bestaande context en guardrails.
4. Zie je **Rejected**, stop en pas de actie of inhoud aan.
5. Maak een approval aan als extra bevestiging nodig is.

### Waar approvals zichtbaar zijn
- **Chats**: thread-level approvals in de rechterkolom
- **Feeder**: creator-level approvals in de rechterkolom

### Acties
Je kunt in de workspaces:
- een approval aanmaken
- een pending approval goedkeuren
- een pending approval afwijzen

Alleen approvals binnen jouw scope zijn zichtbaar en wijzigbaar.

## Run log
In de run log zie je compacte gebeurtenissen zoals:
- Approval aangemaakt
- Approval goedgekeurd
- Approval afgewezen
- Template geopend / gebruikt
- Laatste handoff / laatste update

Gebruik dit voor snelle overdracht en teruglezen.

## Werkregel
De belangrijkste regel blijft:
- **Werk alleen door als context, policy en scope duidelijk genoeg zijn.**
- Als een approval of completeness alert twijfel oproept, escaleer eerst.
