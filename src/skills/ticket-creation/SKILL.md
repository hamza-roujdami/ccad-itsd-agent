---
name: ticket-creation
description: Create ManageEngine ServiceDesk Plus tickets with correct classification, priority verification, and clinical business rules. Load this skill when a user needs a new IT ticket created.
---

## Ticket Creation Workflow

When creating a ticket (via `createRequest`), follow these steps in order:

### Step 0 — Look Up Requester
Before creating the ticket, call `getUserDetails` with the caregiver's email to get
their requester ID and full name. Use these in the `requester` field.
If lookup fails, use the email directly: `{"email_id": "user@clinic.example.com"}`.

### Step 1 — Verify Priority
Call `assess_priority` with the issue subject, description, user's suggested priority,
impact, and urgency. Use the verified priority from the tool's response.

### Step 2 — Classify the Ticket

#### Request Type (Incident vs Service Request)
Classify based on the nature of the request:

| Trigger Words | Classification |
|---|---|
| "not working", "broken", "down", "error", "crash", "failure", "disruption", "unavailable", "stopped" | **Incident** |
| Everything else (new access, install software, request hardware, how-to) | **Service Request** |

Set `request_type` accordingly when creating the ticket.

#### Impact + Urgency
ManageEngine derives priority from impact + urgency. Use this mapping:

| Scenario | Impact | Urgency |
|----------|--------|---------|
| Patient safety / care delivery | 0 - Immediate Patient Care | 3 - Immediate Business Disruption |
| System outage, all users, security breach | 1 - Whole Department | 3 - Immediate Business Disruption |
| Department-wide, multiple users blocked | 2 - Large Number of Caregivers | 2 - Limited Business Disruption |
| Single user, standard IT problem | 4 - Single Caregiver | 4 - Normal Maintenance |
| How-to question, cosmetic, enhancement | 4 - Single Caregiver | 4 - Normal Maintenance |

#### Category (use `viewAllCategories` to confirm)
Pick the best match from `references/categories.md`.

#### Resolver Group (use `viewAllSupportGroups` to confirm)
Pick the best match from `references/resolver-groups.md`.

#### Mode
Always set mode to `{"name": "E-Mail"}` for agent-created tickets.

#### Service Templates
Use `getServiceTemplates` to find the right template. Templates auto-populate downstream fields.

### Step 3 — Apply Clinical Business Rules
Read `references/business-rules.md` for mandatory business rules before submitting.

### Step 4 — Mandatory Fields
Every ticket MUST include these 5 fields or creation will fail:
1. `subject` — short summary (max 50 chars)
2. `requester` — `{"id": "...", "name": "..."}` from getUserDetails (or `{"email_id": "..."}` as fallback)
3. `mode` — `{"name": "E-Mail"}`
4. `group` — `{"name": "SERVICE DESK"}` (or appropriate team)
5. `category` — `{"name": "Software"}` (or appropriate category)

Priority is optional — ManageEngine uses its default if omitted.

### Step 5 — Context Handoff
The ticket description MUST include:
1. **User's original issue** — what they reported
2. **KB articles tried** — which articles were shown and whether they helped
3. **Troubleshooting attempted** — what steps the user already tried
4. **Why escalating** — why self-service could not resolve this
5. **User details** — department, location, affected system (if mentioned)

Format:
```
Issue: [user's problem]
KB Attempted: [articles shown, or "No matching KB articles"]
Steps Tried: [what was attempted]
Escalation Reason: [why ticket is needed]
Additional Context: [department, location, device details]
```
