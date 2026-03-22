# Changelog

## 2026-03-18
### Added
- Operations Dashboard as root landing page
- Creator network view
- Channel detail / channel work page
- Channel access policy fields:
  - `vpn_required`
  - `approved_egress_ip`
  - `approved_ip_label`
  - `approved_access_region`
  - `access_profile_notes`
  - `last_ip_check_at`
- Channel access/account metadata:
  - `profile_url`
  - `login_identifier`
  - `credential_status`
  - `access_notes`
  - `last_access_check_at`
  - `two_factor_enabled`
- Creator content intake fields:
  - `content_source_type`
  - `content_source_url`
  - `content_source_notes`
  - `content_ready_status`

### Changed
- Creator detail upgraded into operator work page
- Channel list improved with quick access links
- Base template upgraded with navigation, cards, panels and badges
- Dashboard now surfaces operational alerts and quick access
- Routes expanded with creator network and channel detail pages

### Fixed
- Multiple view/url/template wiring issues
- Missing imports in `core/views.py`
- Syntax errors in `core/urls.py`
- Missing dashboard template path
- Model/view mismatch around VPN/IP fields
- Missing navigation links to network and channel detail pages

## 2026-03-18
### Added
- Operations Dashboard as root landing page
- Creator network view
- Channel detail / channel work page
- Channel access policy fields
- Content intake source fields on Creator
- Quick links for creator/channel/platform flow

### Changed
- Creator detail upgraded into operator work page
- Channel list improved with operational quick access
- Base template upgraded with cards, badges, panels and navigation

### Confirmed
- Internal tool first
- Dashboard as control layer
- External shared content source preferred first over direct internal media hosting
