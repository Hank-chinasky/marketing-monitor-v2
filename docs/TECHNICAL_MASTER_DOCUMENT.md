# CreatorWorkboard — Technical Master Document

## Doel

Dit document beschrijft de huidige technische bouwrichting van CreatorWorkboard.

De prioriteit is op dit moment:

- interne operations cockpit versterken
- de huidige control layer live bewijzen
- de betaalde wedge smal houden
- geen premature verbreding naar suite of SaaS

---

## Technische hoofdrichting

CreatorWorkboard blijft in deze fase:

- een Django monolith
- server-rendered
- simpel in operatie
- bewust beperkt in complexiteit
- gericht op dagelijkse operatorflow
- geschikt voor live validatie in bestaande chatomgevingen

### Niet de focus
- multitenancy
- full SaaS architectuur
- heavy AI
- brede integrations
- realtime suite-gedrag
- inbox replacement
- analyticsplatform

---

## Bouwvolgorde

De vaste volgorde blijft:

1. interne operations cockpit
2. routing / conversation layer
3. backoffice / monetization layer
4. pas daarna SaaS / productisering

De huidige slice zit nog steeds vooral in laag 1, met een klein begin van laag 2.

---

## Huidige technische basis

De volgende fundamenten staan nu:

### Scopebasis
- central assignment scope helpers in `core/services/scope.py`
- creator en channel views gebruiken assignment-scoped querysets
- operations dashboard gebruikt dezelfde access rules
- `primary_operator` is verwijderd uit autorisatiebeslissingen
- admin breadth blijft via `is_staff` / `is_superuser`

### Deploymentbasis
- Docker deployment live op VPS
- Traefik routing werkend
- basic auth werkend
- reverse-proxy loginflow hersteld
- healthcheck stabiel
- Gunicorn startup bevestigd
- migrations en collectstatic bevestigd

### Bestaande ops-slices
- creator materials
- preview-first materials UX
- app-controlled material open/download
- materials scoped zichtbaar voor operators binnen scope

---

## Huidige Route 1 Control Layer

### Status
De eerste versie bestaat al in de app.

### Implementatie-app
`core/`

### Huidige onderdelen
- `ProfileOpportunity`
- `OutcomeEntry`
- server-side scoring service
- opportunity queue
- opportunity detail view
- queue pagination
- tests op scoring, override, visibility, ordering en pagination

### Huidige V1-regel
Opportunity creation blijft buiten app-flow.  
Records worden in V1 via Django admin aangemaakt.

---

## Datamodel

## ProfileOpportunity

### Doel
Eén klein werkobject in de queue.

### Velden
- `assigned_to`
- `intake_name`
- `profile_url`
- `intake_notes`
- `handoff_note`
- `source_quality_score`
- `profile_signal_score`
- `intent_guess_score`
- `target_fit_score`
- `risk_penalty_score`
- `total_score`
- `priority_band`
- `action_bucket`
- `score_reason_short`
- `manual_override`
- `override_priority_band`
- `override_action_bucket`
- `override_reason_short`
- `created_at`
- `updated_at`

### Bewuste grenzen
Niet toevoegen:
- creator FK
- channel FK
- assignment FK
- analytics velden
- statusmachine
- tags
- payoutvelden
- CRM-historie
- recommendation modelvelden als aparte sublaag

---

## OutcomeEntry

### Doel
Kleine uitkomstregel per opportunity.

### Velden
- `opportunity`
- `outcome_type`
- `notes`
- `created_by`
- `created_at`

### outcome_type choices
- `geen_reactie`
- `gesprek_gestart`
- `warm_vervolg`
- `conversion`
- `afgevallen`
- `onduidelijk`

---

## Scoringlogica

### Locatie
`core/services/opportunity_scoring.py`

### Regel
Scoring is altijd server-side.

Niet in:
- templates
- JavaScript
- prompts
- client-side decisioning

### Inputwaarden
- `source_quality_score`: 0 / 1 / 2
- `profile_signal_score`: 0 / 1 / 2
- `intent_guess_score`: 0 / 1 / 2
- `target_fit_score`: 0 / 1 / 2
- `risk_penalty_score`: 0 / -1 / -2

### Harde afvang
Direct `low` + `niet_waard` bij:
- `risk_penalty_score == -2`
- `target_fit_score == 0 and intent_guess_score == 0`

### Totaalscore
```python
total_score = (
    source_quality_score
    + profile_signal_score
    + intent_guess_score
    + target_fit_score
    + risk_penalty_score
)
