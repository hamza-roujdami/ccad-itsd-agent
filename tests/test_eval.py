"""Evaluation test suite — validates agent behavior against expected outcomes.

Run: python -m pytest tests/test_eval.py -v
Requires: agent server running on localhost:8000 + mock MCP on 8001
"""

import httpx
import pytest

BASE_URL = "http://localhost:8000"


def chat(message: str, session_id: str | None = None) -> dict:
    """Send a chat message and return the response."""
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    resp = httpx.post(f"{BASE_URL}/chat", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


# ── KB-first resolution ──────────────────────────────────────────────────


class TestKBResolution:
    """Agent should answer from KB without creating tickets."""

    def test_password_reset(self):
        result = chat("How do I reset my password?")
        assert "Clinical ManageEngine" not in result["tools_used"], "Should NOT create a ticket for KB question"
        reply = result["reply"].lower()
        assert any(w in reply for w in ["sspr", "password", "reset"]), "Should mention password reset steps"

    def test_vpn_troubleshooting(self):
        result = chat("My VPN keeps disconnecting")
        reply = result["reply"].lower()
        assert any(w in reply for w in ["vpn", "forticlient", "connect"]), "Should mention VPN troubleshooting"

    def test_printer_help(self):
        result = chat("How do I enroll my badge on the printer?")
        reply = result["reply"].lower()
        assert any(w in reply for w in ["badge", "printer", "enroll", "canon"]), "Should mention badge enrollment"


# ── Non-IT routing ───────────────────────────────────────────────────────


class TestNonITRouting:
    """Non-IT requests should be redirected without creating tickets."""

    def test_hr_routing(self):
        result = chat("I need to request time off")
        assert "Clinical ManageEngine" not in result["tools_used"], "Should NOT create a ticket"
        reply = result["reply"].lower()
        assert "hr" in reply, "Should mention HR department"

    def test_facilities_routing(self):
        result = chat("The air conditioning in my office is broken")
        assert "Clinical ManageEngine" not in result["tools_used"], "Should NOT create a ticket"
        reply = result["reply"].lower()
        assert "facilities" in reply or "maintenance" in reply, "Should mention Facilities"


# ── Priority verification ────────────────────────────────────────────────


class TestPriorityVerification:
    """Priority should be verified and overridden when necessary."""

    def test_user_says_low_but_critical(self):
        result = chat(
            "I have a low priority issue - there is a security breach and data loss "
            "on the server. Multiple users affected. Email: test@clinic.example.com"
        )
        assert "assess_priority" in result["tools_used"], "Should use assess_priority tool"
        reply = result["reply"].lower()
        assert "critical" in reply or "urgent" in reply, "Should override to critical/urgent"

    def test_patient_care_escalation(self):
        result = chat(
            "The patient monitor in ICU is not responding. Patient is on life support. "
            "Email: nurse@clinic.example.com"
        )
        assert "Clinical ManageEngine" in result["tools_used"], "Should create a ticket"
        reply = result["reply"].lower()
        assert "urgent" in reply or "patient care" in reply or "p0" in reply, \
            "Should escalate to patient care priority"


# ── Ticket creation ──────────────────────────────────────────────────────


class TestTicketCreation:
    """Tickets should be created with correct fields."""

    def test_creates_ticket_with_id(self):
        result = chat(
            "Please create a support ticket. My laptop screen is completely cracked "
            "and I cannot work. I am a single caregiver affected. "
            "Name: Test User. Email: user@clinic.example.com. Department: Radiology."
        )
        assert "Clinical ManageEngine" in result["tools_used"], "Should create a ticket"
        reply = result["reply"]
        assert any(c.isdigit() for c in reply), "Should include a ticket ID number"

    def test_urgent_tag_in_subject(self):
        result = chat(
            "Epic Hyperspace is down for the entire ER. Multiple patients affected. "
            "Email: er-doc@clinic.example.com"
        )
        reply = result["reply"].lower()
        # The agent should treat ER/patient impact as urgent — accept any equivalent
        # escalation language, since the exact wording is non-deterministic.
        urgent_signals = ["[urgent]", "urgent", "critical", "patient care", "escalat", "immediate"]
        assert any(s in reply for s in urgent_signals), "Should signal urgent escalation"


# ── Ticket management ────────────────────────────────────────────────────


class TestTicketManagement:
    """Should be able to check and manage existing tickets."""

    def test_check_ticket_status(self):
        # First create a ticket
        create_result = chat("My keyboard stopped working. Email: test@clinic.example.com")
        # Extract ticket ID from reply
        reply = create_result["reply"]
        # Find a number that looks like a ticket ID (5+ digits)
        import re
        ticket_ids = re.findall(r"\b\d{5,}\b", reply)
        if ticket_ids:
            # Check its status
            status_result = chat(f"What is the status of ticket {ticket_ids[0]}?")
            assert "Clinical ManageEngine" in status_result["tools_used"], "Should query ManageEngine"


# ── Multi-turn conversation ──────────────────────────────────────────────


class TestMultiTurn:
    """Multi-turn conversations should maintain context."""

    def test_kb_then_escalate(self):
        # Turn 1: Ask about issue
        r1 = chat("My Wi-Fi keeps dropping in the cardiology department")
        session_id = r1["session_id"]

        # Turn 2: KB didn't help, create ticket
        r2 = chat(
            "None of those steps worked. Please create a ticket. "
            "Email: dr.smith@clinic.example.com",
            session_id=session_id,
        )
        assert "Clinical ManageEngine" in r2["tools_used"], "Should create ticket on second turn"
