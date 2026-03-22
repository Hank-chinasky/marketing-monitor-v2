## 2026-03-18 — Content intake is modeled as source-based and future-proof
**Decision**  
Content intake is stored as source metadata on Creator, not as a forced internal media-hosting model.

**Why**  
This keeps the current workflow light and legally/operationally simpler, while allowing later transition to internal storage without breaking the domain model.

**Consequence**  
Creator now stores:
- `content_source_type`
- `content_source_url`
- `content_source_notes`
- `content_ready_status`
## 2026-03-18
- documented decision: content intake modeled as source-based metadata on `Creator`
