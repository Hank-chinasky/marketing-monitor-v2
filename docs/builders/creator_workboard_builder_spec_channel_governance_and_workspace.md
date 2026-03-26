# CreatorWorkboard — Builder spec voor Channel Governance + Workspace v1

## Oordeel
**NOW**

## Waarom
Dit sluit direct aan op de huidige fase:
- interne operations cockpit
- channel workspace per platform
- context vóór actie
- launch-first platformflow
- sessie starten en afsluiten
- handoff verplicht na sessie

Niet doen:
- geen agency model
- geen meerdere operators per creator als teamlaag
- geen thread/commentlaag
- geen source/destination model
- geen deep platformintegraties
- geen AI-laag

---

# 1. Bouwregel

## Hoofdkeuze
Bouw dit **bovenop het bestaande model**.

Dus:
- `Creator` blijft eigenaar van content source en content ready
- `CreatorChannel` blijft eigenaar van channel-context, access policy en governance-status
- `OperatorAssignment` blijft de scope-bron
- voeg **één lichte sessielaag** toe voor start/stop + handoff

## Niet doen
Nu **geen** aparte modellen bouwen voor:
- `Agency`
- `AgencyMembership`
- `ChannelConnection`
- `Thread`
- `Conversation`
- `Lead`
- `Destination`
- breed `ComplianceCase`
- zware `AuditTrail`

---

# 2. Datamodel — concreet

## 2.1 Bestaande modellen behouden

### `Creator`
Bestaande velden blijven leidend voor contentcontext:
- `display_name`
- `legal_name`
- `status`
- `consent_status`
- `primary_operator`
- `notes`
- `content_source_type`
- `content_source_url`
- `content_source_notes`
- `content_ready_status`

### `CreatorChannel`
Bestaande velden blijven leidend voor channel-context:
- `creator`
- `platform`
- `handle`
- `profile_url`
- `status`
- `access_mode`
- `recovery_owner`
- `login_identifier`
- `credential_status`
- `access_notes`
- `last_access_check_at`
- `two_factor_enabled`
- `vpn_required`
- `approved_egress_ip`
- `approved_ip_label`
- `approved_access_region`
- `access_profile_notes`
- `last_ip_check_at`
- `last_operator_update`
- `last_operator_update_at`

### `OperatorAssignment`
Blijft bron van scope:
- `operator`
- `creator`
- `scope`
- `starts_at`
- `ends_at`
- `active`

---

## 2.2 CreatorChannel uitbreiden

### Doel
Niet een nieuw governance-systeem bouwen, maar de channelkaart compleet genoeg maken om:
- veilig te starten
- minder context te verliezen
- blokkades te zien vóór platformwerk
- dagelijkse handoff af te dwingen

### Nieuwe velden op `CreatorChannel`

#### Eigendom / governance
- `legal_owner_name` — `CharField(max_length=255, blank=True)`
- `owner_identity_verified` — `BooleanField(default=False)`
- `management_consent_status` — `CharField(choices=["missing", "partial", "confirmed"], default="missing")`
- `collaborator_docs_status` — `CharField(choices=["na", "missing", "present"], default="na")`

#### Toegang / recovery
- `recovery_email` — `EmailField(blank=True)`
- `recovery_phone` — `CharField(max_length=50, blank=True)`
- `two_factor_method` — `CharField(choices=["unknown", "app", "sms", "email", "other"], default="unknown")`
- `backup_codes_status` — `CharField(choices=["unknown", "missing", "stored"], default="unknown")`
- `native_team_access_available` — `BooleanField(default=False)`
- `native_team_access_active` — `BooleanField(default=False)`
- `password_reset_required` — `BooleanField(default=False)`

#### Veiligheid / policy
- `wrong_region_risk` — `BooleanField(default=False)`
- `recovery_tested_at` — `DateTimeField(null=True, blank=True)`
- `platform_warning_status` — `CharField(choices=["none", "warning", "restricted"], default="none")`

#### Werkbaarheid
- `work_mode` — `CharField(choices=["launch_first", "monitoring", "support", "other"], default="launch_first")`
- `work_note` — `TextField(blank=True)`
- `biggest_blocker` — `TextField(blank=True)`
- `next_action` — `TextField(blank=True)`

