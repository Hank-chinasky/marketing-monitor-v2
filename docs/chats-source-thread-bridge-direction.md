# Chats Workspace — source-thread bridge direction

## Doelbeeld

De relevante Mara-chat hoort uiteindelijk zichtbaar en werkbaar te zijn in het middenpaneel van Chats Workspace.

Het middenpaneel is het werkvlak. Voor Chats betekent dat: thread/chat-focus centraal, met context, handoff, open issues en volgende stap direct zichtbaar.

Een externe tab openen is niet het einddoel. Dat is alleen een tijdelijke brug.

## Tijdelijke stap: source-thread bridge v1

De eerste veilige stap is een source-thread bridge.

Deze bridge toont in het middenpaneel:

- geselecteerde Mara-thread
- creator/context
- bronplatform
- laatste handoff
- open issue/open loop
- volgende stap
- tijdelijke actie: Open bronchat

De knop Open bronchat opent het echte Mara-bronplatform.

Deze stap bewijst:

- welke thread de juiste bronchat is
- of de thread binnen scope valt
- of operator-scope klopt
- of bronlink/platformreferentie bestaat
- of het middenpaneel de juiste werkfocus draagt

## Belangrijk

Open bronchat is tijdelijk.

Het is geen eindoplossing voor snelle workflow, maar een gecontroleerde tussenstap voordat embedded source-chat wordt onderzocht.

## Volgende technische verkenning

Na source-thread bridge v1 komt een aparte feasibility-check:

- kan het Mara-platform veilig embedded worden?
- blokkeert het platform iframe/embed?
- is read-only embed mogelijk?
- is platform-native interactie mogelijk zonder Mara als chatclient te maken?
- is een API/connector nodig?
- wat is het minimale veilige model?
- wat zijn login/session-risico’s?

## Mogelijke latere richting

Als feasibility positief is, kan later een aparte slice komen:

Chats middle-panel embedded source view v1

Doel daarvan:

- bronchat zichtbaar in het middenpaneel
- operator blijft in Mara-flow
- geen contextverlies door tabwissel
- geen autonome AI-acties
- geen brede routing engine
- geen multi-platform chatproduct

## Niet nu

Niet bouwen in deze fase:

- embedded live chatfundament
- eigen chatclient
- message sync
- replies vanuit Mara
- OAuth/API-koppeling zonder aparte review
- multi-platform connectorlaag
- routing engine
- conversation layer als hoofdproduct
- Buddy die gesprekken voert
- autonome AI-acties
- SaaS/productisering
- deep integrations

## Eerst te inventariseren

Voor source-thread bridge v1 moet eerst read-only worden uitgezocht:

- bestaat `ConversationThread` al voor Mara?
- welke velden bestaan voor source system?
- bestaat source thread id?
- bestaat source URL of platformlink?
- hoe wordt operator scope bepaald?
- hoe kiest `ChatHubView` nu een thread?
- waarom toont het middenpaneel nu: Geen threads beschikbaar binnen scope?

## Toegestane code-oppervlakken later

Alleen na aparte review:

- Chats view-context
- Chats middenpaneel-template
- Chats tests

Niet zonder aparte review:

- models
- migrations
- routing/url
- settings/env
- deploy/VPS
- platformconnector
- approvals action logic
- buddy-uitbreiding

## Stopregel

Als deze richting een model, migration, routing, settings/env, deploy, connector of embedded platformlaag nodig blijkt te hebben, stopt de slice.

Dan volgt eerst aparte architect- en VPS-review.
