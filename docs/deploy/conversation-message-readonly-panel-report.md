# Technisch verslag — ConversationMessage read-only panel en huidige main-status

## 1. Oordeel

GO voor afgeronde merge van PR #60 naar `main`.

NO-GO voor deploy/VPS.

De wijziging staat nu op `main`, maar is nog niet live. Omdat PR #60 migration `core.0017_conversation_message` bevat, moet livegang later via een aparte migration-aware deploy-gate.

## 2. Wat net is gedaan

PR #60 is gemerged:

```text
PR: #60 Add conversation message read-only panel
Branch: feat/conversation-message-readonly-panel-v1 → main
Merge result: success
Main commit: 14d6593 Add conversation message read-only panel (#60)
Previous main: 89050cd docs: lock chats message context v1 scope (#59)
```

Lokale `main` is daarna fast-forward bijgewerkt:

```text
89050cd..14d6593
7 files changed
250 insertions
3 deletions
create mode 100644 core/migrations/0017_conversation_message.py
```

## 3. Doel van de slice

```text
Chats Workspace v1 — ConversationMessage read-only panel
```

Doel:

```text
Berichtcontext tonen in het middenpaneel van /chats/ op basis van opgeslagen ConversationMessage-records bij een bestaande ConversationThread.
```

Niet-doel:

```text
geen livechat API
geen realtime sync
geen embedded chatclient
geen send/reply actie
geen import API
geen webhook/background worker
geen operator message create/update flow
geen attachments
geen raw payload
geen metadata
geen Buddy-posting of Buddy-beslissing
```

## 4. Technische inhoud

### Model

Nieuw model:

```text
ConversationMessage
```

Velden:

```text
thread = FK ConversationThread, related_name="conversation_messages"
direction = inbound / outbound / internal_note
sender_label = blank=True
source_message_id = blank=True
body = TextField
occurred_at = DateTimeField(default=timezone.now)
created_at = auto_now_add
```

Meta:

```text
ordering = ["occurred_at", "id"]
index = (thread, occurred_at)
```

### Migration

Nieuwe migration:

```text
core/migrations/0017_conversation_message.py
```

Dependency:

```text
core.0016_creator_customer_stage
```

Impact:

```text
maakt nieuwe tabel voor ConversationMessage
wijzigt geen bestaande data
wijzigt geen bestaande velden
```

### Admin

`ConversationMessage` is geregistreerd in Django admin voor admin-only inspectie/beheer.

Er is geen operator-facing create/update flow toegevoegd.

### Chats view

`ChatHubView` haalt messages alleen op via de gescopete selected thread:

```python
selected_thread.conversation_messages.order_by("occurred_at", "id")
```

Er is geen brede production-query zoals:

```python
ConversationMessage.objects.all()
```

voor zichtbaarheid in `/chats/`.

### Template

`templates/chats/chat_hub.html` toont een read-only panel:

```text
Berichtcontext
Read-only berichten uit de geselecteerde thread.
```

Bij geen messages:

```text
Nog geen berichten vastgelegd voor deze thread.
```

Er is geen formulier, geen knop om berichten toe te voegen, geen send/reply flow.

## 5. Testbewijs

Lokaal vóór commit/merge:

```text
core.tests.test_conversation_thread + core.tests.test_shared_core_v1_views:
64 tests OK

Full test suite:
231 tests OK

makemigrations --check --dry-run:
No changes detected
```

Gedekte cases:

```text
ConversationMessage defaults
required body validation
direction choice validation
/chats/ toont messages van selected_thread
/chats/ lekt geen messages van andere thread
empty state zonder messages
geen "Bericht toevoegen"
geen message_body form field
```

## 6. Scopebewaking

Niet gewijzigd:

```text
forms.py
urls.py
conversation_views.py
settings.py
Docker/Compose
.env
Traefik
CHANGELOG in de code-slice zelf
```

Niet toegevoegd:

```text
livechat API
send/reply action
import/webhook/background worker
operator message create/update flow
attachments
raw payload
metadata
delivery_status
platform sync state
Buddy decisioning/posting
```

## 7. Huidige repo-status

```text
main == origin/main
HEAD = 14d6593
PR #60 merged
ConversationMessage code staat op main
Niet deployed
```

## 8. Deploystatus

```text
NO-GO voor deploy nu
```

Reden:

```text
PR #60 bevat migration 0017
Livegang vereist aparte migration-aware deploy-gate
VPS live commit moet opnieuw read-only bewezen worden
commit range moet opnieuw worden bepaald
database backend en applied migrations moeten opnieuw worden gecontroleerd
backup/migration/rollbackplan moet vóór deploy worden vastgesteld
```

## 9. Verwachte latere deploy-gate

Voor latere deploy naar `14d6593` moet minimaal worden bewezen:

```text
local main == origin/main
full tests groen
makemigrations --check schoon
VPS live commit
VPS git status clean
VPS remote main = 14d6593
live DB migrations applied through 0016
container healthy
Django check OK
SQLite backup vóór migrate
migrate naar 0017
showmigrations bevestigt [X] 0017_conversation_message
browser smoke op /chats/
```

## 10. Eindoordeel

```text
ConversationMessage read-only panel: DONE on main
PR #60: merged
Deploy: NOT DONE
Next step: migration-aware deploy preflight, only when consciously chosen
```
