# Kort technisch verslag — Sanitized Send Preview v1

## 1. Doel

De Operator Composer moest een veilige verzendpreview krijgen vóórdat later een bronhandoff of echte verzendintegratie wordt gebouwd.

De operator kan nu een concept laten controleren op herkenbare contactgegevens. Het systeem toont een gesanitiseerde preview, maar bewaart niets en verzendt niets.

## 2. Productbesluit

Deze slice blijft bewust tussen schrijven en verzenden staan:

```text
concept opstellen
→ server-side contactdata controleren
→ veilige preview tonen
→ menselijke controle
→ geen verzending
```

De bronsoftware blijft de uitvoeromgeving. CreatorWorkboardFlow blijft de operatorlaag erboven.

## 3. Implementatie

### Backend

Er is een nieuwe view toegevoegd:

```text
SanitizedSendPreviewView
```

Route:

```text
POST /chats/send-preview/
```

Belangrijkste eigenschappen:

- login vereist;
- CSRF-beveiligd;
- accepteert uitsluitend JSON;
- verwacht één stringveld `message`;
- weigert lege, ongeldige of te lange payloads;
- maximale lengte: 10.000 tekens;
- gebruikt de centrale `sanitize_contact_data(...)` service;
- geeft alleen gesanitiseerde tekst en veilige metadata terug;
- retourneert altijd `send_available: false`;
- gebruikt `Cache-Control: private, no-store`;
- voert geen databasewrite of externe netwerkactie uit.

Demo-viewers worden daarnaast fail-closed geblokkeerd door de bestaande read-only bescherming.

### Frontend

In `templates/chats/_buddy_reply_focus.html` is een previewpaneel toegevoegd.

Het paneel toont:

- gesanitiseerde tekst;
- rood signaal wanneer contactgegevens zijn gemaskeerd;
- groen signaal wanneer niets is gevonden;
- gedetecteerde categorieën;
- expliciete melding dat niets is opgeslagen of verzonden.

De previewtekst wordt via `textContent` geplaatst en niet als HTML gerenderd.

De oorspronkelijke concepttekst blijft in het textarea staan.

### Race-condition hardening

Tijdens review bleek een stale-response-risico mogelijk:

1. operator start een previewrequest;
2. operator wijzigt direct daarna de tekst;
3. de oude response zou later nog kunnen terugkomen.

Dit is opgelost met:

- `AbortController`;
- annuleren van de actieve request bij input;
- blokkeren van herhaalde previewactie tijdens een lopende request;
- vergelijking van de actuele textarea-inhoud met de oorspronkelijke requesttekst;
- stille afhandeling van `AbortError`.

Hierdoor kan een oude preview niet meer als actuele preview worden getoond.

## 4. Gewijzigde bestanden

```text
core/send_preview_views.py
core/urls.py
templates/chats/_buddy_reply_focus.html
core/tests/test_sanitized_send_preview_v1.py
core/tests/test_buddy_reply_focus_v1.py
```

Geen andere product-, model-, settings-, migration- of infrastructuurbestanden zijn gewijzigd.

## 5. Testresultaten

Gerichte suite:

```text
24 tests
OK
```

Volledige suite:

```text
382 tests
OK
```

Aanvullend:

```text
Django system check: groen
makemigrations --check --dry-run: No changes detected
```

Handmatige browsertests bevestigden:

- e-mailadres en telefoonnummer worden gemaskeerd;
- datum en tijd blijven intact;
- ordernummer blijft intact;
- gewone tekst blijft ongewijzigd;
- preview verdwijnt na conceptwijziging;
- exact één interne POST per klik;
- endpoint retourneert status 200;
- geen externe bronrequest.

## 6. Git- en mergestatus

```text
PR: #107
390909a  Add sanitized send preview v1
8eadd0a  Prevent stale sanitized preview responses
e77ecea  Merge pull request #107
```

De PR is gemerged naar `main`.

## 7. Deploy

Productiecommit:

```text
e77ecea04ab16464a72b6307fc1fa2e83547da2a
```

Vorige productie- en rollbackcommit:

```text
cad2dbd4fd34a85dcbbb709c71d0678ad9d1c4fe
```

Resultaat:

```text
container: healthy
interne healthcheck: 200
publiek zonder Basic Auth: 401
migrations: none
Venice: disabled
real send: disabled
```

## 8. Backup en rollback

Databasebackup:

```text
/opt/commandcenter/backups/creatorworkboard-ops/db-predeploy-20260721T214118Z-cad2dbd.sqlite3
```

SHA-256:

```text
cb2beb53abb4700f26e514a56b24450bb3828f1ca0aaaa08ad707f63a1ec0912
```

Rollback image:

```text
creatorworkboard-ops-rollback:cad2dbd-20260721T214337Z
```

Deploymanifest:

```text
/opt/commandcenter/backups/creatorworkboard-ops/deploy-20260721T214337Z-e77ecea.txt
```

## 9. Deployincidenten

Twee deploypogingen zijn vóór de live switch afgebroken:

1. Django settings waren niet geïnitialiseerd in het losse backup-Pythonproces.
2. Daarna werd de niet-bestaande module `config.settings` gebruikt.

Beide keren bleef productie onaangetast.

De definitieve oplossing was de backup uitvoeren via:

```text
python manage.py shell
```

Daarmee werd automatisch de echte settingsmodule gebruikt:

```text
marketing_monitor.settings
```

Vervolgens is de deploy zonder rollback geslaagd.

## 10. Huidige veiligheidsgrens

Na PR #107 geldt nog steeds:

- geen echte verzending;
- geen automatische source writeback;
- geen provideractivatie;
- geen Venice;
- geen opslag van previewtekst;
- operator blijft eindverantwoordelijk;
- menselijke review blijft verplicht.

## 11. Logische volgende slice

De eerstvolgende verkoopbare stap is een veilige source-aware handoff:

```text
veilige preview
→ veilige tekst kopiëren
→ juiste bron/thread openen
→ operator verzendt handmatig in de bron
```

Ook die stap moet zonder automatische send en zonder bronadapterwrite beginnen.
