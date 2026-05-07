# Templates v1 — acceptance lock

## Status

Templates v1 is gecontroleerd als kleine operator-hulplaag binnen Mara Ops Workboard.

## Bevestigd

Templates v1 ondersteunt:

- templates tonen in Chats en Feeder
- zoeken op titel
- filteren op type
- filteren op tag
- template openen
- ingevulde template tonen met bestaande context
- templategebruik zichtbaar maken in run log/context

## Niet bedoeld als

Templates v1 is geen:

- templatebeheerplatform
- CMS
- externe integratie
- automation engine
- approval-beslisser
- zelfstandig publicatiepad

## Guardrails

- Geen modelwijzigingen
- Geen migrations
- Geen routingwijzigingen
- Geen settings/env-wijzigingen
- Geen Docker/Compose/VPS/deploy-wijzigingen
- Geen deep integrations
- Geen Buddy-uitbreiding

## Testresultaat

- `python manage.py test core.tests.test_shared_core_v1_views` → groen
- `python manage.py makemigrations --check` → geen wijzigingen
