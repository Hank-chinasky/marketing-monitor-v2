# ROLVERDELING.md

## CreatorWorkboard — Rolverdeling

**Status:** Actief  
**Laatste update:** 2026-03-28

---

## 1. Doel van dit document

Dit document maakt duidelijk:

- welke rollen er zijn
- wat elke rol wel en niet mag
- waar eigenaarschap ligt
- hoe scope, verantwoordelijkheid en handoff logisch verdeeld zijn

Belangrijke regel:
**rolhelderheid verlaagt frictie en fouten.**

---

## 2. Hoofdrollen

De huidige logische rollen zijn:

- Superadmin
- Admin
- Operator

Publieke bezoekers van de root-site zijn geen operationele rol binnen de app.

---

## 3. Superadmin

## Doel
Technische en operationele systeemverantwoordelijke.

## Verantwoordelijk voor
- globale systeeminrichting
- deployment
- stack ownership
- domein/routing-structuur
- kritieke policy-instellingen
- toegangsbeheer op hoog niveau
- beheer van rollen en admins
- herstelacties bij incidenten

## Mag wel
- infrastructuur aanpassen
- stacks beheren
- routing en Traefik beheren
- gevoelige policy velden beheren
- admins aanmaken/verwijderen
- operatorstructuur corrigeren
- globale configuraties aanpassen

## Mag niet
- dagelijkse operatorflow vervangen als normale werkmodus
- productscope oprekken zonder expliciete keuze
- public-site wijzigingen mengen met ops-logica zonder reden

## Belangrijk
Superadmin is systeem-owner, niet standaard dagelijkse operator.

---

## 4. Admin

## Doel
Operationele beheerrol boven operators, binnen de dagelijkse machine.

## Verantwoordelijk voor
- creators beheren
- channels beheren
- operators beheren
- assignments beheren
- controleren van handoff/kwaliteit
- operationele structuur bewaken
- zorgen dat het team binnen duidelijke scope werkt

## Mag wel
- creators aanmaken en wijzigen
- channels aanmaken en wijzigen
- operators beheren
- assignments toewijzen
- operationele status corrigeren
- handoff-kwaliteit bewaken

## Mag niet
- globale infrastructuur wijzigen
- domeinen/routing aanpassen
- publieke stack wijzigen zonder technische verantwoordelijkheid
- systeemarchitectuur veranderen

## Belangrijk
Admin bewaakt de dagelijkse operatie, niet de infrastructuur.

---

## 5. Operator

## Doel
Dagelijkse uitvoerende gebruiker binnen duidelijke operationele scope.

## Verantwoordelijk voor
- werken aan toegewezen creators
- channelcontext volgen
- updates vastleggen
- handoff werkbaar houden
- werken binnen policy en assignment-scope

## Mag wel
- werken binnen toegewezen creator/channel-context
- operationele updates vastleggen
- handoff-notities bijwerken
- workspace-context gebruiken
- uitvoering doen binnen de gegeven scope

## Mag niet
- globale structuur wijzigen
- andere operators beheren
- assignments op hoog niveau aanpassen
- infrastructuur of routing aanpassen
- buiten toegewezen scope werken zonder duidelijke reden

## Belangrijk
Operatorwerk moet snel, simpel en duidelijk blijven.
De rol is uitvoerend, niet systeemsturend.

---

## 6. Publieke site versus interne rollen

De publieke root-site is geen operationele rolomgeving.

Dat betekent:

- bezoekers van `creatorworkboard.com` zitten niet in het interne rollenmodel
- de public site is alleen:
  - uitleg
  - positionering
  - contact
- er is nu geen publiek accountmodel
- er is nu geen customer portal
- er is nu geen self-service gebruikerslaag

---

## 7. Eigenaarschap per laag

## Publieke root-site
**Owner:** technische / product-owner laag  
**Stack:** `creatorworkboard-site`

Gebruik:
- publiek
- uitleg
- contact
- kleine frontdoor

## Interne ops-app
**Owner:** operationele machine  
**Stack:** `creatorworkboard-ops`

Gebruik:
- creators
- channels
- operators
- assignments
- access policy
- handoff

---

## 8. Role boundaries in de praktijk

## Superadmin
Denkt vanuit:
- systeem
- stabiliteit
- scheiding
- herstel
- deployment

## Admin
Denkt vanuit:
- teamflow
- structuur
- kwaliteit
- toewijzing
- dagelijkse operatie

## Operator
Denkt vanuit:
- uitvoering
- actuele context
- volgende stap
- handoff
- werken binnen scope

---

## 9. Wat rolverdeling moet voorkomen

Dit document bestaat vooral om deze fouten te voorkomen:

- operators die buiten scope werken
- admins die infrastructuurprobleem moeten oplossen
- superadmins die dagelijkse operatorflow overnemen
- onduidelijk eigenaarschap per creator of channel
- losse overdracht zonder duidelijke verantwoordelijke

---

## 10. Niet nu

Niet nu toevoegen:
- publieke customer roles
- klantaccounts
- multitenant role modellen
- brede permissiematrices zonder directe noodzaak
- extra rollen die geen directe operationele winst geven

Meer rollen zonder directe noodzaak vergroten alleen complexiteit.

---

## 11. Samenvatting

De kernrolverdeling is simpel:

### Superadmin
Owner van systeem, deployment en kritieke configuratie

### Admin
Owner van dagelijkse operationele structuur

### Operator
Owner van dagelijkse uitvoering binnen toegewezen scope

Dat is voorlopig genoeg.
