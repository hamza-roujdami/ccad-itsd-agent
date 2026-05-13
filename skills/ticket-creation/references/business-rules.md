# CCAD Business Rules (MANDATORY)

These rules override all other classification logic. Violating them will cause
tickets to be rejected or misrouted.

## Rule 1 — No P1/P2 incidents via agent
The agent must NOT create tickets that result in Patient Care or Critical priority.
Instead, add `[Urgent]` at the start of the subject line so the Service Desk can
triage and escalate manually.

Example: `"[Urgent] Epic Hyperspace down for Cardiology department"`

## Rule 2 — Clinical Engineering → Service Desk first
When the issue maps to the `CLINICAL ENGINEERING` resolver group, always assign
to `SERVICE DESK` instead. The Service Desk will triage and forward to Clinical
Engineering if needed.

## Rule 3 — Requester email required
Every ticket must have a valid `requester.email_id`. If the user hasn't provided
their email, ask for it before creating the ticket.

## Rule 4 — Mode is always E-Mail
Agent-created tickets must always set `mode` to `{"name": "E-Mail"}`.
