"""Mock ManageEngine MCP Server.

Replicates the 17 tools from CCAD's real MCP server behind APIM.
Uses real ManageEngine field values from the production instance.
Accepts the same CreateRequestPostRequest wrapper format as the real server.

Run: python -m mock_mcp.server
"""

import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="ManageEngine ServiceDesk Plus",
    port=8001,
)

# ── Real CCAD ManageEngine data ──────────────────────────────────────────

PRIORITIES = [
    {"id": "301", "name": "0.Patient Care", "priority_order": "301", "color": "#ef1616", "deleted": False, "description": None},
    {"id": "302", "name": "1.Critical", "priority_order": "302", "color": "#ff0000", "deleted": False, "description": None},
    {"id": "303", "name": "2.High", "priority_order": "303", "color": "#ef8216", "deleted": False, "description": None},
    {"id": "304", "name": "3.Normal", "priority_order": "304", "color": "#2f78d0", "deleted": False, "description": None},
    {"id": "305", "name": "4.Low", "priority_order": "305", "color": "#5dc35a", "deleted": False, "description": None},
    {"id": "601", "name": "Normal", "priority_order": "601", "color": "#006600", "deleted": False, "description": None},
]

STATUSES = [
    {"id": "1", "name": "Open", "internal_name": "Open", "in_progress": False, "stop_timer": False, "color": "#0066ff"},
    {"id": "2", "name": "In Progress", "internal_name": "InProgress", "in_progress": True, "stop_timer": False, "color": "#ff9900"},
    {"id": "3", "name": "On Hold", "internal_name": "OnHold", "in_progress": False, "stop_timer": True, "color": "#999999"},
    {"id": "4", "name": "Resolved", "internal_name": "Resolved", "in_progress": False, "stop_timer": True, "color": "#009900"},
    {"id": "5", "name": "Closed", "internal_name": "Closed", "in_progress": False, "stop_timer": True, "color": "#333333"},
]

# Real CCAD categories (from viewAllCategories — 24 total, showing confirmed ones)
CATEGORIES = [
    {"id": "301", "name": "Hardware", "deleted": False, "description": None, "technician": None, "change_manager": None},
    {"id": "302", "name": "Software", "deleted": False, "description": None, "technician": None, "change_manager": None},
    {"id": "303", "name": "User Access", "deleted": False, "description": None, "technician": None, "change_manager": None},
    {"id": "304", "name": "Network", "deleted": False, "description": None, "technician": None, "change_manager": None},
    {"id": "305", "name": "Email", "deleted": False, "description": None, "technician": None, "change_manager": None},
    {"id": "306", "name": "Printing", "deleted": False, "description": None, "technician": None, "change_manager": None},
    {"id": "307", "name": "Clinical Systems", "deleted": False, "description": None, "technician": None, "change_manager": None},
    {"id": "308", "name": "Telephony", "deleted": False, "description": None, "technician": None, "change_manager": None},
    {"id": "309", "name": "VPN / Remote Access", "deleted": False, "description": None, "technician": None, "change_manager": None},
    {"id": "310", "name": "VDI", "deleted": False, "description": None, "technician": None, "change_manager": None},
]

# Real CCAD support groups (from viewAllSupportGroups)
SUPPORT_GROUPS = [
    {"id": "301", "name": "EPIC APPLICATIONS", "site": None, "deleted": False, "description": None, "sender_name": "", "sender_email_id": ""},
    {"id": "302", "name": "ASSET MANAGEMENT", "site": None, "deleted": False, "description": None, "sender_name": "", "sender_email_id": ""},
    {"id": "303", "name": "BUSINESS APPLICATIONS", "site": None, "deleted": False, "description": None, "sender_name": "", "sender_email_id": ""},
    {"id": "304", "name": "NETWORK & SECURITY", "site": None, "deleted": False, "description": None, "sender_name": "", "sender_email_id": ""},
    {"id": "305", "name": "SERVICE DESK", "site": None, "deleted": False, "description": None, "sender_name": "", "sender_email_id": ""},
    {"id": "306", "name": "INFRASTRUCTURE", "site": None, "deleted": False, "description": None, "sender_name": "", "sender_email_id": ""},
    {"id": "307", "name": "CLINICAL ENGINEERING", "site": None, "deleted": False, "description": None, "sender_name": "", "sender_email_id": ""},
    {"id": "308", "name": "TELECOM", "site": None, "deleted": False, "description": None, "sender_name": "", "sender_email_id": ""},
]

