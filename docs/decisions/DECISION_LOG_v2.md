# DECISION LOG V2

## 2026-03-18 — Runtime app lives in repo root, reference stays frozen
**Decision**  
De echte runnable Django-app staat in de repo root.  
`reference/` blijft intact als frozen canon/reference en is niet de runtime-app.

**Why**  
Zo blijft er één werkende applicatiebasis voor lokaal draaien en later deployment, terwijl de canon-bestanden apart leesbaar blijven.

**Consequence**  
- Runtime code leeft in root:
  - `manage.py`
  - `marketing_monitor/`
  - `core/`
  - `templates/`
- `reference/` blijft documentatie-/canonlaag

---

## 2026-03-18 — Scope/auth stays assignment-based only
**Decision**  
Scope komt alleen uit actieve geldige `OperatorAssignment` records.

**Why**  
Dit houdt permissies deterministisch en sluit aan op de Sprint 1–2 canon.

**Consequence**  
- `primary_operator` is geen permission source
- operators zien alleen scoped data
- admin houdt write access

---

## 2026-03-18 — Operators are read-focused, admin handles writes
**Decision**  
Operator-UI blijft primair read/scoped. Writes blijven admin-only.

**Why**  
Dit voorkomt verwarring, houdt rechten simpel en blijft binnen Sprint 1–2.

**Consequence**  
- operator krijgt geen operator management-scherm
- admin-only create/update flows blijven actief
- delete blijft via Django admin

---

## 2026-03-18 — Dashboard is a control layer, not a social login broker
**Decision**  
Het dashboard wordt gebruikt als operationele cockpit en policy/control layer, niet als embedded social login omgeving.

**Why**  
Dit verlaagt security debt, houdt verantwoordelijkheden helder en voorkomt dat het platform zelf een riskante login-broker wordt.

**Consequence**  
- wel `Open platform` knoppen
- geen embedded Instagram/TikTok/Telegram login in het dashboard
- geen automatische credential-injectie

---

## 2026-03-18 — No plain text password storage in operational views
**Decision**  
Geen plain text wachtwoorden of vergelijkbare secrets in gewone operationele dashboardvelden.

**Why**  
Dat voorkomt onnodig security-risico en technische schuld in een vroege fase.

**Consequence**  
- dashboard toont access metadata
- echte credentials blijven buiten gewone applaag
- focus ligt op policy, context en workflow

---

## 2026-03-18 — Channel access policy is first-class operational data
**Decision**  
Per `CreatorChannel` wordt access policy expliciet opgeslagen.

**Why**  
Operators moeten vóór handelingen kunnen zien onder welke netwerk- en toegangsregels ze moeten werken.

**Consequence**  
Toegevoegde channelvelden:
- `vpn_required`
- `approved_egress_ip`
- `approved_ip_label`
- `approved_access_region`
- `access_profile_notes`
- `last_ip_check_at`

---

## 2026-03-18 — Channel account access metadata is part of workflow
**Decision**  
Per `CreatorChannel` wordt operationele account access metadata opgeslagen.

**Why**  
Dat maakt handmatig werken sneller en consistenter zonder echte secrets in de app te stoppen.

**Consequence**  
Toegevoegde of bevestigde channelvelden:
- `profile_url`
- `login_identifier`
- `credential_status`
- `access_notes`
- `last_access_check_at`
- `two_factor_enabled`

---

## 2026-03-18 — Creator detail becomes operator work page
**Decision**  
De creator detailpagina is geen kale recordweergave meer maar een operator work page.

**Why**  
Operators hebben behoefte aan directe context, alerts, quick actions en policy-overzicht.

**Consequence**  
Creator detail toont nu:
- summary cards
- alerts
- channel cards
- account access
- access policy
- quick links
- netwerklink

---

## 2026-03-18 — Channel detail becomes account-level work page
**Decision**  
Er is een aparte channel detail/work page per account.

**Why**  
Het echte operationele werk gebeurt per platform-account, niet alleen op creator-niveau.

**Consequence**  
Per channel bestaat nu een pagina met:
- alerts
- creator context
- account access
- access policy
- assignments
- open-platform flow

---

## 2026-03-18 — Add creator network visualization
**Decision**  
Per creator is een interne netwerkkaart toegevoegd.

**Why**  
Dit helpt operators visueel begrijpen hoe creator, channels en operators aan elkaar hangen.

