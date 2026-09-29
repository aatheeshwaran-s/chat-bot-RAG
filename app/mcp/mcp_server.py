"""
Week 9: MCP Server Implementation for Track A (Customer Support Tickets & Ticket History).

Exposes app tools as a standardized Model Context Protocol (MCP) server using FastMCP.
Features:
- Dynamic Tool Schema Exposure (JSON-RPC)
- Access Control / Auth Verification on sensitive tools (escalate_ticket)
- Recoverable Error Handling
- Support for stdio and HTTP/SSE transports
"""

import json
from typing import Dict, Any, Optional
from fastmcp import FastMCP
import ast
from app.agents.tools import MOCK_TICKET_DB, safe_eval

# Initialize FastMCP Server
mcp_server = FastMCP(
    name="TicketHistoryService",
    instructions="MCP Server exposing Customer Support Ticket DB, Customer Resolution History, Math Evaluation, and Ticket Escalation."
)


@mcp_server.tool(
    name="check_ticket_db_mcp",
    description="Look up customer or employee support ticket details from the database by ticket ID (e.g. TICK-101)."
)
def check_ticket_db_mcp(ticket_id: str) -> str:
    """
    Retrieves ticket details. Returns recoverable JSON error if ticket is missing.
    """
    clean_id = ticket_id.strip().upper()
    if clean_id in MOCK_TICKET_DB:
        return json.dumps({
            "status": "success",
            "ticket": MOCK_TICKET_DB[clean_id]
        })
    else:
        # Recoverable Error Handling: Return descriptive error string instead of crashing
        return json.dumps({
            "status": "error",
            "message": f"Recoverable MCP Error: Ticket ID '{ticket_id}' was not found in the database. Please verify the ID."
        })


@mcp_server.tool(
    name="get_customer_history_mcp",
    description="Retrieve past ticket resolution history for a specific customer or employee name."
)
def get_customer_history_mcp(name: str) -> str:
    """
    Searches historical resolutions for a customer or employee.
    """
    query_name = name.strip().lower()
    matches = []
    for tid, data in MOCK_TICKET_DB.items():
        c_name = data.get("customer_name", "").lower()
        e_name = data.get("employee_name", "").lower()
        if query_name in c_name or query_name in e_name:
            matches.append(data)
    
    if matches:
        return json.dumps({
            "status": "success",
            "count": len(matches),
            "history": matches
        })
    return json.dumps({
        "status": "success",
        "count": 0,
        "history": [],
        "message": f"No previous support history found for '{name}'."
    })


@mcp_server.tool(
    name="calculate_reimbursement_mcp",
    description="Safely evaluate mathematical expressions for financial reimbursements or refund totals over MCP."
)
def calculate_reimbursement_mcp(expression: str) -> str:
    """
    Evaluates safe math expressions using AST evaluation.
    """
    clean_expr = expression.replace("$", "").replace(",", "").strip()
    try:
        tree = ast.parse(clean_expr, mode='eval')
        res = safe_eval(tree.body)
        return json.dumps({
            "status": "success",
            "result": str(res)
        })
    except Exception as err:
        return json.dumps({
            "status": "error",
            "message": f"Recoverable MCP Math Error: {err}"
        })


@mcp_server.tool(
    name="escalate_ticket_mcp",
    description="Escalate a policy exception or high-value refund ticket to human managerial review. REQUIRES auth_token='admin-secret'."
)
def escalate_ticket_mcp(ticket_id: str, reason: str, auth_token: str = "") -> str:
    """
    Escalates ticket to manager. Enforces Security / Access Control check on auth_token.
    """
    # Security / Access Control Check
    if auth_token != "admin-secret":
        return json.dumps({
            "status": "security_denied",
            "message": f"Access Control Error: Unauthorized attempt to escalate ticket '{ticket_id}'. Required valid auth_token."
        })
    
    clean_id = ticket_id.strip().upper()
    if clean_id in MOCK_TICKET_DB:
        MOCK_TICKET_DB[clean_id]["status"] = "ESCALATED"
    
    return json.dumps({
        "status": "success",
        "escalated_ticket_id": clean_id,
        "reason": reason,
        "escalation_ref": f"ESC-MCP-{clean_id}"
    })


if __name__ == "__main__":
    print("[MCP Server] Starting TicketHistoryService on stdio transport...")
    mcp_server.run()
