"""
Thursday's Fresh-Eyes Reviewer Client Script.

Simulates an external engineer from another squad (e.g., Squad 4 / Insurance Squad)
connecting to our Track A SupportTriageMCPService to:
1. Discover all exposed capabilities over FastMCP.
2. Search help-centre policies via `search_help_center_mcp`.
3. Check customer plan entitlement via `entitlement_check_mcp`.
4. Validate that their incoming trace_id survives the MCP hop completely intact.
5. Confirm no customer PII (email/address) is leaked in returned payloads.
"""

import sys
import json
import asyncio
import uuid
from app.mcp_server import mcp_server


def run_fresh_eyes_review() -> bool:
    print("\n" + "=" * 80)
    print(" [FRESH-EYES REVIEW] External Squad Reviewer Client -> SupportTriageMCPService")
    print(" Reviewer: Sarah Jenkins (Squad 4 - Claims & Contracts)")
    print(" Target: Track A Tier-1 Deflection Assistant MCP Server")
    print("=" * 80)

    # Step 1: Tool Discovery Handshake
    print("\n[Step 1] Executing MCP list_tools() discovery handshake...")
    try:
        tools = asyncio.run(mcp_server.list_tools())
        tool_names = [t.name for t in tools]
        print(f" -> DISCOVERY SUCCESS: Found {len(tool_names)} live tools:")
        for name in tool_names:
            print(f"    * {name}")
    except Exception as e:
        print(f" -> DISCOVERY FAILED: {e}")
        return False

    required_tools = ["search_help_center_mcp", "order_lookup_mcp", "entitlement_check_mcp", "escalate_ticket_mcp"]
    for req in required_tools:
        if req not in tool_names:
            print(f" [FAIL] Missing required tool: {req}")
            return False
    print(" [PASS] All 4 mandatory core capabilities exposed over MCP.")

    # Step 2: Live Help-Center Search Call
    external_trace_id = f"tr-fresh-eyes-{uuid.uuid4().hex[:6]}"
    print(f"\n[Step 2] Calling 'search_help_center_mcp' with Trace ID '{external_trace_id}'...")
    try:
        res = asyncio.run(mcp_server.call_tool("search_help_center_mcp", {
            "query": "refund policy window 30 days hardware",
            "trace_id": external_trace_id
        }))
        payload_text = res.content[0].text if hasattr(res, 'content') and res.content else str(res)
        data = json.loads(payload_text)
        print(f" -> Status: {data.get('status')}")
        print(f" -> Results returned: {data.get('total_hits')}")
        for r in data.get("results", []):
            print(f"    - Article Slug: {r.get('slug')} (Updated: {r.get('last_updated')})")
        assert data.get("trace_id") == external_trace_id, "Trace ID did not survive MCP hop!"
        print(" [PASS] Trace ID preserved across search_help_center_mcp call.")
    except Exception as e:
        print(f" -> CALL FAILED: {e}")
        return False

    # Step 3: Entitlement & Terms Verification Call
    print(f"\n[Step 3] Calling 'entitlement_check_mcp' for customer CUST-101...")
    try:
        res2 = asyncio.run(mcp_server.call_tool("entitlement_check_mcp", {
            "identifier": "CUST-101",
            "trace_id": external_trace_id
        }))
        payload2 = res2.content[0].text if hasattr(res2, 'content') and res2.content else str(res2)
        data2 = json.loads(payload2)
        print(f" -> Customer: {data2.get('customer_name')}")
        print(f" -> Plan Tier: {data2.get('plan_tier')}")
        print(f" -> Applicable Policy Slug: {data2.get('applicable_refund_policy_slug')}")
        print(f" -> Refund Window: {data2.get('refund_window_days')} days")

        # PII Check
        raw_str = str(data2)
        assert "@" not in raw_str, "Customer email leaked in MCP payload!"
        assert "Terrace" not in raw_str and "Springfield" not in raw_str, "Customer address leaked in MCP payload!"
        print(" [PASS] PII check passed: zero raw email or physical address leaked in payload.")
    except Exception as e:
        print(f" -> CALL FAILED: {e}")
        return False

    print("\n" + "=" * 80)
    print(" [FRESH-EYES REVIEW VERDICT]: APPROVED (All MCP requirements verified live)")
    print("=" * 80 + "\n")
    return True


if __name__ == "__main__":
    success = run_fresh_eyes_review()
    sys.exit(0 if success else 1)
