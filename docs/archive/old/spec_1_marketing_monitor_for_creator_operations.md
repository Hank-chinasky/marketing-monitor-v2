# SPEC-1-Marketing-Monitor-for-Creator-Operations

## Background

## Productregel

**Dit systeem bestaat om managed creator operations veilig, meetbaar en economisch bestuurbaar te maken — niet om social marketing te automatiseren.**

## Scope-regel

**Elke feature die niet direct bijdraagt aan betere controle, betere meting of betere economische besluitvorming hoort niet in MVP.**

Marketing Monitor for Creator Operations is een interne applicatie voor het beheren van echte creators en hun kanalen, het ondersteunen van handmatige content- en publicatieprocessen, en het zichtbaar maken van economische output per creator, kanaal, operator en contentactie.

De aanleiding is operationeel, niet theoretisch:

- creators, kanalen en verantwoordelijkheden zitten vaak verspreid over chats, spreadsheets en losse tools
- handmatige posting gebeurt wel, maar de uitvoeringswaarheid is niet centraal zichtbaar
- economische output is vaak losgekoppeld van creator, kanaal, operator en concrete contentactie
- governance-risico’s zoals consent, access mode en kanaalstatus worden te laat of inconsistent vastgelegd

Deze MVP is daarom geen droomplatform en geen automation suite. Het is een kleine, serieuze en bruikbare interne control- en monitorlaag.

De MVP moet drie dingen goed doen:

1. creators en hun kanalen gestructureerd beheren
2. handmatige content- en publicatieprocessen ondersteunen
3. zichtbaar maken wat economisch werkt en wat niet

Wat het systeem expliciet **niet** is in MVP:

- geen social automation tool
- geen bulkposter
- geen DM-bot
- geen uitgebreide asset library
- geen scheduling engine met API-publicatie
- geen AI-contentgenerator
- geen enterprise rights matrix
- geen CRM
- geen uitgebreide audit suite
- geen health scores
- geen scorecards
- geen SEO-module
- geen customer-facing portal
- geen uitgebreide exports
- geen cluster management
- geen profile graph linking
- geen csv import

## Requirements

### Must have

- Admin/owner kan alle creators, channels, operators, content, publish events, results en dashboards beheren.
- Operator kan uitsluitend records zien en wijzigen waarvoor een actieve toewijzing bestaat.
- Een creator moet een status en consent_status hebben; een actieve creator zonder geldige consent_status is niet toegestaan.
- Een creator moet een primary operator kunnen hebben.
- Een creator kan meerdere channels hebben met platform, status, access_mode, recovery_owner en risk_flag.
- Een operator assignment moet verantwoordelijkheid expliciet vastleggen met scope, geldigheidsperiode en active-state.
- Content items moeten de handmatige werkstroom ondersteunen van draft naar ready/approved naar posted of rejected/removed.
- Approval moet registreerbaar zijn wanneer vereist.
- Publish events moeten vastleggen wat daadwerkelijk live ging, wanneer, via welke methode en door welke operator.
- Tracking links moeten uniek identificeerbare routes bieden per creator/channel/contentcontext.
- Traffic events moeten ruwe meetevents kunnen opslaan, inclusief optionele omzetwaarde.
- Results moeten bestuurlijke samenvattingen per dag/periode bewaren voor dashboards en rapportage.
- Governance-events moeten licht maar bruikbaar worden gelogd in access_audit.
- Pause/revoke-acties moeten direct operationeel effect hebben op zichtbaarheid en bewerkbaarheid.
- Het systeem moet zeven primaire schermen hebben: Dashboard, Creators, Creator Detail, Content Queue, Publish Log, Results, Operator Time Entries.
- Het dashboard moet minimaal revenue, paid_count, joins, clicks, posts, flagged channels en top/worst performers tonen.
- De applicatie mag geen accountwachtwoorden van creators of channels opslaan.
- Het systeem moet interne user-accounts hebben voor login en autorisatie.
- Het systeem moet operatoruren kunnen registreren om revenue per operator hour betrouwbaar te berekenen.

