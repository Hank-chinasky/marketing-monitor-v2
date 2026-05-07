# Buddy Assist v1 — acceptance lock

## Status

Buddy Assist v1 is gecontroleerd als kleine assistlaag binnen Mara Ops Workboard.

## Bevestigd

Buddy ondersteunt alleen:

- samenvatten
- ontbrekende velden/contextgaten signaleren
- volgende stap voorstellen
- compacte sessiebrief tonen
- laatste handoff condenseren

## Niet toegestaan

Buddy mag niet:

- posten
- chatten
- externe acties uitvoeren
- approvals beslissen
- workflow overnemen
- multi-agent gedrag starten
- routing engine worden

## Audit

Gecontroleerd:

- bestaande Buddy helpers in `core/shared_core_views.py`
- Buddy-slot in Chats
- Buddy-slot in Feeder
- BuddyDraft approve-flow
- regressietests voor shared core, BuddyDraft en conversation thread views

## Testresultaat

- `python manage.py test core.tests.test_shared_core_v1_views` → groen
- `python manage.py test core.tests.test_buddy_draft core.tests.test_buddy_draft_detail_ui core.tests.test_buddy_draft_approve_action` → groen
- `python manage.py test core.tests.test_conversation_thread_views` → groen
- `python manage.py makemigrations --check` → geen wijzigingen

## Guardrails

- Geen modelwijzigingen
- Geen migrations
- Geen routingwijzigingen
- Geen settings/env-wijzigingen
- Geen Docker/Compose/VPS/deploy-wijzigingen
- Geen externe Buddy API geactiveerd
- Geen autonome acties toegevoegd
