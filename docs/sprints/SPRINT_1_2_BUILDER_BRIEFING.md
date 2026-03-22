# Sprint 1–2 Builder Briefing — V2.0 Marketing Monitor

## Doel

We bouwen nu **niet** het hele systeem.

We bouwen alleen de **fundering van V2.0** voor onze interne handmatige creator operations.

Deze fase moet een kleine, stabiele en onderhoudbare basis opleveren waarop later verder gebouwd kan worden.

---

## Nu in scope

Alleen deze onderdelen horen nu bij de bouw:

- auth / login
- users
- operators
- creators
- creator_channels
- operator_assignments
- basis creator detail pagina

---

## Nu expliciet niet in scope

Deze onderdelen horen **niet** bij Sprint 1–2:

- dashboard
- content queue
- publish log
- tracking links
- traffic events
- results
- operator time entries
- access audit
- bonussysteem
- payouts
- backoffice
- klanttoegang
- multi-tenant SaaS
- automation
- scheduler
- DM-tools
- asset library
- AI-features
- LinkedIn/business-use-cases

Niet alvast bouwen.
Niet alvast half voorbereiden met extra modules als dat nu niet nodig is.

---

## Gebruikers

### Admin
Heeft volledige toegang binnen Sprint 1–2 scope.

### Operator
Heeft alleen toegang binnen **actieve, geldige assignments**.

Er zijn geen klantgebruikers.  
Er is geen publieke registratie.

---

## Wat deze fase moet opleveren

Na Sprint 1 en 2 moet het systeem dit kunnen:

- admin kan inloggen
- admin kan operators aanmaken en beheren
- admin kan creators aanmaken en beheren
- admin kan channels koppelen aan creators
- admin kan assignments vastleggen tussen operators en creators
- admin en operator kunnen creator detail bekijken binnen hun toegestane scope
- operator ziet alleen creators, channels en assignments waarvoor een actieve, geldige assignment bestaat

---

## Kernobjecten voor deze fase

Alleen deze objecten moeten nu gebouwd worden:

- `users`
- `operators`
- `creators`
- `creator_channels`
- `operator_assignments`

---

## Schermen voor deze fase

Alleen deze schermen horen nu bij de bouwstart:

1. Login
2. Operators
3. Creators
4. Creator Detail
5. Channels
6. Assignments

Dat is genoeg voor Sprint 1 en 2.

---

## Functionele regels

### Users / auth
- interne login
- alleen actieve users mogen inloggen
- geen publieke registratie
- geen creator- of channel-wachtwoorden opslaan

### Operators
- operators zijn een operationeel domeinobject
- operators moeten expliciet gekoppeld zijn aan een user
- geen impliciete koppeling via e-mail

### Creators
- creator heeft verplichte `status`
- creator heeft verplichte `consent_status`
- een actieve creator zonder `consent_status = active` is niet toegestaan
- creator kan een `primary_operator` hebben

### Creator channels
- elk channel hoort bij exact één creator
- `access_mode` is verplicht
- platformen en statuswaarden volgen de documentatie
- duplicate `(platform, handle)` moet worden voorkomen of netjes afgehandeld

### Operator assignments
- koppelen operator aan creator
- bevatten `scope`, `starts_at`, `ends_at`, `active`
- operator mag alleen werken of kijken binnen actieve, geldige assignments
- dubbele of overlappende actieve assignments moeten expliciet worden gevalideerd als dat functioneel onwenselijk is

---

## Autorisatie

### Admin
- volledige toegang binnen Sprint 1–2 objecten
- volledige CRUD

### Operator
- alleen scoped toegang
- minimaal scoped read
- alleen scoped write als dat expliciet nodig is binnen Sprint 1–2

Belangrijk:

- scope moet worden afgedwongen in de **queryset-/view-laag**
- niet alleen in templates
- niet alleen door links te verbergen

Dus:

- admin ziet alles
- operator ziet alleen creators met actieve, geldige assignment
- dezelfde beperking geldt voor creator detail, channels en assignments

---

## UX-prioriteit

Deze fase is geslaagd als handmatig werk eenvoudiger wordt.

Dus:

- korte formulieren
- minimale verplichte invoer
- logische defaults
- snelle terugvindbaarheid
- zo min mogelijk klikken
- geen dubbel werk

Belangrijke UX-regel:

**de tool moet lichter aanvoelen dan spreadsheetwerk, niet bureaucratischer.**

---

## Technische richting

Gewenste richting:

- één monolithische app
- server-rendered interface
- nette, uitbreidbare structuur
- geen overengineering
- geen losse SPA + API

Voorkeursstack:

- Django

Gebruik framework-standaarden voor:

- auth
- sessions
- CSRF
- forms
- ORM
- admin
- migrations

Niet zelf een mini-framework bouwen.

SQLite voor lokale development is toegestaan.  
De structuur moet later eenvoudig naar PostgreSQL kunnen.

---

## Bouwvolgorde

### Sprint 1
- auth
- users
- operators
- creators

### Sprint 2
- creator_channels
- operator_assignments
- basis creator detail pagina

Niet verder bouwen dan dit.

---

## Acceptatiecriteria

Deze fase is pas klaar als:

- login werkt
- users/auth werkt
- operators en creators beheerd kunnen worden
- channels en assignments logisch gekoppeld zijn
- consent-logica afdwingbaar is
- operator-scope echt werkt
- admin alles ziet
- operator alleen toegewezen records ziet
- creator detail bruikbaar is als basispagina

---

## Beslisregel tijdens de bouw

Bij elke feature geldt:

**Helpt dit direct om Sprint 1 en 2 van de interne operatie stevig neer te zetten?**

- ja → mogelijk in scope
- nee → nu niet bouwen

---

## Documenthiërarchie

Bij tegenstrijdigheden geldt:

- `docs/V2.0_MVP_Startdocument_Marketing_Monitor.md` is leidend voor scope en productgrenzen
- `docs/spec_1_marketing_monitor_for_creator_operations.md` is leidend voor technische specificatie en datamodel
- `docs/V2.0_Datamodel.md` is leidend voor datamodeldetails
- `docs/V2.0_Schermen_En_Flow.md` is leidend voor schermlogica en UX-flow
- `docs/V2.0_Bouwvolgorde_En_Sprints.md` is leidend voor sprintvolgorde

Bij conflict over **scope** wint het Startdocument.  
Bij conflict over **technische modellering** wint SPEC-1.

---

## Harde slotregel

**Bouw nu alleen de fundering. Niet het hele systeem. Een kleine, stabiele basis is waardevoller dan een brede MVP die meteen vervuilt.**