**Consequence**  
Netwerkpagina toont:
- creator node
- channel nodes
- operator nodes
- primary operator relatie
- assignment relaties
- kleurcodering voor alerts

---

## 2026-03-18 — Root landing page is Operations Dashboard
**Decision**  
De root `/` landt op een operations dashboard en niet meer op alleen een creators list.

**Why**  
Het systeem moet sneller laten zien waar aandacht nodig is en waar direct gewerkt kan worden.

**Consequence**  
Dashboard toont:
- samenvattingskaarten
- quick access
- alertblokken
- scoped creators
- operationele badges

---

## 2026-03-18 — Content intake must be future-proof and source-based
**Decision**  
Content-aanlevering wordt gemodelleerd als content source / intake layer op creator-niveau.

**Why**  
Zo kan nu met gedeelde externe mappen gewerkt worden en later eventueel met interne opslag, zonder modelbreuk.

**Consequence**  
Toegevoegde creatorvelden:
- `content_source_type`
- `content_source_url`
- `content_source_notes`
- `content_ready_status`

---

## 2026-03-18 — Prefer external shared source over immediate internal media hosting
**Decision**  
Voor nu is een gedeelde externe bronmap de voorkeursroute boven directe opslag in het eigen platform.

**Why**  
Dat is operationeel lichter, juridisch eenvoudiger te positioneren en sneller inzetbaar.

**Consequence**  
- platform fungeert als cockpit
- materiaalbron wordt gelinkt, niet per se gehost
- later kan `internal_storage` als source type worden toegevoegd/gebruikt

---

## 2026-03-18 — Manual workflow stays central
**Decision**  
De tool ondersteunt handmatige operator-actie in plaats van agressieve automatisering.

**Why**  
De businessflow vraagt menselijk toezicht, toestemming en gecontroleerde uitvoering.

**Consequence**  
Focus blijft op:
- overzicht
- context
- snelle links
- policy
- handoff
- minder klikfrictie

---

## 2026-03-18 — Handoff is a next-priority workflow layer
**Decision**  
Na dashboard, creator work page en channel work page is handoff / laatste update de volgende prioriteit.

**Why**  
Omdat samenwerking tussen operators anders snel context verliest.

**Consequence**  
Volgende beoogde uitbreiding:
- laatste operator update
- handoff notes
- context voor volgende actie

## 2026-03-18 — Content intake is modeled as source-based and future-proof
**Decision**  
Content intake is stored as source metadata on Creator, not as a forced internal media-hosting model.

**Why**  
This keeps the current workflow light and legally/operationally simpler, while allowing later transition to internal storage without breaking the domain model.

**Consequence**  
Creator now stores:
- `content_source_type`
- `content_source_url`
- `content_source_notes`
- `content_ready_status`

# Decision Log — 26 maart 2026

## Beslissing 1 — Creator materials horen in NOW
### Oordeel
Doen.

### Waarom
Operators hebben direct materiaal nodig op creator-niveau om sneller te kunnen werken zonder losse tabs, notities en externe zoekstappen.

### Besluit
Een eerste interne `CreatorMaterial`-laag wordt toegevoegd aan de operations cockpit.

### Scope
Wel:
- creator-gebonden materiaal
- interne upload
- operator-zichtbaarheid binnen scope

Niet:
- creator portal
- externe uploadflows
- integraties
- uitgebreide media library

---

## Beslissing 2 — Creator/channel edit blijft admin-only
### Oordeel
Doen.

### Waarom
Full edit hoort bij structureel beheer.  
Operator-uitvoering en beheer mogen niet door elkaar lopen.

### Besluit
- `creator-update` admin-only
- `channel-update` admin-only

### Gevolg
Operator mag:
- detail bekijken binnen scope

Operator mag niet:
- full creator edit openen
- full channel edit openen

---

## Beslissing 3 — Scope-tests moeten productkeuze volgen
### Oordeel
Doen.

### Waarom
De test-suite bevatte tegenstrijdige verwachtingen over edit-toegang voor operators.

### Besluit
Tests zijn aangepast zodat ze aansluiten op de gekozen productregel:
- detail binnen scope zichtbaar
- edit admin-only

---

## Beslissing 4 — UX-feedback op materials
### Oordeel
Goed idee, juiste fase voor een kleine vervolgslag.

### Besluit
De volgende kleine materials-verbetering wordt:
- thumbnails/previews voor beeldmateriaal
- simpele viewer voor foto/video

### Niet nu
- mappen
- right-click blokkeren
- zwaar mediabeheer