### Should have

- Resultaten moeten herleidbaar zijn naar creator, channel, operator, content item en publish event waar mogelijk.
- KPI’s moeten revenue per creator, revenue per operator, revenue per operator hour, paid per 100 publish events, account survival rate en time-to-publish ondersteunen.
- Segmenten moeten als lichte optionele indeling beschikbaar zijn zonder extra bureaucratische laag.
- De detailpagina van een creator moet overzicht, channels, content queue, publish log, tracking summary en audit tonen.
- Resultschermen moeten afgeleide metrics tonen zoals estimated profit en revenue per click.
- Risk flags moeten zichtbaar filterbaar zijn in beheer- en dashboardoverzichten.

### Could have (opgewaardeerd naar Sprint 6 MVP)

- Minimale webhook-endpoint (één POST-route) voor geautomatiseerde traffic event ingest. Dit is gepromoveerd van 'could have' naar Sprint 6 scope omdat zonder deze route operators clicks handmatig moeten invoeren — precies wat het systeem moet voorkomen.
- Eenvoudige notificaties voor content dat wacht op approval of handmatige posting.
- Basis archivering van offboarded creators en inactive assignments.
- Eenvoudige segmentrapportage op dashboardniveau.

### Won’t have in MVP

- automatische social publishing
- geavanceerde scheduling engine
- DM-automation
- uitgebreide rights matrix
- klantportal
- CRM-functionaliteit
- asset management suite
- AI-contentcreatie
- uitgebreide exportmodule
- SEO- of campaign-planninglaag
- geavanceerde audit- en compliance-suite

## Method

### Architectural stance

De MVP wordt gebouwd als één monolithische server-rendered interne applicatie met PostgreSQL als primaire datastore. Geen losse SPA en geen publieke API-first architectuur in fase 1.

Voorgestelde stack voor MVP:

- Django, Laravel of Rails
- PostgreSQL
- server-rendered HTML interface
- eenvoudige role/scope-based autorisatie op applicatieniveau
- background jobs alleen voor aggregatie en eventverwerking
- optionele object storage voor media_ref verwijzingen, maar geen asset library in scope

### Why this method

Deze methode past bij de productregel:

- lage operationele overhead
- snel implementeerbaar door een klein contractor-team
- sterke standaardadmin- en ORM-capaciteiten
- relationele datamodellering sluit direct aan op creators/channels/content/results
- governance en filtering zijn makkelijker correct af te dwingen in één applicatiegrens

### Core domain model

#### 1. users

Login- en autorisatielaag.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| name | varchar(160) | required |
| email | varchar(255) | unique |
| password_hash | text | required |
| role | enum | admin, operator |
| status | enum | active, inactive |
| last_login_at | timestamptz | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Waarom:

- `users` is de authenticatielaag
- `operators` blijft het operationele domeinobject voor performance, assignments en kostenlogica
- alleen actieve users mogen inloggen
- email moet uniek zijn