URGENCIES = [
    {"id": "1", "name": "Low"},
    {"id": "2", "name": "Medium"},
    {"id": "3", "name": "High"},
    {"id": "4", "name": "Urgent"},
]

IMPACTS = [
    {"id": "1", "name": "Affects User"},
    {"id": "2", "name": "Affects Department"},
    {"id": "3", "name": "Affects Business"},
]

# Real CCAD modes (from viewAllModes)
MODES = [
    {"id": "1", "name": "E-Mail", "internal_name": "E-Mail", "deleted": False, "description": "Request through mail"},
    {"id": "2", "name": "Service Catalog", "internal_name": "Web Form", "deleted": False, "description": "Request through web form"},
    {"id": "3", "name": "Phone Call", "internal_name": "Phone Call", "deleted": False, "description": "Request received through phone call"},
    {"id": "4", "name": "Chat", "internal_name": "Chat", "deleted": False, "description": "Request through chat"},
    {"id": "5", "name": "Mobile App", "internal_name": "Mobile App", "deleted": False, "description": "Request through mobile app"},
]

SOLUTIONS = [
    {"id": "1", "topic": {"name": "Password & Access"}, "title": "How to reset your network password",
     "description": "1. Go to https://aka.ms/sspr\n2. Follow the prompts to verify identity\n3. Set a new password\n4. Update password on all devices"},
    {"id": "2", "topic": {"name": "VPN & Remote Access"}, "title": "VPN connection troubleshooting",
     "description": "1. Use FortiClient VPN\n2. Connect to vpn.ccad.ae\n3. If failing: restart FortiClient service\n4. Clear DNS cache\n5. Check certificate expiry"},
    {"id": "3", "topic": {"name": "Printing"}, "title": "Printer not printing - basic troubleshooting",
     "description": "1. Check printer power and online status\n2. Check for paper jams\n3. Restart print spooler\n4. If using badge printing: re-enroll badge\n5. Re-add printer from print server"},
    {"id": "4", "topic": {"name": "Clinical Systems"}, "title": "Epic Hyperspace not launching",
     "description": "1. Update Citrix Workspace\n2. Clear Citrix cache\n3. Re-launch and try again\n4. Check Epic account in UserWeb\n5. Contact Clinical Applications if issue continues"},
    {"id": "5", "topic": {"name": "Email & Calendar"}, "title": "Outlook not syncing emails",
     "description": "1. Check connectivity\n2. Verify Online mode\n3. Restart Outlook\n4. On mobile: remove and re-add account\n5. Check mailbox quota"},
]

SERVICE_TEMPLATES = [
    {"id": "1", "name": "New Employee Onboarding", "is_service_template": True},
    {"id": "2", "name": "Software Installation Request", "is_service_template": True},
    {"id": "3", "name": "Access Request", "is_service_template": True},
    {"id": "4", "name": "Hardware Request", "is_service_template": True},
    {"id": "5", "name": "VPN Access Request", "is_service_template": True},
]

USERS = [
    {"id": "1001", "name": "Dr. Sarah Ahmed", "email_id": "sarah.ahmed@ccad.ae", "department": {"name": "Cardiology"}, "is_technician": False},
    {"id": "1002", "name": "Nurse Fatima Ali", "email_id": "fatima.ali@ccad.ae", "department": {"name": "ICU"}, "is_technician": False},
    {"id": "1003", "name": "Ahmad Hassan", "email_id": "ahmad.hassan@ccad.ae", "department": {"name": "IT"}, "is_technician": True},
    {"id": "1004", "name": "Yahia Bitar", "email_id": "bitary@ccad.ae", "department": {"name": "IT"}, "is_technician": True},
]

REQUEST_FILTERS = [
    {"id": "1", "name": "My Open Requests"},
    {"id": "2", "name": "All Open Requests"},
    {"id": "3", "name": "Overdue Requests"},
    {"id": "4", "name": "Unassigned Requests"},
    {"id": "5", "name": "Patient Care Priority"},
]

