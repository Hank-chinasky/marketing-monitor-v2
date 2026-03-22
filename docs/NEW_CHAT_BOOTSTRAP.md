# NEW CHAT BOOTSTRAP — MARKETING MONITOR V2

## Project in één zin
We bouwen een interne Django operations cockpit voor creator/channel management, met focus op handmatige operatorflow, access policy, content intake en overzicht.

## Wat er al staat
De lokale app draait al en bevat:
- login/logout
- admin
- operations dashboard als root `/`
- creators list
- creator detail als operator work page
- creator network view
- channels list
- channel detail als channel work page
- assignments list
- scoped operator visibility
- admin-only writes
- VPN/IP access policy per channel
- content intake source fields per creator

## Belangrijkste architectuurregels
- standaard Django `User`
- `Operator.user` met `related_name="operator_profile"`
- scope alleen via `OperatorAssignment`
- `primary_operator` is nooit een permission source
- operator = scoped read
- admin = writes
- dashboard = control layer, geen embedded social login broker
- geen plain text secrets in gewone operationele views

## Huidige domeinrichting
### Creator
Bevat o.a.:
- status
- consent status
- primary operator
- notes
- content source type/url/notes/status

### CreatorChannel
Bevat o.a.:
- platform
- handle
- profile URL
- access metadata
- 2FA
- credential status
- VPN/IP policy
- operator update context

### OperatorAssignment
Enige bron van zichtbaarheid/scope.

## Wat productmatig belangrijk is
De tool is nu:
- intern gericht
- handmatig workflow-ondersteunend
- bedoeld om sneller, veiliger en duidelijker te werken

Niet bedoeld als:
- volledige SaaS
- automation engine
- media DAM
- social login broker

## Huidige prioriteit
Niet breed nieuwe features bouwen.

Wel focus op:
1. handoff / last operator update verbeteren
2. deployment / VPS readiness
3. operationele polish op basis van echte flow

## Strategische richting
Internal tool first.  
Pas later evalueren of productisering zinvol is.

## Gewenste stijl van meedenken
- direct
- scherp
- geen fluff
- prioriteit boven breedte
- eerst echte operationele winst
- future-proof zonder te overbouwen

## Volgende logische stap
Handoff-laag beter maken en daarna de deploy naar VPS strak trekken.
