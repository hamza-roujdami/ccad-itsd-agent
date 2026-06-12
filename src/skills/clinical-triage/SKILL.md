---
name: clinical-triage
description: Clinical prioritization decision tree for patient care incidents. Load this skill when the issue involves medical equipment, Epic/clinical systems, or any situation that may impact patient care.
---

## Clinical Triage Decision Tree

When a caregiver reports an issue that may affect patient care, follow this decision tree
to determine the correct priority and escalation path.

### Step 1 — Identify the System Type

Ask the user (if not already clear): **What system or device is affected?**

| System Type | Examples | Go to |
|---|---|---|
| **Medical Equipment** | Patient monitors, infusion pumps, ventilators, imaging devices, crash carts | → Step 2A |
| **Epic (Clinical System)** | Epic Hyperspace, Haiku, MyChart, clinical workflows | → Step 2B |
| **Non-Epic Clinical Apps** | PACS, lab systems, pharmacy systems, Vocera, other clinical software | → Step 2C |

---

### Step 2A — Medical Equipment

1. **Are there alternative devices that can be used or borrowed?**
   - **Yes** → Log as **P3**, assign to **CLINICAL ENGINEERING** (via SERVICE DESK per business rules)
   - **No** → Go to question 2

2. **Does this stop you from providing patient care?**
   - **No** → Log as **P3**, assign to **CLINICAL ENGINEERING** (via SERVICE DESK)
   - **Yes** → Log as **P0** with `[Urgent]` in subject
     - Assign to **SERVICE DESK**
     - Add note: "Clinical Engineering on-call and Incident Management must be informed"
     - Follow-up required every 45 minutes to 1 hour

---

### Step 2B — Epic (Clinical System)

1. **How many people are affected?**
   - **One patient or caregiver** → Go to question 2
   - **Multiple caregivers or patients** → **Escalate to L3 on-call + Incident Management, possible P1/P2**
     - Log with `[Urgent]` in subject
     - Assign to **SERVICE DESK** (who will route to EPIC APPLICATIONS)

2. **Does this stop you from providing patient care?**
   - **No** → Log as **P3**, assign to **EPIC APPLICATIONS** (via SERVICE DESK)
   - **Yes** → Log as **P0** with `[Urgent]` in subject
     - Assign to **SERVICE DESK**
     - Add note: "P0 incident — follow up with resolver after 15 minutes"
     - If not resolved → escalate to L3 on-call

---

### Step 2C — Non-Epic Clinical Apps

1. **Does this stop you from providing patient care?**
   - **No** → Log as **P3**, assign to **SERVICE DESK** for L3 resolver group
   - **Yes** → Go to question 2

2. **How many people are affected?**
   - **One patient or caregiver** → Log as **P3**, assign to **SERVICE DESK**
     - Add note: "Affects patient care for single user — follow up every 45 min to 1 hour"
   - **Multiple patients or caregivers** → Log as **P0** with `[Urgent]` in subject
     - Assign to **SERVICE DESK**
     - Add note: "L3 on-call and Incident Management must be informed"
     - Follow-up required every 45 minutes to 1 hour

---

### Clarifying Questions to Ask

If the user hasn't provided enough detail, ask these questions **in order**:

1. "What system or device is this about?" (determines branch: equipment / Epic / other)
2. "Is this affecting one person or multiple people?"
3. "Are there any workarounds or alternative devices available?"
4. "Is this currently preventing you from providing patient care?"

### Key Rules

- **P0 incidents are always logged as P3 with `[Urgent]` in the subject** (per business rules — the agent cannot create P0/P1/P2 directly)
- **Clinical Engineering issues → always route through SERVICE DESK first**
- **All patient care incidents require follow-up notes** — add the follow-up interval in the ticket description
- **When in doubt about patient impact, treat it as patient care** — it's safer to over-escalate in a hospital