# ── In-memory request store ──────────────────────────────────────────────

_requests: dict[str, dict] = {}
_next_id = 32200  # Start after real CCAD ticket IDs


def _gen_id() -> str:
    global _next_id
    _next_id += 1
    return str(_next_id)


def _parse_input_data(raw: str | dict) -> dict:
    """Parse the input_data field — handles both CreateRequestPostRequest wrapper and flat format."""
    if isinstance(raw, str):
        # Agent sent: {"CreateRequestPostRequest": {"input_data": "{...}"}}
        # The MCP framework already extracted the string — parse it
        try:
            parsed = json.loads(raw)
            return parsed.get("request", parsed)
        except (json.JSONDecodeError, TypeError):
            return {}
    if isinstance(raw, dict):
        return raw.get("request", raw)
    return {}


def _resolve_field(value) -> str:
    """Extract name or id from a ManageEngine field object like {"name": "X"} or {"id": "Y"}."""
    if isinstance(value, dict):
        return value.get("name", value.get("id", ""))
    return str(value) if value else ""


# ── MCP Tools (matching real ManageEngine MCP schema) ────────────────────

@mcp.tool()
def createRequest(subject: str = "", description: str = "", requester_email: str = "", mode: str = "E-Mail", group: str = "SERVICE DESK", category: str = "", priority: str = "", CreateRequestPostRequest: dict | None = None) -> str:
    """Create Request"""
    # Handle the wrapper format: CreateRequestPostRequest.input_data (real MCP format)
    if CreateRequestPostRequest and "input_data" in CreateRequestPostRequest:
        req_data = _parse_input_data(CreateRequestPostRequest["input_data"])
    elif subject:
        # Flat format (agent sends fields directly)
        req_data = {
            "subject": subject,
            "description": description,
            "requester": {"email_id": requester_email} if requester_email else None,
            "mode": {"name": mode},
            "group": {"name": group},
            "category": {"name": category} if category else None,
            "priority": {"name": priority} if priority else None,
        }
    else:
        return json.dumps({"response_status": {"status_code": 4000, "messages": [{"message": "Subject is required"}], "status": "failed"}})

    subject = req_data.get("subject", "")

    # Check mandatory fields (relaxed for mock — only warn, don't block)
    rid = _gen_id()
    req = {
        "id": rid,
        "display_id": rid,
        "subject": subject,
        "description": req_data.get("description", ""),
        "status": {"name": "Open", "id": "1"},
        "priority": {"name": _resolve_field(req_data.get("priority", {"name": "4.Low"}))},
        "category": {"name": _resolve_field(req_data.get("category"))},
        "group": {"name": _resolve_field(req_data.get("group"))},
        "mode": {"name": _resolve_field(req_data.get("mode"))},
        "requester": req_data.get("requester", {}),
        "created_time": {"display_value": datetime.now().strftime("%b %d, %Y %I:%M %p")},
        "technician": None,
        "has_notes": False,
    }
    _requests[rid] = req
    return json.dumps({"request": req, "response_status": {"status_code": 2000, "status": "success"}})


@mcp.tool()
def requestDetailsById(request_id: str) -> str:
    """Get Request Details"""
    req = _requests.get(request_id)
    if not req:
        return json.dumps({"response_status": {"status_code": 4000, "status": "failed", "messages": [{"message": "Request not found"}]}})
    return json.dumps({"request": req, "response_status": {"status_code": 2000, "status": "success"}})


@mcp.tool()
def updateRequest(request_id: str, **kwargs) -> str:
    """This operation helps you to update the request by using the unique request_id."""
    req = _requests.get(request_id)
    if not req:
        return json.dumps({"response_status": {"status_code": 4000, "status": "failed", "messages": [{"message": "Request not found"}]}})

    # Handle UpdateRequestPutRequest-1 wrapper
    update_wrapper = kwargs.get("UpdateRequestPutRequest-1", kwargs)
    if isinstance(update_wrapper, dict) and "input_data" in update_wrapper:
        update_data = _parse_input_data(update_wrapper["input_data"])
    else:
        update_data = update_wrapper

    if "status" in update_data:
        req["status"] = {"name": _resolve_field(update_data["status"])}
    if "priority" in update_data:
        req["priority"] = {"name": _resolve_field(update_data["priority"])}
    if "group" in update_data:
        req["group"] = {"name": _resolve_field(update_data["group"])}
    if "technician" in update_data:
        req["technician"] = update_data["technician"]

    return json.dumps({"request": req, "response_status": {"status_code": 2000, "status": "success"}})