#### Readiness / risico
- `policy_status` — `CharField(choices=["missing", "partial", "ready"], default="missing")`
- `channel_readiness` — `CharField(choices=["go", "go_with_conditions", "no_go"], default="no_go")`
- `policy_risk_level` — `CharField(choices=["low", "medium", "high"], default="medium")`
- `compliance_risk_level` — `CharField(choices=["low", "medium", "high"], default="medium")`
- `open_issue_count` — `PositiveIntegerField(default=0)`

### Geen extra velden nu
Niet toevoegen in v1:
- scoring engine
- automation flags
- connector states
- thread counts
- team role matrix
- destination-platform velden

---

## 2.3 Nieuw model: `ChannelWorkSession`

### Waarom
Jullie willen nu expliciet:
- sessie starten vanuit dashboard
- sessie afsluiten
- handoff na sessie afdwingen
- operator-output later kunnen meten

Dat vraagt om een lichte, expliciete sessietabel.

### Model
```python
class ChannelWorkSession(models.Model):
    channel = models.ForeignKey("CreatorChannel", on_delete=models.CASCADE, related_name="work_sessions")
    creator = models.ForeignKey("Creator", on_delete=models.CASCADE, related_name="work_sessions")
    operator = models.ForeignKey("Operator", on_delete=models.CASCADE, related_name="work_sessions")

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=[
            ("active", "Active"),
            ("completed", "Completed"),
            ("blocked", "Blocked"),
        ],
        default="active",
    )

    launch_url = models.URLField(blank=True)
    launched_to_platform_at = models.DateTimeField(null=True, blank=True)

    session_goal = models.CharField(max_length=255, blank=True)
    work_done_summary = models.TextField(blank=True)
    blocker_note = models.TextField(blank=True)
    handoff_note = models.TextField(blank=True)
    next_action = models.TextField(blank=True)
    ready_for_next_operator = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Validaties
- operator moet assignment hebben op `creator`
- slechts 1 actieve sessie per `(channel, operator)`
- `ended_at` verplicht als `status != active`
- `handoff_note` verplicht bij afsluiten
- `next_action` verplicht bij afsluiten

### Side effects bij afsluiten
Bij sessie-afsluiting:
- `CreatorChannel.last_operator_update = handoff_note`
- `CreatorChannel.last_operator_update_at = ended_at`
- `CreatorChannel.biggest_blocker` optioneel updaten
- `CreatorChannel.next_action` updaten

---

## 2.4 Optioneel klein model: `AccessAudit`

Alleen gebruiken als het al bestaat of heel licht toegevoegd kan worden.
Niet breed inzetten.
Alleen loggen bij:
- access_mode wijziging
- 2FA wijziging
- password reset bevestigd
- readiness veranderd naar `no_go`
- assignment revoked

Geen brede audittrail.

---

# 3. Admin-formulieren

## 3.1 Channel form — secties
Gebruik **één edit-scherm** voor channelbeheer met duidelijke veldgroepen.

### Sectie A — Basis
- creator
- platform
- handle
- profile_url
- status
- work_mode

### Sectie B — Access
- access_mode
- login_identifier
- credential_status
- recovery_owner
- recovery_email
- recovery_phone
- password_reset_required

### Sectie C — 2FA / Policy
- two_factor_enabled
- two_factor_method
- backup_codes_status
- vpn_required
- approved_access_region
- approved_egress_ip
- approved_ip_label
- wrong_region_risk
- access_profile_notes

### Sectie D — Governance
- legal_owner_name
- owner_identity_verified
- management_consent_status
- collaborator_docs_status
- native_team_access_available
- native_team_access_active
- policy_status

### Sectie E — Werkbaarheid
- work_note
- biggest_blocker
- next_action
- channel_readiness
- policy_risk_level
- compliance_risk_level

### Sectie F — Controle
- last_access_check_at
- recovery_tested_at
- platform_warning_status

## 3.2 Form-validaties
- `approved_access_region` verplicht als `vpn_required=True`
- `two_factor_method` niet `unknown` laten als `two_factor_enabled=True`
- `channel_readiness="go"` alleen toestaan als:
  - `policy_status="ready"`
  - `content_ready_status` op creator niet leeg is
  - `two_factor_enabled` bekend is
  - `biggest_blocker` leeg is of expliciet opgelost

---

# 4. Operator-formulieren

## 4.1 Start session form
Klein houden.

Velden:
- hidden: channel
- hidden: creator
- session_goal

Knoppen:
- `Start session`
- `Start and launch platform`

## 4.2 End session / handoff form
Verplicht bij sessie-afsluiting.

Velden:
- work_done_summary
- blocker_note
- handoff_note
- next_action
- ready_for_next_operator
- status (`completed` / `blocked`)

Regels:
- geen sessie sluiten zonder `handoff_note`
- geen sessie sluiten zonder `next_action`

---

# 5. Tabnamen en schermstructuur

## 5.1 Creator Detail
Hou dit dicht bij de bestaande documentatie.

### Tabs
1. `Overview`
2. `Channels`
3. `Content`
4. `Publish Log`
5. `Results`
6. `Audit`

### Niet doen
Geen aparte top-level tab voor governance op creatorniveau.
Governance hoort op channelniveau.

## 5.2 Channel Detail
Nieuw of scherper detailscherm binnen `Channels`.

### Tabs
1. `Overview`
2. `Governance`
3. `Access Policy`
4. `Workspace`
5. `Activity`

### Betekenis
- `Overview` = kernsamenvatting
- `Governance` = juridische/eigendom/toegang/compliance-status
- `Access Policy` = VPN, regio, IP, do-not-do, recovery-instructie
- `Workspace` = operator-context vóór platformactie
- `Activity` = sessies, handoffs, laatste updates

## 5.3 Operator workspace-blokken
Geen tabs nodig als dit één werkscherm is.
Gebruik vaste blokken:
1. `Channel Readiness`
2. `What you need to know`
3. `Content Context`
4. `Last Handoff`
5. `Actions`

---

# 6. View- en autorisatielogica

## Admin
- volledige CRUD op channels en sessies
- readiness en governance bewerkbaar

## Operator
- mag alleen channels zien binnen actieve assignment-scope
- mag workspace openen voor scoped channel
- mag sessie starten/afsluiten voor scoped channel
- mag geen governance-velden wijzigen
- mag geen creator/channel structuur wijzigen

## Belangrijke regel
Autorisatie blijft server-side op assignment-scope.
Nooit op `primary_operator`.

---

# 7. Template-opbouw

## 7.1 Channel detail template
Bestand:
- `templates/core/channels/detail.html`

Componenten:
- status badge (`GO / GO WITH CONDITIONS / NO GO`)
- quick facts bar
- tabs
- per tab één partial

Partial suggesties:
- `_channel_overview.html`
- `_channel_governance.html`
- `_channel_access_policy.html`
- `_channel_workspace_summary.html`
- `_channel_activity.html`

## 7.2 Workspace template
Bestand:
- `templates/core/workspace/channel_workspace.html`

Componenten:
- readiness banner
- contextblok
- contentblok
- handoffblok
- start session knop
- launch knop
- end session form

---

# 8. Concreet bouwvolgorde

## Stap 1
`CreatorChannel` uitbreiden met governance/readiness/workability velden.

## Stap 2
Admin channel form opdelen in secties.

## Stap 3
Channel detail pagina met tabs bouwen.

## Stap 4
`ChannelWorkSession` model + migration toevoegen.

## Stap 5
Operator workspace bouwen met:
- readiness card
- context vóór actie
- start session
- launch button
- end session + handoff verplicht

## Stap 6
Laatste sessie/handoff tonen op channel detail en workspace.

## Stap 7
Tests:
- operator buiten scope geblokkeerd
- operator mag wel sessie starten binnen scope
- handoff verplicht bij sessie-afsluiting
- `channel_readiness=go` validatie werkt

---

# 9. Wat bewust NIET nu gebouwd wordt

## LATER
- meerdere operators per creator als rolstructuur
- thread/commentlaag
- source/destination model
- ChannelConnection
- echte connectorstatus
- scoring engine
- uitgebreide audittrail
- compliance case management

## NOT NOW
- agency model
- multitenancy
- billing
- AI samenvatting
- AI assist
- deep OnlyFans/Fansly integratie
- realtime chat
- social platform cloning

---

# 10. Harde conclusie

De juiste NOW-bouw is:
- bestaande `Creator` en `CreatorChannel` respecteren
- `CreatorChannel` uitbreiden voor governance/readiness
- `OperatorAssignment` als scope-bron houden
- één lichte `ChannelWorkSession` toevoegen voor start/stop/handoff
- channel detail tabs scherp maken
- operator workspace klein en dwingend bruikbaar maken

Niet groter maken dan dit.

Dit levert direct meer dagelijkse bruikbaarheid op.
Dit vermindert contextverlies.
Dit maakt handoff hard.
Dit houdt de cockpit klein genoeg om echt gebruikt te worden.

