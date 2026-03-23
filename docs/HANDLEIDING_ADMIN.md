# Handleiding — Admin

## Doel van deze rol
De admin beheert de operationele structuur van het systeem.

De admin zorgt dat de app bruikbaar blijft door:
- operators aan te maken
- creators aan te maken
- channels aan te maken
- assignments aan te maken
- operationele context correct vast te leggen

De admin is dus de rol die het systeem voedt en onderhoudt.

---

## Wat je als admin doet

### Structuur opbouwen
- nieuwe operator toevoegen
- nieuwe creator toevoegen
- nieuwe channels toevoegen
- assignments koppelen

### Structuur onderhouden
- records aanvullen of corrigeren
- access policy invullen
- content source invullen
- status en consent bijwerken

### Kwaliteitscontrole
- controleren of operators de juiste creators hebben
- controleren of channels genoeg informatie bevatten
- controleren of de dashboard-signalen logisch zijn

---

## Kernonderdelen van de app

### Operators
Hier beheer je operationele gebruikers in de businesslaag.

Belangrijk:
een operator is niet alleen een Django user, maar ook een gekoppeld `Operator` record.

### Creators
Hier leg je vast:
- naam
- status
- consent
- primary operator
- contentbron
- notities

### Channels
Hier leg je vast:
- platform
- handle
- login identifier
- credential status
- 2FA-status
- VPN/IP policy
- laatste operator update

### Assignments
Hier leg je vast:
- welke operator aan welke creator gekoppeld is
- met welke scope
- vanaf wanneer
- tot wanneer
- actief of niet

---

## Nieuwe operator aanmaken

### Wanneer
Als een nieuw teamlid toegang moet krijgen tot het systeem en later creators moet kunnen behandelen.

### Stappen
1. Ga naar **Operators**
2. Klik op **Nieuwe operator**
3. Vul in:
   - username
   - e-mail
   - voornaam
   - achternaam
   - wachtwoord
4. Sla op

### Resultaat
De app maakt:
- een Django user
- een gekoppeld `Operator` record

### Controle
Controleer daarna of de nieuwe operator zichtbaar is in de operatorlijst.

---

## Nieuwe creator aanmaken

### Wanneer
Als een nieuwe creator operationeel opgenomen moet worden.

### Stappen
1. Ga naar **Creators**
2. Klik op **Nieuwe creator**
3. Vul minimaal in:
   - display name
   - status
   - consent status
   - primary operator
4. Vul waar mogelijk ook in:
   - legal name
   - notes
   - content source type
   - content source URL
   - content source notes
   - content ready status
5. Sla op

### Let op
Een actieve creator hoort normaal ook actieve consent te hebben.

---

## Nieuw channel aanmaken

### Wanneer
Als een creator een nieuw platformaccount of kanaal heeft dat beheerd of opgevolgd moet worden.

### Stappen
1. Ga naar **Channels**
2. Klik op **Nieuw channel**
3. Vul minimaal in:
   - creator
   - platform
   - handle
   - status
   - access mode
   - recovery owner
4. Vul vervolgens zoveel mogelijk operationele context in:
   - profile URL
   - login identifier
   - credential status
   - access notes
   - 2FA-status
   - VPN required
   - approved region
   - approved IP label
   - approved egress IP
   - policy notes
   - laatste operator update
5. Sla op

### Belangrijk
Voor gevoelige channels moet access policy serieus worden ingevuld.  
Niet leeg laten als operators anders van verkeerde regio/IP werken.

---

## Nieuwe assignment aanmaken

### Wanneer
Als een operator operationeel verantwoordelijk moet zijn voor een creator.

### Stappen
1. Ga naar **Assignments**
2. Klik op **Nieuwe assignment**
3. Vul in:
   - operator
   - creator
   - scope
   - startdatum
   - einddatum indien van toepassing
   - active
4. Sla op

### Resultaat
De scope van de operator wordt hiermee bepaald.

---

## Wat je altijd moet controleren

### Bij creators
- klopt status
- klopt consent
- klopt primary operator
- is content source bekend

### Bij channels
- klopt platform + handle
- is 2FA-status ingevuld
- is login identifier ingevuld
- is VPN-policy ingevuld waar nodig
- is laatste operator update bruikbaar

### Bij assignments
- juiste operator
- juiste creator
- juiste scope
- geen onlogische overlap
- active klopt

---

## Veelgemaakte fouten

### 1. Creator zonder assignment
Dan is de creator operationeel slecht vindbaar of niet goed toegewezen.

### 2. Channel zonder identifier of policy
Dan mist de operator context en wordt foutgevoelig gewerkt.

### 3. VPN required zonder IP label of egress IP
Dan is beleid wel bedacht, maar niet uitvoerbaar gemaakt.

### 4. Operator-user zonder echte businesskoppeling
Een Django user alleen is niet genoeg; het gekoppelde `Operator` record moet bestaan.

---

## Dagelijkse admin-check
Loop dagelijks of regelmatig dit langs:
- staan er creators zonder assignment
- staan er channels zonder 2FA
- staan er channels met credential reset nodig
- zijn er policy gaps
- zijn nieuwe teamleden correct ingericht

---

## Doel van goed adminwerk
Als admin maak je de tool niet mooier voor de techniek, maar bruikbaarder voor de operatie.

Goed adminwerk betekent:
- minder zoeken
- minder fouten
- betere overdracht
- duidelijkere verantwoordelijkheid
