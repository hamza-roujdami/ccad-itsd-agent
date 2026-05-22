# Scope & Gap Analysis

## Phase 1 — Current Status

| Scope Requirement | Phase | Status | Notes |
|---|---|---|---|
| Orchestrator — intent detection, routing, context | 1 | ✅ | Single agent + LLM tool-calling |
| Ticket status — retrieve by ID | 1 | ✅ | MCP `requestDetailsById` |
| Follow-up notes — add notes to tickets | 1 | ✅ | MCP `addNote` |
| List open tickets for user | 1 | ✅ | MCP `viewAllRequests` |
| KB-first resolution | 1 | ✅ | `search_kb` → Azure AI Search (33 articles) |
| Category assignment | 1 | ✅ | From skill reference + `viewAllCategories` |
| Priority verification | 1 | ✅ | `assess_priority` — 3-signal weighted vote |
| P0-P2 escalation: log as P3 with [Urgent] | 1 | ✅ | Business rule in `ticket-creation` skill |
| Clinical Engineering → Service Desk rule | 1 | ✅ | Business rule in `ticket-creation` skill |
| Clinical triage decision tree | 1 | ✅ | `clinical-triage` skill — equipment/Epic/non-Epic branching |
| Create ticket in ITSM (ManageEngine) | 1 | ✅ | MCP `createRequest` via APIM |
| Non-IT routing — HR/Facilities/Operations | 1 | ✅ | `non-it-routing` skill |
| Conversation persistence | 1 | ✅ | Cosmos DB (prod) / File (dev) |
| MCP integration (ManageEngine) | 1 | ✅ | `MCPStreamableHTTPTool` — 17 tools |
| Monitoring / App Insights | 1 | ✅ | OpenTelemetry → Agents (Preview) |
| Eval / test suite | 1 | ✅ | 11 pytest tests |
| MAF Skills (token optimization) | 1 | ✅ | 4 skills via `SkillsProvider` |
| Subcategory assignment | 1 | ❌ | Need subcategory data from customer |
| Incident vs Service Request classification | 1 | ❌ | Need `createRequest` field confirmation |
| Priority from historical ticket data | 1 | ❌ | Need ~40k ticket export |
| Core42 Compass via APIM | 1 | ❌ | Need APIM endpoint + key |
| Entra ID auth | 1 | ❌ | Need tenant ID + app registration |
| FCR — Password Reset | 1 | ❌ | Depends on Entra ID |
| Containerization (Docker) | 1 | ❌ | No blocker |

**Phase 1 completion: 17/24 (71%)**

## Phase 2 — Planned

| Scope Requirement | Status |
|---|---|
| Voice channel (Azure Communication Services) | 🔧 In progress — `voice/` module with ACS Call Automation |
| Email channel — auto-triage after ticket creation | ❌ Not started |
| Microsoft Teams channel | ❌ Not started |
| WhatsApp channel (Twilio) | ❌ Not started |
| Document/image attachment processing | ❌ Not started |
| Unified knowledge ingestion (SharePoint) | ❌ Not started |
| Evaluator LLM for response quality scoring | ❌ Not started |
| Cross-channel context preservation | ❌ Not started |
| Multilingual support | ❌ Not started |

## Blockers — Waiting on Customer

| Item | What we need |
|---|---|
| Subcategories | Run `viewAllCategories` on real MCP — does it include subcategories? |
| Core42 Compass | APIM endpoint URL + subscription key + confirm OpenAI-compatible |
| Entra ID | Tenant ID, app registration, auth flow (Teams SSO or web login?) |
| Historical tickets | Export ~40k past tickets as CSV for AI Search indexing |