#### 2. creators

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| display_name | varchar(160) | required |
| legal_name | varchar(200) | nullable |
| status | enum | active, paused, offboarded |
| consent_status | enum | pending, active, revoked |
| primary_operator_id | fk operators.id | nullable |
| notes | text | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### 3. creator_channels

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| creator_id | fk creators.id | indexed |
| platform | enum | instagram, tiktok, telegram, other |
| handle | varchar(160) | required |
| profile_url | text | nullable |
| status | enum | active, paused, restricted, banned |
| access_mode | enum | creator_only, operator_with_approval, operator_direct, draft_only |
| recovery_owner | enum | creator, agency, shared |
| risk_flag | boolean | default false |
| last_posted_at | timestamptz | nullable |
| last_checked_at | timestamptz | nullable |
| notes | text | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### 4. operators

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| name | varchar(160) | required |
| email | varchar(255) | unique |
| status | enum | active, inactive |
| hourly_cost | numeric(12,2) | nullable |
| notes | text | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### 5. operator_assignments

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| operator_id | fk operators.id | indexed |
| creator_id | fk creators.id | indexed |
| scope | enum | full_management, posting_only, draft_only, analytics_only |
| starts_at | timestamptz | required |
| ends_at | timestamptz | nullable |
| active | boolean | default true |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### 6. content_items

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| creator_id | fk creators.id | indexed |
| channel_id | fk creator_channels.id | indexed |
| title | varchar(200) | required |
| caption | text | nullable |
| media_ref | text | nullable |
| cta_link | text | nullable |
| content_type | enum | post, story, short_video, telegram_message, other |
| status | enum | draft, ready, approved, scheduled_manual, posted, rejected, removed |
| approval_required | boolean | default false |
| approved_by_creator_at | timestamptz | nullable |
| approved_by_operator_id | fk operators.id | nullable |
| planned_publish_at | timestamptz | nullable |
| actual_publish_at | timestamptz | nullable |
| created_by | fk users.id | |
| updated_by | fk users.id | |
| notes | text | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### 7. publish_events

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| content_item_id | fk content_items.id | indexed |
| creator_id | fk creators.id | indexed |
| channel_id | fk creator_channels.id | indexed |
| operator_id | fk operators.id | nullable |
| published_at | timestamptz | required |
| publish_method | enum | creator_posted, operator_posted, assisted_posting |
| post_url | text | nullable |
| tracking_link_id | fk tracking_links.id | nullable |
| notes | text | nullable |
| created_at | timestamptz | |

#### 8. tracking_links

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| creator_id | fk creators.id | indexed |
| channel_id | fk creator_channels.id | nullable |
| content_item_id | fk content_items.id | nullable |
| destination_type | enum | telegram, site, app, whatsapp, other |
| destination_url | text | required |
| short_code | varchar(64) | unique |
| campaign_name | varchar(120) | nullable |
| active | boolean | default true |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### 9. traffic_events

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| tracking_link_id | fk tracking_links.id | indexed |
| event_type | enum | click, landing_view, telegram_join, signup, install, paid |
| event_time | timestamptz | indexed |
| revenue_amount | numeric(12,2) | nullable |
| meta_json | jsonb | nullable |

#### 10. results

Bestuurlijke waarheid / samenvattingslaag voor dashboarding en rapportage.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| result_date | date | indexed |
| creator_id | fk creators.id | indexed |
| channel_id | fk creator_channels.id | nullable |
| content_item_id | fk content_items.id | nullable |
| publish_event_id | fk publish_events.id | nullable |
| operator_id | fk operators.id | nullable |
| clicks | integer | default 0 |
| telegram_joins | integer | default 0 |
| contacts | integer | default 0 |
| leads | integer | default 0 |
| paid_count | integer | default 0 |
| revenue | numeric(12,2) | default 0 |
| cost | numeric(12,2) | default 0 |
| notes | text | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Aanbevolen granulariteit:

- per `result_date`
- per `creator_id`
- optioneel verder uitgesplitst naar `channel_id`, `content_item_id`, `publish_event_id`, `operator_id`

Dus:

- `traffic_events` = ruwe eventlaag
- `results` = geaggregeerde daglaag / bestuurlijke waarheid

#### 11. operator_time_entries

Tijdregistratie per operator. Vastleggen hoeveel tijd een operator heeft besteed aan werk voor een creator of specifiek kanaal, zodat efficiency en economische output per operator meetbaar worden.

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| operator_id | fk operators.id | indexed |
| creator_id | fk creators.id | indexed |
| channel_id | fk creator_channels.id | nullable |
| entry_date | date | indexed |
| minutes_spent | integer | required, > 0 |
| entry_type | enum | content, posting, review, other |
| source | varchar(40) | nullable (manual, derived, imported) |
| notes | text | nullable |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Belangrijke regels:

