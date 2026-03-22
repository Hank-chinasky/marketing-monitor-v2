# CHANGELOG

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Runnable Django Sprint 1–2 app in repo root
- Django project package: `marketing_monitor/`
- Core app package: `core/`
- Server-rendered templates in root `templates/`
- Runtime models for:
  - `Operator`
  - `Creator`
  - `CreatorChannel`
  - `OperatorAssignment`
- Canon-aligned auth/scope helpers in `core/authz.py`
- Canon-aligned CBV mixins in `core/mixins.py`
- Canon-aligned validation helpers in `core/validators.py`
- Django admin registration for Sprint 1–2 models
- Login/logout flow using Django auth views
- Migration `core.0001_initial`
- Initial runtime tests for:
  - scope/auth semantics
  - creator consent validation
  - channel uniqueness validation
  - admin-only update protection
  - overlap rule for assignments

### Changed
- Repository evolved from governance/reference-only state to real runtime Django app
- Scope/auth behavior implemented server-side in runtime code
- Navigation cleaned up so operator-facing UI is less misleading
- Logout behavior updated to use POST instead of GET
- Root templates completed so login and core screens render correctly

### Fixed
- Broken remote/local `reference` situation where `reference` briefly existed as file instead of directory
- Missing `registration/login.html` causing `TemplateDoesNotExist`
- Test discovery issue where Django initially found 0 tests
- Logout 405 error caused by GET-based logout link
- Misleading operator navigation to admin-only/operator-only screens
- Git hygiene issues around generated files such as `__pycache__`, `*.pyc`, and `db.sqlite3`

### Notes
- `reference/` remains intact as frozen canon/reference and is not the runtime app
- Sprint 1–2 scope remains intentionally limited
- `primary_operator` remains label/default only and is not used as permission source
- Operator UI remains scoped read-only
- Admin write flows remain allowed


# TODAY PROGRESS REPORT

## Date
2026-03-18

## Summary
Vandaag is de lokale Django Sprint 1–2 app verder uitgebouwd van een basis CRUD/scoped tool naar een bruikbare operationele cockpit voor handmatige creator- en channel-operations.

De nadruk lag op:
- operatorvriendelijke workflow
- access policy per channel
- VPN/IP governance
- visuele netwerkweergave
- operations dashboard
- channel work page
- future-proof content intake op creator-niveau

---

## What was completed today

### 1. Runtime app actief en bruikbaar gemaakt
De lokale Django app draait nu werkend met:
- login/logout
- admin
- creators
- channels
- assignments
- operators
- scoped views op basis van assignment-scope

### 2. Creator detail verbeterd naar operator work page
De creator detailpagina is omgebouwd van simpele datalijst naar operationele werkpagina met:
- summary cards
- badges
- alerts
- duidelijke channel cards
- account access blok
- access policy blok
- snelle links naar platform, netwerk en channel detail

### 3. Network view toegevoegd
Per creator is een netwerkpagina toegevoegd:
- creator centraal
- gekoppelde channels
- primary operator
- assignment-based operators
- visuele kleurcodering voor alerts

Route:
- `/creators/<id>/network/`

### 4. Access policy per channel toegevoegd
Per `CreatorChannel` zijn operationele access policy velden toegevoegd:
- `vpn_required`
- `approved_egress_ip`
- `approved_ip_label`
- `approved_access_region`
- `access_profile_notes`
- `last_ip_check_at`

Doel:
- consistente access-richtlijnen
- minder risico op onveilige of inconsistente logins
- duidelijke operatorinstructie per channel

### 5. Account access metadata uitgebreid
Per `CreatorChannel` is de toegangsinformatie verder bruikbaar gemaakt met:
- `profile_url`
- `login_identifier`
- `credential_status`
- `access_notes`
- `last_access_check_at`
- `two_factor_enabled`

### 6. Channel detail / channel work page toegevoegd
Een aparte channel detailpagina is toegevoegd voor account-level werk.

Doel:
- werken per platform-account
- snelle focus op één channel
- access policy en account access op één pagina

Inhoud:
- alerts
- creator context
- account access
- access policy
- actieve assignments
- snelle links terug naar creator / netwerk / platform

Route:
- `/channels/<id>/`

