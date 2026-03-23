# Handleiding — Superadmin

## Doel van deze rol
De superadmin bewaakt de hele omgeving:
- toegang
- gebruikers
- deployment
- basisveiligheid
- dataconsistentie
- escalaties

De superadmin is geen gewone dagelijkse operator, maar de eindverantwoordelijke beheerrol.

---

## Wat je als superadmin doet

### Beheer
- nieuwe admins en operators kunnen laten aanmaken of controleren
- controleren of records logisch zijn ingericht
- deploymentstatus controleren
- problemen oplossen als een admin of operator vastloopt

### Controle
- checken of creators, channels en assignments logisch gekoppeld zijn
- checken of belangrijke channels voldoende access policy hebben
- checken of operators alleen de juiste data zien

### Veiligheid
- wachtwoorden resetten indien nodig
- basis auth- en toegangsproblemen oplossen
- opletten dat gevoelige gegevens niet los in notities, shell of chat blijven rondzwerven

---

## Wanneer gebruik je deze rol
Gebruik de superadminrol alleen wanneer nodig:
- bij eerste inrichting
- bij fouten in rollen of data
- bij herstelwerk
- bij livegangchecks
- bij beheer en escalatie

Niet voor elk klein dagelijks werk.

---

## Standaard werkwijze

### 1. Inloggen
- open de ops-omgeving
- ga door Traefik basic auth
- log in met je Django superadmin-account

### 2. Dashboard bekijken
Controleer:
- alerts
- channels zonder 2FA
- channels met needs reset
- VPN/IP gaps
- creators zonder actieve assignment

### 3. Gebruikers en operators controleren
Ga naar:
- Operators

Controleer:
- bestaan de juiste operators
- hebben ze assignments
- hebben belangrijke creators een primary operator

### 4. Basisstructuur controleren
Ga na:
- creators bestaan en hebben logische status
- channels zijn gekoppeld aan juiste creator
- assignments kloppen
- access policy is ingevuld waar nodig

---

## Belangrijkste taken

### A. Nieuwe admin of operator mogelijk maken
Als een nieuw teamlid toegang nodig heeft:
- laat een operator of admin aanmaken via de app
- of corrigeer dit zelf als beheeractie nodig is

### B. Fout in structuur herstellen
Voorbeelden:
- creator aan verkeerde operator gekoppeld
- assignment ontbreekt
- channel hangt aan verkeerde creator
- access policy mist

### C. Livegang of beheercontrole
Voor interne livegang controleer je:
- werkt login
- werkt dashboard
- werken create-formulieren
- staan echte operators/creators/channels erin
- klopt de scope

---

## Waar je op let

### 1. Geen shell-werkwijze als dagelijkse norm
Shell is noodgereedschap.
Normale operationele gegevens moeten via de app beheerd worden.

### 2. Geen losse wachtwoorden
Geen wachtwoorden in:
- notities
- shell history
- losse chats
- onveilige documenten

### 3. Geen valse zekerheid
Als iets “lijkt te werken”, check dan ook:
- rolgedrag
- scope
- opgeslagen data
- terugvindbaarheid in de UI

---

## Checklist superadmin

### Dagelijks / wekelijks
- dashboard gecontroleerd
- alerts bekeken
- operators bestaan en kloppen
- assignments logisch
- creators/channels correct gekoppeld

### Bij wijzigingen
- nieuwe operators correct aangemaakt
- access policy velden ingevuld
- content source aanwezig waar nodig

### Bij incidenten
- wachtwoorden resetten
- toegang herzien
- fouten in records herstellen
- live omgeving controleren

---

## Wanneer escaleren
Escaleren of ingrijpen als:
- operators verkeerde data zien
- login of CSRF stuk is
- deployment unhealthy wordt
- belangrijke channels policy gaps hebben
- team niet meer weet welke workflow leidend is