- elke tijdregistratie hoort bij exact één operator en één creator
- channel_id is optioneel, zodat tijd zowel op creator-niveau als op kanaalniveau vastgelegd kan worden
- minutes_spent moet groter zijn dan 0
- entry_type beschrijft het soort werk en is verplicht
- source is optionele metadata over de herkomst van de registratie

#### 12. segments

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| name | varchar(120) | unique |
| description | text | nullable |
| status | varchar(40) | active, inactive |

Alleen gebruiken als lichte indeling van stijl, doelgroep of angle.

#### 13. access_audit

| Field | Type | Notes |
|---|---|---|
| id | uuid / bigint | PK |
| creator_id | fk creators.id | indexed |
| channel_id | fk creator_channels.id | nullable |
| operator_id | fk operators.id | nullable |
| event_type | enum | assignment_created, assignment_revoked, access_mode_changed, consent_changed, channel_paused, channel_flagged, password_rotation_confirmed, 2fa_changed |
| notes | text | nullable |
| created_at | timestamptz | |

### Relaties

Simpel overzicht:

- één creator heeft meerdere channels
- één creator heeft één primary operator, maar meerdere assignments kunnen actief of historisch bestaan
- één channel heeft meerdere content items
- één content item kan leiden tot één of meerdere publish events
- één publish event gebruikt idealiter één tracking link
- tracking links genereren traffic events
- results vatten economische output samen per creator/kanaal/operator/content
- users loggen in; operators voeren werk uit
- operator_time_entries leveren de minutenbasis voor rendement per operator
- één creator kan meerdere operator_time_entries hebben
- één creator_channel kan meerdere operator_time_entries hebben

### Harde systeemregels en constraints

Deze regels horen expliciet in de MVP:

1. `creators.status = active` vereist `consent_status = active`
2. `content_items.channel_id` moet horen bij dezelfde `creator_id`
3. `content_items.status = posted` vereist minimaal één gekoppeld `publish_event`
4. `tracking_links.short_code` is uniek en niet-herbruikbaar
5. operator mag alleen handelen binnen actieve assignment + scope
6. `pause` of `revoke` heeft direct effect op write-acties en zichtbaarheid waar relevant
7. de app slaat geen creator- of channel-wachtwoorden op
8. `access_mode` is verplicht per channel
9. `publish_events` moeten consistente creator/channel/content-relaties hebben
10. een actieve operator-user moet gekoppeld zijn aan een geldige operator waar relevant

### Autorisatiemodel

#### Admin

- volledige read/write op alle domeinobjecten
- kan pause/revoke uitvoeren
- kan results corrigeren
- kan assignments beheren

#### Operator

- toegang alleen als gekoppeld aan actieve assignment
- scope bepaalt capabilities:
  - `full_management`: alle operationele acties binnen toegewezen creator
  - `posting_only`: publish events, contentstatus naar posted/rejected, tracking links gebruiken
  - `draft_only`: content opstellen en aanpassen, geen publish of governance-acties
  - `analytics_only`: read-only op publish/results/dashboard binnen toewijzing

Autorisatiecontrole bij elke query:

1. is user admin, dan toestaan
2. anders user.operator_id ophalen
3. controleren op actieve assignment voor betreffende creator binnen datumrange
4. scope matchen met gevraagde actie
5. creator/channel-status blokkades toepassen

### Workflow

1. creator aanmaken met consent_status, primary operator en status
2. channels toevoegen met platform, access mode, recovery owner en risk flag
3. operator assignment vastleggen
4. content item aanmaken
5. indien nodig approval registreren
6. operator of creator post handmatig
7. publish event registreren en tracking link koppelen
8. traffic events en/of handmatige result-invoer komen binnen
9. aggregatie werkt results bij
10. dashboard toont wat werkt en wat doodloopt

### Aggregatieregels

`traffic_events` is de ruwe eventlaag.
`results` is de bestuurlijke waarheid.

