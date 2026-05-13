---
name: ticket-management
description: Check ticket status, add notes, update tickets, or list open tickets. Load this skill when a user asks about existing tickets.
---

## Ticket Management

Use these ManageEngine MCP tools for existing ticket operations:

### Check Ticket Status
When a user asks about an existing ticket:
- Use `requestDetailsById` with the ticket ID
- Show: status, priority, assigned group, last update

### Add Notes
When a user wants to add information to an existing ticket:
- Use `addNote` to append follow-up information
- Include the user's message and any new details

### List Tickets
When a user wants to see open tickets:
- Use `viewAllRequests` to list tickets
- Use `viewAllRequestFilters` to find available filter options
- Summarize results clearly (ticket ID, subject, status, priority)

### Update Tickets
When a user wants to change a ticket:
- Use `updateRequest` to modify priority, status, or assignment
- Confirm the change with the user before applying
