# TECHNICAL_MASTER_DOCUMENT.md

## CreatorWorkboard — Technical Master Document

**Status:** Active  
**Last updated:** 2026-03-28  
**Environment:** VPS / Docker / Traefik  
**Scope:** Current live technical architecture for CreatorWorkboard

---

## 1. Purpose

This document defines the current technical architecture of CreatorWorkboard.

It exists to make the following explicit:

- what is live now
- what owns which domain
- which stacks are operationally separate
- what is intentionally in scope now
- what is intentionally not in scope now

This document is not a vision deck.
It is the current technical ground truth.

---

## 2. Core build order

CreatorWorkboard follows this build order:

1. internal operations cockpit
2. routing / conversation layer
3. backoffice / monetization layer
4. only then SaaS / productization

This order is deliberate.

The internal machine must work before the public machine grows.
The public site exists as a small support layer, not as the main product surface.

---

## 3. Architecture principles

### 3.1 Separation of ownership
Public and internal surfaces are separate by default.

That means:

- separate stack
- separate routing
- separate failure boundary
- separate deployment ownership

### 3.2 Traefik is the public ingress
All public HTTP/HTTPS traffic should enter through Traefik.

That means:

- no host-level nginx/apache for public routing
- no extra public host port bindings per app
- public services must be attached to `cc_public`
- internal-only services must stay off `cc_public`

### 3.3 Minimal NOW-scope
Anything that does not create direct operational value should stay out of NOW.

That includes:

- premature SaaS structure
- premature multitenancy
- multilingual public infrastructure
- CMS layers
- heavy AI
- broad integrations without direct operational need

### 3.4 Reconstructable live state
Live state should be reconstructable from:

- git-managed files
- explicit environment/config
- stack-level deployment

Manual live-only ownership is not acceptable as a stable end state.

---

## 4. Current domain model

### 4.1 Active domains

Current domain intent:

- `creatorworkboard.com` → public root-site
- `www.creatorworkboard.com` → public root-site alias
- `ops.creatorworkboard.com` → internal ops application

### 4.2 Reserved / later domains

Reserved for later phases only:

- `portal.creatorworkboard.com`
- `account.creatorworkboard.com`

These are not part of NOW.

### 4.3 Ownership boundaries

Current domain ownership is explicitly split:

#### Public owner
- stack: `creatorworkboard-site`
- domains:
  - `creatorworkboard.com`
  - `www.creatorworkboard.com`

#### Internal owner
- stack: `creatorworkboard-ops`
- domain:
  - `ops.creatorworkboard.com`

This separation is intentional.

The public site must not be merged into the ops stack.

---

## 5. Current live stack structure

### 5.1 Public site stack

**Stack name:** `creatorworkboard-site`

**Purpose:**  
Small public frontdoor explaining what CreatorWorkboard is and what it can mean for companies.

**Current characteristics:**
- static site
- Nginx container
- routed through Traefik
- attached to `cc_public`
- no database
- no Redis
- no worker
- no coupling to internal ops logic

**Current page set:**
- `/`
- `/for-teams.html`
- `/how-it-works.html`
- `/why-creatorworkboard.html`
- `/contact.html`

**Current limitations:**
- contact form UI exists
- contact form is not yet connected to a live endpoint
- `www` and apex both serve the site
- canonical redirect can be added later

---

### 5.2 Internal ops stack

**Stack name:** `creatorworkboard-ops`

**Purpose:**  
Internal operations cockpit for creators, channels, operators, assignments, access policy and handoff.

**Current ownership:**
- `ops.creatorworkboard.com`

**Important rule:**  
This stack remains operationally separate from the public root-site.

No public homepage logic should be added to this stack.

---

### 5.3 Traefik

**Role:** public ingress / reverse proxy / TLS termination

**Current behavior:**
- handles public HTTPS routing
- reads Docker provider
- reads file provider
- uses ACME / Let’s Encrypt resolver `le`
- `exposedByDefault: false`

This means all public containers must opt in explicitly with labels.

---

## 6. Current network model

### 6.1 Public network
`cc_public`

This network is the public ingress network.
Any public web-facing service must join this network.

### 6.2 Internal stack networks
Each stack may also have its own local internal network.

Example:
- `creatorworkboard-site_site_net`
- stack-specific internal traffic only

### 6.3 Rule of use
Allowed:
- public web container on `cc_public`
- internal stack network for local isolation

Not allowed:
- putting DB/Redis/worker on `cc_public`
- exposing internal services directly to the public ingress layer

---

## 7. Current public root-site implementation

### 7.1 Stack
`creatorworkboard-site`

### 7.2 Web container
- image: `nginx:alpine`

### 7.3 Routing
Traefik router rule:

- `Host(\`creatorworkboard.com\`) || Host(\`www.creatorworkboard.com\`)`

### 7.4 TLS
Enabled through Traefik with:

- `tls=true`
- `tls.certresolver=le`

### 7.5 Deployment path
Current owner-map:

- `/opt/commandcenter/apps/creatorworkboard-site`

### 7.6 Current structure
```text
/opt/commandcenter/apps/creatorworkboard-site/
├── docker-compose.yml
├── nginx/
│   └── default.conf
└── site/
    ├── index.html
    ├── for-teams.html
    ├── how-it-works.html
    ├── why-creatorworkboard.html
    ├── contact.html
    ├── robots.txt
    ├── sitemap.xml
    └── assets/
        ├── styles.css
        └── site.js
