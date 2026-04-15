# Handleiding Admin — Mara Ops Workboard v1

## Doel
Als admin beheer je de werkcontext van Mara Ops Workboard v1 voor:
- Chats Workspace
- Feeder Workspace

Je rol is nu klein en operationeel:
- context bruikbaar houden
- approvals beoordelen
- operators niet laten werken met onduidelijke of risicovolle basis

## Waar jij op let
Jij kijkt vooral naar:
- policy en access
- completeness
- handoff-discipline
- approvals
- of de workspaces bruikbaar blijven voor dagelijkse operatie

## Approvals v1
Approvals v1 is geen workflow-engine. Het is een kleine beslislaag binnen de bestaande workspaces.

### Approvaltypes
- **Content approval**
- **Action approval**
- **Access exception**

### Statussen
- **Not required**
- **Pending**
- **Approved**
- **Rejected**
- **Expired**

## Wat je als admin kunt doen
Binnen de bestaande workspace-context kun je:
- approval aanmaken
- approvalstatus bekijken
- pending approval goedkeuren
- pending approval afwijzen

## Wanneer maak je een approval aan
Maak een approval alleen aan als extra bevestiging echt nodig is, bijvoorbeeld:
- gevoelige content
- een actie met extra risico
- een toegangsuitzondering
- onduidelijke context waar eerst groen licht nodig is

## Waar approvals zichtbaar zijn
- **Chats**: approvals gekoppeld aan een thread
- **Feeder**: approvals gekoppeld aan een creator

## Belangrijke werkregels
### 1. Houd approvals klein
Geen approval aanmaken “voor de zekerheid” als het niet nodig is.

### 2. Beslis alleen in context
Kijk altijd naar:
- creator
- thread of creator-level context
- handoff
- policy
- completeness alerts

### 3. Fail-closed
Buiten scope mag niets zichtbaar of wijzigbaar zijn.
Een approval buiten scope hoort niet bereikbaar te zijn via directe URL of formuliertruc.

### 4. Pending-only
Alleen approvals met status **Pending** zijn beslisbaar.
Approved, rejected, expired en not_required zijn geen open beslisitems meer.

## Run log
In de run log worden approval-events compact zichtbaar:
- Approval aangemaakt
- Approval goedgekeurd
- Approval afgewezen

Dat helpt bij teruglezen en overdracht zonder zware auditlaag.

## QA-check voor admins
Loop bij twijfel dit rijtje af:
1. Klopt de creator/thread-context?
2. Is scope duidelijk?
3. Is policy bekend?
4. Is de handoff bruikbaar?
5. Is dit echt een approvalgeval?
6. Staat de approval op pending?
7. Is goedkeuren of afwijzen hier verantwoord?

## Werkregel
Approvals zijn bedoeld om de operatie veiliger en duidelijker te maken, niet om een bureaucratisch systeem te bouwen.
