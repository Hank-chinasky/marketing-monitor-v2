# Docs index

## Purpose

This file defines which documents are currently canonical for CreatorWorkboard.

Use this file as the entry point for technical, operational and planning documentation.

---

## Canonical documents

### Technical
- `TECHNICAL_MASTER_DOCUMENT.md`
  - current technical ground truth
  - domains, stacks, routing, boundaries, live architecture

- `DEPLOY_HISTORY.md`
  - deploy log and important infra/runtime changes

### Planning and scope
- `ROADMAP_6_MAANDEN_2026.md`
  - current build order and execution roadmap

- `MVP_SCOPE_VS_V2_SCOPE_VS_VISION_SCOPE.md`
  - scope guardrail for MVP, V2 and vision

- `NOW_LATER_NOT_NOW.md`
  - practical prioritization guardrail

### Roles and operations
- `ROLVERDELING.md`
  - current role boundaries and ownership model

---

## Current live interpretation

### Public surface
- `creatorworkboard-site`
- `creatorworkboard.com`
- `www.creatorworkboard.com`

### Internal surface
- `creatorworkboard-ops`
- `ops.creatorworkboard.com`

The public site is a small frontdoor only.
The internal ops cockpit remains the actual product priority.

---

## Supporting documents

These may be useful, but are not automatically the leading source unless explicitly referenced:

- `roadmap/CREATORWORKBOARD_EXECUTION_ROADMAP_v1.md`
- `roadmap/CREATORWORKBOARD_NOW_NEXT_LATER_v1.md`

Treat these as supporting material unless they are explicitly promoted to canonical status.

---

## Current open follow-up
- connect the public contact form to a real endpoint
- add canonical redirect for apex / `www`
- keep public site small and separate from ops
- avoid duplicate planning documents over time

---

## Documentation rule

If two documents overlap, the canonical document listed in this file wins.

If a document is exploratory, temporary or local-only, it should not become canonical by accident.

Local-only material belongs outside the canonical doc set.