### 7. Operations Dashboard gebouwd
De root van de applicatie is omgezet naar een operations dashboard.

Dashboard bevat:
- samenvattingskaarten
- aandacht vereist blokken
- quick access
- creators in scope
- badges en kleuraccenten

Belangrijke signalen:
- needs reset
- geen 2FA
- VPN/IP gaps
- consent issues
- creators zonder actieve assignment

Route:
- `/`

### 8. Navigatie en basislayout verbeterd
`base.html` is uitgebreid met:
- dashboard link
- creators/channels/assignments navigatie
- logout knop
- cards / panels / badges styling

### 9. Content Intake future-proof toegevoegd op creator-niveau
Een future-proof content source laag is toegevoegd op `Creator` zodat het systeem nu externe gedeelde mappen kan ondersteunen en later ook interne opslag.

Toegevoegd:
- `content_source_type`
- `content_source_url`
- `content_source_notes`
- `content_ready_status`

Doel:
- creators kunnen materiaal via gedeelde bronmap aanleveren
- operators hebben direct zicht op materiaalbron
- later kan interne storage worden toegevoegd zonder modelbreuk

### 10. Admin/forms aangepast aan nieuwe velden
De relevante forms en admin screens zijn bijgewerkt zodat:
- nieuwe channel access velden invulbaar zijn
- nieuwe creator content intake velden invulbaar zijn
- search/list displays bruikbaar blijven

---

## Key UX improvements
De tool voelt nu minder als een kale admin-uitbreiding en meer als een operationele cockpit.

Belangrijkste UX-winst:
- minder zoeken
- minder klikken
- snellere context per creator en channel
- duidelijke access policy zichtbaar vóór platformactie
- directe open-platform flow
- beter handmatig samenwerken

---

## Architectural direction confirmed
Vandaag is de volgende richting expliciet bevestigd:

### Security / access
- geen plain text wachtwoorden in gewone operationele views
- dashboard toont policy en metadata
- echte credentials blijven buiten de normale applaag

### Platform usage
- geen embedded social login in het dashboard
- wel duidelijke `Open platform` flow
- dashboard is control layer, niet login broker

### Content handling
- voorlopig geen eigen media-hosting als primaire route
- gedeelde externe bronmap is voor nu operationeel slimmer
- wel future-proof gemodelleerd richting interne opslag later

### Workflow philosophy
- handmatige operatorflow blijft centraal
- systeem ondersteunt beslissen, openen, controleren en overdragen
- niet over-automatiseren wat menselijk toezicht nodig heeft

---

## Main files updated today
Waarschijnlijk aangepast of uitgebreid:

- `core/models.py`
- `core/forms.py`
- `core/admin.py`
- `core/views.py`
- `core/urls.py`
- `templates/base.html`
- `templates/dashboard/operations_dashboard.html`
- `templates/creators/creator_detail.html`
- `templates/creators/creator_network.html`
- `templates/channels/channel_list.html`
- `templates/channels/channel_detail.html`

---

## Issues encountered and resolved
### Resolved
- ontbrekende root runtime-app
- ontbrekende templates
- foutieve importregels in `core/urls.py`
- ontbrekende imports in `core/views.py`
- foutieve template block plaatsing
- model/view mismatch bij `vpn_required`
- ontbrekende dashboard-template
- fout door verkeerde mapnaam (`dashboards` vs `dashboard`)
- dubbele/oude devserver-processen

### Lessons confirmed
- eerst model/state rechtzetten, dan views/templates
- altijd checken of templatepad exact overeenkomt
- altijd py_compile/check/runserver gebruiken na view/url wijzigingen
- operatorflow moet leidend zijn, niet alleen datamodel

---

## Current working state
De app ondersteunt nu lokaal:

- login/logout
- dashboard landing page
- scoped creator visibility
- scoped channel visibility
- creator work page
- channel work page
- network view
- content intake bronregistratie
- access policy per channel
- admin-only writes
- operator read-focused workflow

---

## Recommended next step
De meest logische volgende stap is:

### Handoff / last operator update laag afmaken
Zodat operators elkaar beter kunnen overdragen met:
- laatste update
- volgende actie
- context voor volgende operator

Dat levert waarschijnlijk de hoogste operationele winst op voor handmatig teamwork.

---

## Status
Stable local working version.
