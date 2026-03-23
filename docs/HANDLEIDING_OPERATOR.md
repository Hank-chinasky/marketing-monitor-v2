# Handleiding — Operator

## Doel van deze rol
De operator gebruikt de app als dagelijkse operationele cockpit.

De operator gebruikt de app om:
- creators te bekijken
- channels te bekijken
- access policy te volgen
- contentbron te vinden
- updates/handoff te lezen
- handmatige acties beter uit te voeren

De operator is dus geen beheerdersrol, maar een uitvoerende werkrol.

---

## Wat je als operator doet

### Dagelijks
- inloggen
- dashboard bekijken
- creator of channel openen
- policy lezen
- contentbron volgen
- platform openen
- werk uitvoeren
- update/handoff noteren of raadplegen

### Niet jouw hoofdtaak
Je bent niet primair verantwoordelijk voor:
- operators aanmaken
- creators structureren
- channels volledig inrichten
- assignments beheren

Dat is vooral adminwerk.

---

## Hoe je de app gebruikt

## 1. Start op het dashboard
Na login kom je op het dashboard.

Daar zie je:
- aandachtspunten
- alerts
- quick access
- creators in scope
- channels met issues

Kijk vooral naar:
- needs reset
- geen 2FA
- VPN/IP gaps
- consent issues

---

## 2. Open de juiste creator
Ga naar:
- **Creators**
of
- klik direct vanaf het dashboard

Op de creatorpagina zie je:
- basisstatus
- consentstatus
- channels
- assignments
- alerts
- netwerkoverzicht

Gebruik dit als centrale werkpagina voor een creator.

---

## 3. Open het juiste channel
Als je aan een specifiek platformaccount werkt, open dan het channel.

Daar zie je:
- platform
- handle
- login identifier
- credential status
- access notes
- 2FA-status
- VPN/IP policy
- laatste operator update

Dit is je belangrijkste accountcontext.

---

## 4. Lees altijd eerst de access policy
Voor je naar het platform gaat, check je:
- is VPN verplicht
- welke regio is goedgekeurd
- welk IP label moet gebruikt worden
- wat is het approved egress IP
- zijn er extra notities

### Belangrijk
Niet zomaar op gevoel inloggen of posten.
De app is juist bedoeld om fouten door verkeerde context te voorkomen.

---

## 5. Check de content source
Bij de creator hoort een contentbron.

Kijk naar:
- content source type
- content source URL
- content source notes
- content ready status

Daaruit haal je:
- waar het materiaal staat
- of het al klaar is
- of er nog iets ontbreekt

---

## 6. Gebruik quick links
Als profile URL aanwezig is, kun je vaak direct doorklikken naar het platform.

Gebruik de app als:
- contextlaag
- policylaag
- navigatielaag

Niet als vervanging van het platform zelf.

---

## Hoe je veilig werkt

### Altijd eerst context
Voor je iets doet:
- lees policy
- lees laatste operator update
- check 2FA-status
- check of credentialsituatie logisch is

### Geen improvisatie met regio/IP
Als VPN vereist is:
- volg de opgegeven policy
- gebruik niet zomaar een andere regio of verbinding

### Kijk naar vorige operator-update
Als er een recente handoff of notitie staat:
- lees die eerst
- voorkom dubbel werk of fouten

---

## Wat je doet bij problemen

### Geen login identifier
Meld het aan admin of kijk of notes/context genoeg geven.

### Needs reset
Niet negeren. Dit is een signaal dat accounttoegang aandacht nodig heeft.

### Geen 2FA
Werk extra voorzichtig en meld dit als risico.

### VPN gap
Als VPN verplicht is maar IP/context ontbreekt:
- ga niet gokken
- laat dit aanvullen

### Geen assignment of verkeerde zichtbaarheid
Meld dit aan admin. Scope moet kloppen.

---

## Praktische werkvolgorde

### Voor contentwerk
1. login
2. dashboard
3. creator openen
4. channel openen
5. policy lezen
6. content source openen
7. platform openen
8. werk uitvoeren
9. update/handoff bekijken of noteren

### Voor overdracht
1. open channel
2. lees laatste operator update
3. werk af of neem over
4. noteer wat de volgende operator moet weten

---

## Wat je níet moet doen
- geen willekeurige platformlogins zonder policycheck
- geen notities alleen buiten de app houden als context in de app thuishoort
- geen creator behandelen zonder te checken of jij daar assignment voor hebt
- geen aannames maken over regio/IP/credentials

---

## Wanneer admin nodig is
Schakel admin in als:
- creator ontbreekt
- channel ontbreekt
- operatorstructuur niet klopt
- assignment mist
- policygegevens missen
- belangrijke basisvelden leeg zijn

---

## Doel van goed operatorgebruik
Goed operatorgebruik betekent:
- minder fouten
- sneller schakelen
- betere overdracht
- minder chaos
- veiliger werken binnen afgesproken policy