Aanbevolen aanpak:

- ingest pipeline schrijft alleen naar `traffic_events`
- dagelijkse of on-demand aggregator berekent `results`
- admins kunnen beperkte handmatige correcties op `results` doen
- correcties worden vastgelegd in notes of wijzigingshistorie

Aggregatielogica:

1. groepeer traffic events per `result_date` en `tracking_link_id`
2. resolve tracking link naar creator, channel en content
3. resolve operator via publish_event of fallback naar primary operator
4. tel events per `event_type` op
5. sommeer `revenue_amount` voor paid events
6. combineer optionele handmatige kostenbron
7. schrijf of update één `results` record op de gekozen daggranulariteit

### Schermen

**Overzicht van primaire schermen:**

1. Dashboard
2. Creators
3. Creator Detail
4. Content Queue
5. Publish Log
6. Results
7. Operator Time Entries

#### 1. Dashboard

Doel: managementoverzicht en economische waarheid.

Blokken:

- totale revenue
- paid_count
- telegram_joins
- clicks
- actieve creators
- actieve kanalen
- posts per week
- flagged channels
- top creators
- top operators
- top channels
- top content types
- slechtst presterende creators/channels

KPI’s:

- revenue per creator
- revenue per operator
- revenue per operator hour
- paid per 100 posts of publish events
- revenue per channel
- revenue per publish event

Filters:

- datumrange
- platform
- operator
- creator
- segment
- status

#### 2. Creators

Doel: creators beheren.

Tabelkolommen:

- display_name
- primary_operator
- consent_status
- status
- actieve kanalen
- laatste publicatie
- revenue 30d
- paid_count 30d

Acties:

- creator toevoegen
- bewerken
- pauzeren
- offboarden
- detail openen

#### 3. Creator Detail

Tabs:

- Overview
- Channels
- Content Queue
- Publish Log
- Tracking Summary
- Audit

Overview toont:

- basisinfo
- consent
- operator
- status
- omzet/paid laatste 30 dagen
- actieve routes

Channels toont:

- platform
- handle
- access mode
- risk flag
- last posted
- status

#### 4. Content Queue

Doel: dagelijkse contentoperatie.

Tabelkolommen:

- creator
- channel
- title
- content_type
- status
- approval_required
- planned_publish_at
- created_by
- updated_at

Acties:

- content toevoegen
- status wijzigen
- goedkeuring registreren
- markeren als posted / rejected / removed

#### 5. Publish Log

Doel: chronologisch zien wat live ging.

Tabelkolommen:

- published_at
- creator
- channel
- operator
- publish_method
- content_item
- tracking_link
- post_url
- first result summary

Acties:

- publish event toevoegen
- notitie toevoegen
- link openen

#### 6.5 Operator Time Entries

Doel: lichte tijdregistratie zodat `revenue per operator hour` berekend kan worden.

Tabelkolommen:

- operator
- creator
- channel (optioneel)
- entry_date
- minutes_spent
- entry_type
- notes

Acties:

- tijd registreren
- bestaande registratie bewerken
- filteren op operator, datum, creator, entry_type

Ook beschikbaar als tab in Creator Detail (Tab 7 — Time Entries).

UX-regel: een operator moet tijd in minder dan 15 seconden kunnen registreren. Niet voor micromanagement, maar voor efficiency meten en revenue per operator hour kunnen berekenen.

#### 7. Results

Doel: economische output en vergelijkbaarheid.

Tabelkolommen:

- date
- creator
- channel
- operator
- clicks
- telegram_joins
- contacts
- leads
- paid_count
- revenue
- cost
- estimated profit

Extra afgeleide metrics:

- revenue per click
- revenue per join
- revenue per creator
- revenue per operator
- revenue per operator hour
- paid per 100 posts of publish events

### KPI-definities