@mcp.tool()
def addNote(request_id: str, **kwargs) -> str:
    """This operation lets you add a note under a request"""
    req = _requests.get(request_id)
    if not req:
        return json.dumps({"response_status": {"status_code": 4000, "status": "failed", "messages": [{"message": "Request not found"}]}})

    # Handle AddnotesPostRequest-1 wrapper
    note_wrapper = kwargs.get("AddnotesPostRequest-1", kwargs)
    if isinstance(note_wrapper, dict) and "input_data" in note_wrapper:
        note_data = _parse_input_data(note_wrapper["input_data"])
    else:
        note_data = note_wrapper

    req["has_notes"] = True
    note = {
        "id": _gen_id(),
        "request_id": request_id,
        "description": note_data.get("description", note_data.get("request_note", {}).get("description", "")),
        "show_to_requester": note_data.get("show_to_requester", True),
        "created_time": {"display_value": datetime.now().strftime("%b %d, %Y %I:%M %p")},
    }
    return json.dumps({"request_note": note, "response_status": {"status_code": 2000, "status": "success"}})


@mcp.tool()
def viewAllRequests() -> str:
    """This operation lets you to view the details of all the requests."""
    return json.dumps({
        "requests": list(_requests.values()),
        "response_status": [{"status_code": 2000, "status": "success"}],
        "list_info": {"row_count": len(_requests), "has_more_rows": False},
    })


@mcp.tool()
def viewAllPriorities() -> str:
    """This operation fetches all priorities."""
    return json.dumps({"priorities": PRIORITIES, "response_status": [{"status_code": 2000, "status": "success"}]})


@mcp.tool()
def viewAllStatuses() -> str:
    """This operation fetches all statuses available in the application."""
    return json.dumps({"statuses": STATUSES, "response_status": [{"status_code": 2000, "status": "success"}]})


@mcp.tool()
def viewAllCategories() -> str:
    """This operation fetches details of all categories."""
    return json.dumps({"categories": CATEGORIES, "response_status": [{"status_code": 2000, "status": "success"}]})


@mcp.tool()
def viewAllSupportGroups() -> str:
    """This operation fetches all support groups."""
    return json.dumps({"support_groups": SUPPORT_GROUPS, "response_status": [{"status_code": 2000, "status": "success"}]})


@mcp.tool()
def viewAllUrgencies() -> str:
    """This operation fetches all urgencies."""
    return json.dumps({"urgencies": URGENCIES, "response_status": [{"status_code": 2000, "status": "success"}]})


@mcp.tool()
def viewAllImpacts() -> str:
    """This operation fetches all impacts."""
    return json.dumps({"impacts": IMPACTS, "response_status": [{"status_code": 2000, "status": "success"}]})


@mcp.tool()
def viewAllModes() -> str:
    """This operation fetches all modes."""
    return json.dumps({"modes": MODES, "response_status": [{"status_code": 2000, "status": "success"}]})


@mcp.tool()
def viewAllSolutions() -> str:
    """This operation helps you view all the existing solutions in the application."""
    return json.dumps({"solutions": SOLUTIONS, "response_status": [{"status_code": 2000, "status": "success"}]})


@mcp.tool()
def getServiceTemplates() -> str:
    """This operation lets you get the list of all service templates in the application."""
    return json.dumps({"service_templates": SERVICE_TEMPLATES, "response_status": [{"status_code": 2000, "status": "success"}]})


@mcp.tool()
def getUserDetails() -> str:
    """Get all users"""
    return json.dumps({"users": USERS, "response_status": [{"status_code": 2000, "status": "success"}]})


@mcp.tool()
def viewAllRequestFilters() -> str:
    """This operation lets you to view all the request filters."""
    return json.dumps({"filters": REQUEST_FILTERS, "response_status": [{"status_code": 2000, "status": "success"}]})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
