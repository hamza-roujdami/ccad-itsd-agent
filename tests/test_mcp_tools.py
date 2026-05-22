"""Test ALL ManageEngine MCP tools — verifies connectivity and tool responses.

Usage (against mock):
    python -m pytest tests/test_mcp_tools.py -v

Usage (against real APIM):
    python tests/test_mcp_tools.py --key YOUR_KEY
    python tests/test_mcp_tools.py --key YOUR_KEY --tool getServiceTemplates
    python tests/test_mcp_tools.py --key YOUR_KEY --save mcp_results.json

Reads from .env:
    MANAGE_ENGINE_MCP_URL=https://apim-uaen-uatai-001.azure-api.net/manage-engine-mcp/mcp
    APIM_SUBSCRIPTION_KEY=your-key
"""

import json
import os
import sys

import httpx
import pytest

# ── Pytest tests (against local mock on :8001) ──────────────────────────

MOCK_URL = "http://localhost:8001/mcp"

SAFE_TOOLS = [
    "viewAllPriorities",
    "viewAllStatuses",
    "viewAllCategories",
    "viewAllSupportGroups",
    "viewAllUrgencies",
    "viewAllImpacts",
    "viewAllModes",
    "viewAllSolutions",
    "viewAllRequestFilters",
    "getServiceTemplates",
    "getUserDetails",
]


class MCPClient:
    """Simple MCP JSON-RPC client."""

    def __init__(self, url: str, headers: dict | None = None):
        self.url = url
        self.headers = {"Content-Type": "application/json", **(headers or {})}
        self.session_id = None
        self.client = httpx.Client(timeout=30)
        self._call_id = 0

    def _next_id(self):
        self._call_id += 1
        return self._call_id

    def initialize(self):
        resp = self.client.post(self.url, json={
            "jsonrpc": "2.0", "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"},
            },
        }, headers=self.headers)
        self.session_id = resp.headers.get("mcp-session-id")
        return resp.json()

    def call_tool(self, name: str, arguments: dict | None = None):
        h = {**self.headers}
        if self.session_id:
            h["mcp-session-id"] = self.session_id
        resp = self.client.post(self.url, json={
            "jsonrpc": "2.0", "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }, headers=h)
        body = resp.json()
        if "error" in body:
            return None
        content = body.get("result", {}).get("content", [])
        if content:
            try:
                return json.loads(content[0].get("text", "{}"))
            except json.JSONDecodeError:
                return content[0].get("text")
        return body.get("result")

    def close(self):
        self.client.close()


@pytest.fixture(scope="module")
def mcp():
    client = MCPClient(MOCK_URL)
    client.initialize()
    yield client
    client.close()


@pytest.mark.parametrize("tool_name", SAFE_TOOLS)
def test_read_only_tool(mcp, tool_name):
    """Each read-only MCP tool should return a successful response."""
    result = mcp.call_tool(tool_name)
    assert result is not None, f"{tool_name} returned None"
    assert isinstance(result, dict), f"{tool_name} should return a dict"


def test_create_and_get_request(mcp):
    """Create a ticket and verify it can be retrieved."""
    result = mcp.call_tool("createRequest", {
        "subject": "Test ticket from MCP tools test",
        "description": "Automated test — safe to delete",
        "requester_email": "test@clinic.example.com",
        "mode": "E-Mail",
        "group": "SERVICE DESK",
        "category": "Software",
    })
    assert result is not None
    ticket_id = result.get("request", {}).get("id")
    assert ticket_id, "Should return a ticket ID"

    # Get the ticket back
    details = mcp.call_tool("requestDetailsById", {"request_id": ticket_id})
    assert details is not None
    assert details.get("request", {}).get("id") == ticket_id


def test_add_note(mcp):
    """Create a ticket and add a note to it."""
    result = mcp.call_tool("createRequest", {
        "subject": "Note test ticket",
        "requester_email": "test@clinic.example.com",
        "mode": "E-Mail",
        "group": "SERVICE DESK",
    })
    ticket_id = result.get("request", {}).get("id")

    note_result = mcp.call_tool("addNote", {
        "request_id": ticket_id,
        "AddnotesPostRequest-1": {
            "input_data": json.dumps({
                "request_note": {"description": "Test note", "show_to_requester": True}
            })
        },
    })
    assert note_result is not None
    assert note_result.get("response_status", {}).get("status") == "success"


# ── CLI mode (against real APIM) ────────────────────────────────────────

def cli_main():
    """Run against real MCP endpoint with APIM key."""
    import argparse
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="Test ManageEngine MCP tools")
    parser.add_argument("--url", default=os.getenv("MANAGE_ENGINE_MCP_URL",
        "https://apim-uaen-uatai-001.azure-api.net/manage-engine-mcp/mcp"))
    parser.add_argument("--key", default=os.getenv("APIM_SUBSCRIPTION_KEY", ""))
    parser.add_argument("--tool", help="Test a single tool")
    parser.add_argument("--save", help="Save results to JSON file")
    args = parser.parse_args()

    if not args.key:
        print("ERROR: No APIM key. Use --key or set APIM_SUBSCRIPTION_KEY in .env")
        sys.exit(1)

    client = MCPClient(args.url, {"Ocp-Apim-Subscription-Key": args.key})

    print("Initializing MCP session...")
    init = client.initialize()
    print(f"  Session: {client.session_id}")

    tools_to_test = [args.tool] if args.tool else SAFE_TOOLS
    results = {}

    for tool_name in tools_to_test:
        print(f"  {tool_name} ... ", end="", flush=True)
        result = client.call_tool(tool_name)
        if result:
            print("OK")
            if isinstance(result, dict):
                for k, v in result.items():
                    if isinstance(v, list):
                        print(f"    {k}: {len(v)} items")
            results[tool_name] = {"status": "ok", "data": result}
        else:
            print("FAILED")
            results[tool_name] = {"status": "failed"}

    ok = sum(1 for r in results.values() if r["status"] == "ok")
    print(f"\nResult: {ok}/{len(results)} passed")

    if args.save:
        with open(args.save, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Saved to {args.save}")

    client.close()


if __name__ == "__main__":
    cli_main()
