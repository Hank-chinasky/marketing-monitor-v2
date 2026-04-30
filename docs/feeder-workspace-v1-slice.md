# Feeder Workspace v1 — slice

## Baseline

Branch: `feat/feeder-workspace-v1-slice`

Startpunt: actuele `main` na Feeder middle pane fix.

Deze slice is alleen bedoeld om de Feeder Workspace v1-scope vast te leggen voordat er nieuwe code wordt gemaakt.

## Doel

Een kleine, scanbare Feeder Workspace v1-slice voorbereiden binnen Mara Ops Workboard.

De feeder moet operators sneller laten zien:

- wat nu aandacht nodig heeft
- welke content/context erbij hoort
- wat de volgende operatoractie is
- welke overdracht naar Chats nodig is

## Wat heeft nu aandacht nodig?

De Feeder Workspace moet duidelijk maken welke creator/contentregel prioriteit heeft, zonder dat de operator door losse context hoeft te zoeken.

## Welke content/context hoort erbij?

Per feeder-item moet de operator snel kunnen zien:

- creator/context
- relevante status
- open issue of aandachtspunt
- beschikbare content/context
- laatst bekende overdracht of run-log-signaal

## Volgende operatoractie

De workspace moet per geselecteerd feeder-item duidelijk maken wat de operator nu moet doen.

Voorbeelden:

- controleren
- voorbereiden
- doorzetten naar chats
- markeren als aandachtspunt
- afsluiten met handoff

## Handoff naar Chats

Als feeder-context relevant is voor Chats, moet de overdracht kort en scanbaar zijn.

De feeder mag geen nieuwe chatlaag worden.

## 3-pane semantiek

De bestaande 3-pane shell blijft leidend.

Links:

- policy
- context
- alerts
- scope
- access/risk
- completeness

Midden:

- feeder-werkvlak
- wat nu aandacht nodig heeft
- content/context focus
- volgende operatoractie

Rechts:

- handoff
- run log
- quick actions
- issues
- buddy-slot

Alleen het middenpaneel mag inhoudelijk verschillen van Chats.

## Wel in scope

- Feeder view-context
- Feeder template-scanbaarheid
- Feeder tests
- behoud van bestaande 3-pane semantiek
- duidelijke handoff richting Chats
- geen extra workflowlaag

## Niet nu

- models
- migrations
- routing/url
- settings/env
- VPS/deploy
- approvals action logic
- buddy-uitbreiding
- conversation layer
- routing engine
- SaaS/productisering
- creator-markt
- deep integrations
- AI-autopilot
- nieuwe chatclient
- embedded live chatfundament

## Technische grens

Deze slice mag later alleen code raken als dat vooraf apart is gereviewd.

Toegestane code-oppervlakken voor een latere code-slice:

- Feeder view-context
- Feeder template-scanbaarheid
- Feeder tests

Niet toegestaan zonder nieuwe review:

- models
- migrations
- urls/routing
- settings/env
- deploy/VPS/compose/Docker/Traefik
- approvals action logic
- buddy-autonomie

## Klaar als

Deze document-slice is klaar als:

- alleen `docs/feeder-workspace-v1-slice.md` is toegevoegd
- er geen codewijzigingen zijn
- `git status --short` schoon is na commit
- de documentdiff apart gereviewd kan worden
