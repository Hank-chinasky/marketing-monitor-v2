# CreatorWorkboard — MVP Scope vs V2 Scope vs Vision Scope

## Kernregel

**Visie is richting, geen backlog.**

CreatorWorkboard wordt niet gebouwd als brede suite.  
De scope wordt per fase hard afgesneden.

---

## Huidige feitelijke status

De MVP is niet meer alleen concept.

De volgende onderdelen bestaan nu al in de app:

- `ProfileOpportunity`
- `OutcomeEntry`
- server-side scoring service
- opportunity queue
- detail view
- queue pagination
- tests op scoring, visibility, ordering en pagination
- admin-seeded creation flow voor V1

Daarom gaat de huidige fase niet meer over “bedenken wat de MVP wordt”, maar over:

- live bewijzen
- aanscherpen
- commercieel veilig positioneren

---

## MVP Scope

## Doel van MVP

Een kleine, dagelijkse **control layer** voor operatorflow.

### MVP moet bewijzen:
- dat operatorwerk beter prioriteerbaar wordt
- dat handoff strakker wordt
- dat next action duidelijker wordt
- dat contextverlies afneemt
- dat outcome discipline verbetert

### MVP zit in `core/`

### MVP bevat

#### Datamodel
- `ProfileOpportunity`
- `OutcomeEntry`

#### Workflow
- operator queue
- detail pane
- handoff note
- outcome log
- manual override met reden

#### Logic
- server-side scoring / prioritization
- score reason short
- recommendation light als afgeleide support

#### Scope
- admin ziet alles
- operator ziet alleen eigen assigned items

#### Gebruiksvorm
- V1 opportunities kunnen via Django admin worden aangemaakt
- creation flow zit nog niet in de app zelf

#### Kwaliteit
- basis tests
- live proof sprint in Mara

---

## MVP bevat expliciet niet

- social intake adapter als verkoopbaar onderdeel
- inbox replacement
- creator/channel-relaties
- assignment-architectuur koppelen aan deze nieuwe slice
- analytics dashboard
- BI
- payout logic
- lead ownership logic
- creator-facing tools
- integrations
- multitenancy
- SaaS packaging
- AI-autopilot
- governance suite
- full CRM-gedrag

---

## V2 Scope

V2 komt pas nadat de MVP in live operatorflow heeft bewezen dat de control layer echt werkt.

### Mogelijke V2-richting
- compacter en scherper detailpane
- betere handoff discipline
- betere stalled visibility
- beperkte operationele metrics
- beperkte intake capture-uitbreiding
- verfijning van recommendation light
- betere pilot-inrichting voor een tweede team

### V2 is nog steeds niet
- inbox replacement
- full CRM
- analytics platform
- brede creator suite
- social intake als standaard commerciële scope

---

## Vision Scope

De vision scope is breder dan MVP en V2, maar wordt nu niet gebouwd.

### Vision bevat potentieel
- internal social intake adapter
- add-on intake modules
- creator-facing tools
- beperkte integrations
- bredere routinglaag
- later mogelijke productisering

### Vision betekent niet
dat dit nu backlog wordt.

---

## Betaalde wedge NOW

### Wel
- operator queue
- handoff
- next action
- context
- risk/policy visibility light
- scoring / prioritization
- outcome log
- recommendation light

### Niet
- social intake
- payout logic
- inbox replacement
- analytics suite
- integrations
- creator tooling

---

## Internal only NOW

Deze onderdelen zijn intern relevant, maar horen niet in de eerste betaalde wedge:

- social media intake adapter
- human intake review
- lead ownership / payout logic
- bron-specifieke intake-experimenten
- cashflow-routing vanuit externe social instroom

---

## Harde beslisregel

Een onderdeel hoort alleen in MVP als het direct helpt bij:

- prioritering
- operatorhandeling
- handoff
- next action clarity
- stalled/blocking visibility
- outcome discipline

Alles daarbuiten is:
- V2
- vision
- of niet doen

---

## Samenvatting

### MVP
smalle control layer, deels al gebouwd, nu live te bewijzen

### V2
verbeterde dagelijkse bruikbaarheid op basis van echt gebruik

### Vision
mogelijke uitbreiding na bewijs

De fout is alles tegelijk willen bouwen.  
De juiste keuze is: eerst de workflow core in live gebruik hard maken.
