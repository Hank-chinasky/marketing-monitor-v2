# Creator Workboard — App Architecture

Status: active internal build  
Date: 2026-03-20

## 1. Product definition

Creator Workboard is an internal Django operations cockpit for creator/channel management.

It is built to support:
- manual operator workflow
- access policy visibility
- scoped access by assignment
- creator and channel work pages
- content intake / source tracking
- handoff and operational context
- fast navigation and decision support

It is not built as:
- public SaaS
- automation-first publication engine
- embedded social login broker
- plain text credential vault
- external customer portal in this phase

## 2. Current application state

The current runtime app already includes:
- login/logout
- admin
- operations dashboard as root
- creators list
- creator detail as operator work page
- creator network view
- channels list
- channel detail as channel work page
- assignments list
- scoped operator visibility
- admin-only writes
- VPN/IP access policy per channel
- content intake source fields on creator

## 3. Architecture rules

Core rules:
- Django monolith
- server-rendered templates
- standard Django auth
- standard Django admin
- no SPA as primary route
- no API-first architecture as primary route
- SQLite allowed locally, portable toward PostgreSQL later

Permission rules:
- `User` is not `Operator`
- scope comes only from `OperatorAssignment`
- `primary_operator` is never a permission source
- operators are scoped read-focused
- admin handles writes
- scope must be enforced server-side

Security rules:
- no plain text passwords in normal operational views
- dashboard is a control layer, not a login broker
- open-platform flow is allowed
- real credentials stay outside normal operational UI

## 4. Main domain objects

### Creator
Examples of relevant fields:
- display_name
- legal_name
- status
- consent_status
- primary_operator
- notes
- content_source_type
- content_source_url
- content_source_notes
- content_ready_status

### CreatorChannel
Examples of relevant fields:
- platform
- handle
- profile_url
- status
- access_mode
- recovery_owner
- login_identifier
- account_email
- account_phone_number
- credential_status
- access_notes
- last_access_check_at
- two_factor_enabled
- vpn_required
- approved_egress_ip
- approved_ip_label
- approved_access_region
- access_profile_notes
- last_ip_check_at
- last_operator_update
- last_operator_update_at

### OperatorAssignment
Examples of relevant fields:
- operator
- creator
- scope
- starts_at
- ends_at
- active

## 5. Current UX surfaces

Current key surfaces:
- `/` → operations dashboard
- `/creators/` → creators list
- `/creators/<id>/` → creator work page
- `/creators/<id>/network/` → creator network
- `/channels/` → channels queue/list
- `/channels/<id>/` → channel work page
- `/assignments/` → assignments list

## 6. Current product priority

Do not broaden scope unnecessarily.

Current focus:
1. stable operator flow
2. deployment readiness
3. queue + handoff polish
4. internal pilot usage
5. only then broader expansion

## 7. Domain direction

Recommended domain structure:
- `creatorworkboard.com` → root / brand shell
- `www.creatorworkboard.com` → alias/redirect
- `ops.creatorworkboard.com` → internal ops app
- `portal.creatorworkboard.com` → later customer/backoffice surface
- `account.creatorworkboard.com` → only later if central auth becomes necessary

## 8. Deployment stance

For current development phase:
- same VPS is acceptable
- separate app stack required
- separate env required
- separate DB boundary required
- separate domain routing required

Do not let Creator Workboard become just “another page” inside Virtual Development.
