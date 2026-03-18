# CHANGELOG

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Runnable Django Sprint 1–2 app in repo root
- Django project package: `marketing_monitor/`
- Core app package: `core/`
- Server-rendered templates in root `templates/`
- Runtime models for:
  - `Operator`
  - `Creator`
  - `CreatorChannel`
  - `OperatorAssignment`
- Canon-aligned auth/scope helpers in `core/authz.py`
- Canon-aligned CBV mixins in `core/mixins.py`
- Canon-aligned validation helpers in `core/validators.py`
- Django admin registration for Sprint 1–2 models
- Login/logout flow using Django auth views
- Migration `core.0001_initial`
- Initial runtime tests for:
  - scope/auth semantics
  - creator consent validation
  - channel uniqueness validation
  - admin-only update protection
  - overlap rule for assignments

### Changed
- Repository evolved from governance/reference-only state to real runtime Django app
- Scope/auth behavior implemented server-side in runtime code
- Navigation cleaned up so operator-facing UI is less misleading
- Logout behavior updated to use POST instead of GET
- Root templates completed so login and core screens render correctly

### Fixed
- Broken remote/local `reference` situation where `reference` briefly existed as file instead of directory
- Missing `registration/login.html` causing `TemplateDoesNotExist`
- Test discovery issue where Django initially found 0 tests
- Logout 405 error caused by GET-based logout link
- Misleading operator navigation to admin-only/operator-only screens
- Git hygiene issues around generated files such as `__pycache__`, `*.pyc`, and `db.sqlite3`

### Notes
- `reference/` remains intact as frozen canon/reference and is not the runtime app
- Sprint 1–2 scope remains intentionally limited
- `primary_operator` remains label/default only and is not used as permission source
- Operator UI remains scoped read-only
- Admin write flows remain allowed