- `estimated_profit = revenue - cost`
- `revenue per operator hour = sum(revenue) / (sum(minutes_spent) / 60)` binnen dezelfde filterperiode
- `paid per 100 publish events = 100 * paid_count / aantal publish events`
- `account survival rate = bruikbaar gebleven channels / channels actief aan begin van periode`
- `time-to-publish = published_at - content_items.created_at`

### Securityregels vanaf dag 1

Verplicht:

- geen wachtwoorden opslaan in de app
- consent_status verplicht voor actieve creator
- access_mode verplicht per channel
- operator ziet alleen toegewezen creators/channels
- pause/revoke moet direct operationeel effect hebben
- unieke trackinglinks gebruiken voor analyse
- governance-events loggen
- risk_flag handmatig kunnen zetten per channel

## Implementation

### Bouwvolgorde in 8 stappen

1. users + auth + operators
2. creators + creator detail
3. channels + access mode + consent state
4. operator assignments
5. content queue
6. publish log + tracking links
7. traffic events + minimale ingest-endpoint + results + aggregatielogica + dashboard + operator_time_entries
8. access audit + pause/revoke flows

### Aanbevolen technische invulling

- monolithische app
- server-rendered interface
- PostgreSQL
- simpele auth
- interne adminachtige UI
- geen SPA + losse API als start

### v0.1 absolute minimum

Als nog kleiner gestart moet worden, bevat v0.1 alleen:

- login
- creators aanmaken
- channels koppelen
- operator assignments
- content item registreren
- publish event registreren
- tracking link koppelen
- results tonen in dashboard

## Milestones

### Milestone 1 — Foundation

- users, auth en operatorrollen werken
- basisnavigatie staat
- operators zien alleen toegewezen records

### Milestone 2 — Operations backbone

- creators, channels en assignments live
- consent- en channelstatus afdwingbaar
- creator detail bruikbaar

### Milestone 3 — Content and publishing

- content queue live
- publish log live
- tracking links bruikbaar

### Milestone 4 — Economic visibility

- traffic ingest live
- results aggregatie live
- dashboard KPI’s bruikbaar
- operatoruren invoerbaar

### Milestone 5 — Governance hardening

- access audit live
- pause/revoke flow werkt direct
- risk flags en survival metrics beschikbaar

## Gathering Results

De MVP is geslaagd wanneer de volgende vragen dagelijks beantwoord kunnen worden zonder spreadsheets of chatreconstructie:

- welke creator is actief?
- op welke kanalen?
- wie is verantwoordelijk?
- wat is geplaatst?
- via welke route?
- wat heeft het opgeleverd?

### KPI’s die bepalen of het model werkt

1. Revenue per creator  
   Brengt een creator echt geld binnen?

2. Revenue per operator  
   Is het als managed operatie schaalbaar?

3. Revenue per operator hour  
   Dit is de hardste waarheid.

4. Paid conversions per 100 publish events  
   Is output commercieel zinvol?

5. Account survival rate  
   Hoeveel kanalen blijven bruikbaar zonder restrictie of bans?

6. Time-to-publish  
   Hoe snel gaat draft → approval → live?

### Scope-bewaking na livegang

Nieuwe featureverzoeken worden alleen geaccepteerd als ze direct bijdragen aan:

- betere controle
- betere meting
- betere economische besluitvorming

Alles daarbuiten schuift naar post-MVP.

## Documenthiërarchie

Voor V2.0 gelden de volgende regels:

- Het **Startdocument** (`V2.0_MVP_Startdocument_Marketing_Monitor.md`) is leidend voor:
  - productdoel
  - scope
  - out-of-scope
  - gebruikers
  - succesdefinitie
  - productregels

- **SPEC-1** (dit document) is leidend voor:
  - technische specificatie
  - datamodel
  - constraints
  - autorisatie
  - implementatiedetails

### Conflictenregel
- Bij conflict over **scope of productgrenzen** wint het Startdocument.
- Bij conflict over **technische modellering of implementatie** wint SPEC-1.

