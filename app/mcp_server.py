"""
Week 12 Capstone: SupportTriageMCPService (Model Context Protocol Server for Track A).

Exposes core customer support capabilities over FastMCP:
1. `order_lookup_mcp`: Order status, purchase date, item type, return status.
2. `entitlement_check_mcp`: Customer plan, 30-day vs 14-day refund window, applicable policy slug.
3. `search_help_center_mcp`: Help-centre article search with exact slug and last-updated date.
4. `escalate_ticket_mcp`: Escalation to Tier-2 / Lead with reason and priority.
5. Backwards-compatible tools (`check_ticket_db_mcp`, `get_customer_history_mcp`, `calculate_reimbursement_mcp`).

All tools accept optional `trace_id` to ensure distributed trace correlation across the MCP hop.
"""

import os
import re
import json
import glob
import time
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from app.capstone_logger import sanitize_pii

# Initialize FastMCP Server
mcp_server = FastMCP(
    name="SupportTriageMCPService",
    instructions="MCP Server exposing Customer Support Database, Entitlements, Help-Center Search, and Ticket Escalation."
)

_CUSTOMER_DB_CACHE: Optional[Dict[str, Any]] = None
_HELP_CENTER_CACHE: Optional[List[Dict[str, Any]]] = None


def _load_customer_db() -> Dict[str, Any]:
    global _CUSTOMER_DB_CACHE
    if _CUSTOMER_DB_CACHE is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "data", "help_center", "customer_orders_entitlements.json")
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                _CUSTOMER_DB_CACHE = json.load(f).get("customers", {})
        else:
            _CUSTOMER_DB_CACHE = {}
    return _CUSTOMER_DB_CACHE


def _load_help_center_docs() -> List[Dict[str, Any]]:
    global _HELP_CENTER_CACHE
    if _HELP_CENTER_CACHE is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        hc_dir = os.path.join(base_dir, "data", "help_center")
        docs = []
        for md_path in glob.glob(os.path.join(hc_dir, "*.md")):
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Extract YAML frontmatter
            slug = os.path.basename(md_path).replace(".md", "")
            last_updated = "2026-01-01"
            title = slug
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = parts[1]
                    body = parts[2]
                    for line in fm.strip().split("\n"):
                        if line.startswith("article_slug:"):
                            slug = line.split(":", 1)[1].strip()
                        elif line.startswith("title:"):
                            title = line.split(":", 1)[1].strip()
                        elif line.startswith("last_updated:"):
                            last_updated = line.split(":", 1)[1].strip()
                    docs.append({
                        "slug": slug,
                        "title": title,
                        "last_updated": last_updated,
                        "body": body.strip(),
                        "path": md_path
                    })
                    continue
            docs.append({
                "slug": f"help-center/{slug}",
                "title": title,
                "last_updated": last_updated,
                "body": content.strip(),
                "path": md_path
            })
        _HELP_CENTER_CACHE = docs
    return _HELP_CENTER_CACHE


@mcp_server.tool(
    name="order_lookup_mcp",
    description="Look up customer order details (order_id, purchase date, item type, amount, return condition, tracking) from order database."
)
def order_lookup_mcp(order_id: str, trace_id: str = "") -> str:
    """Retrieves order details for a given Order ID or Ticket ID."""
    clean_id = order_id.strip().upper()
    db = _load_customer_db()
    for cust_id, cust in db.items():
        for order in cust.get("orders", []):
            if order.get("order_id") == clean_id or order.get("ticket_id") == clean_id or clean_id in order.get("order_id", ""):
                result = {
                    "status": "success",
                    "trace_id": trace_id,
                    "customer_id": cust_id,
                    "customer_name": cust.get("name"),
                    "order": order
                }
                return json.dumps(sanitize_pii(result))
    return json.dumps({
        "status": "error",
        "trace_id": trace_id,
        "message": f"Order or Ticket '{order_id}' was not found in Order Database."
    })


@mcp_server.tool(
    name="entitlement_check_mcp",
    description="Check customer plan entitlement, refund window (30 vs 14 days), account tier, and applicable refund policy slug BEFORE making claims."
)
def entitlement_check_mcp(identifier: str, trace_id: str = "") -> str:
    """Checks customer entitlement and applicable terms."""
    clean_id = identifier.strip().upper()
    db = _load_customer_db()

    target_cust = None
    for cust_id, cust in db.items():
        if cust_id == clean_id or clean_id in cust.get("name", "").upper():
            target_cust = cust
            break
        for order in cust.get("orders", []):
            if order.get("order_id") == clean_id or order.get("ticket_id") == clean_id:
                target_cust = cust
                break
        if target_cust:
            break

    if target_cust:
        result = {
            "status": "success",
            "trace_id": trace_id,
            "customer_id": target_cust.get("customer_id"),
            "customer_name": target_cust.get("name"),
            "plan_tier": target_cust.get("plan_tier"),
            "refund_window_days": target_cust.get("refund_window_days"),
            "applicable_refund_policy_slug": target_cust.get("applicable_refund_policy_slug"),
            "vip_status": target_cust.get("vip_status", False),
            "account_created_date": target_cust.get("account_created_date")
        }
        return json.dumps(sanitize_pii(result))

    # Default fallback for unknown accounts
    return json.dumps({
        "status": "success",
        "trace_id": trace_id,
        "customer_id": clean_id,
        "plan_tier": "STANDARD_CURRENT",
        "refund_window_days": 30,
        "applicable_refund_policy_slug": "help-center/refund-policy-current-30day",
        "vip_status": False,
        "note": "Standard retail customer terms applied by default."
    })


@mcp_server.tool(
    name="search_help_center_mcp",
    description="Search public help-centre documentation (refund policies, shipping SLA matrix, product changelog) returning exact article slugs and versions."
)
def search_help_center_mcp(query: str, trace_id: str = "") -> str:
    """Searches help centre articles and returns relevant sections with slugs and dates."""
    docs = _load_help_center_docs()
    q_words = set(re.findall(r'\w+', query.lower())) - {"the", "a", "an", "is", "for", "to", "in", "what"}

    scored_hits = []
    for d in docs:
        body_words = set(re.findall(r'\w+', d["body"].lower()))
        title_words = set(re.findall(r'\w+', d["title"].lower()))
        overlap = len(q_words.intersection(body_words)) + 2 * len(q_words.intersection(title_words))
        if overlap > 0:
            # Extract relevant paragraph
            paragraphs = [p.strip() for p in d["body"].split("\n\n") if p.strip()]
            best_snippet = paragraphs[0] if paragraphs else d["body"][:300]
            for p in paragraphs:
                p_set = set(re.findall(r'\w+', p.lower()))
                if len(q_words.intersection(p_set)) >= 2:
                    best_snippet = p
                    break
            scored_hits.append({
                "slug": d["slug"],
                "title": d["title"],
                "last_updated": d["last_updated"],
                "snippet": best_snippet,
                "score": overlap
            })

    scored_hits.sort(key=lambda x: x["score"], reverse=True)
    top_hits = scored_hits[:3] if scored_hits else []

    return json.dumps({
        "status": "success",
        "trace_id": trace_id,
        "query": query,
        "total_hits": len(top_hits),
        "results": top_hits
    })


@mcp_server.tool(
    name="escalate_ticket_mcp",
    description="Escalate a ticket to human Tier-2 Support Lead when ticket requires supervisor override, VIP review, or policy exception."
)
def escalate_ticket_mcp(ticket_id: str, reason: str, priority: str = "normal", trace_id: str = "") -> str:
    """Escalates ticket to Tier-2 supervisor."""
    clean_id = ticket_id.strip().upper()
    return json.dumps({
        "status": "success",
        "trace_id": trace_id,
        "escalated_ticket_id": clean_id,
        "priority": priority,
        "reason": reason,
        "assigned_queue": "Tier-2 Supervisor Escalations",
        "escalation_ref": f"ESC-TIER2-{clean_id}"
    })


# ----------------------------------------------------
# Backwards-Compatible Legacy Tools
# ----------------------------------------------------
from app.tools import MOCK_TICKET_DB, safe_eval
import ast

@mcp_server.tool(
    name="check_ticket_db_mcp",
    description="Look up customer or employee support ticket details from the database by ticket ID (e.g. TICK-101)."
)
def check_ticket_db_mcp(ticket_id: str) -> str:
    clean_id = ticket_id.strip().upper()
    if clean_id in MOCK_TICKET_DB:
        return json.dumps({
            "status": "success",
            "ticket": MOCK_TICKET_DB[clean_id]
        })
    return order_lookup_mcp(ticket_id)


@mcp_server.tool(
    name="get_customer_history_mcp",
    description="Retrieve past ticket resolution history for a specific customer or employee name."
)
def get_customer_history_mcp(name: str) -> str:
    query_name = name.strip().lower()
    matches = []
    for tid, data in MOCK_TICKET_DB.items():
        c_name = data.get("customer_name", "").lower()
        e_name = data.get("employee_name", "").lower()
        if query_name in c_name or query_name in e_name:
            matches.append(data)
    return json.dumps({
        "status": "success",
        "count": len(matches),
        "history": matches
    })


@mcp_server.tool(
    name="calculate_reimbursement_mcp",
    description="Safely evaluate mathematical expressions for financial reimbursements or refund totals over MCP."
)
def calculate_reimbursement_mcp(expression: str) -> str:
    clean_expr = expression.replace("$", "").replace(",", "").strip()
    try:
        tree = ast.parse(clean_expr, mode='eval')
        res = safe_eval(tree.body)
        return json.dumps({"status": "success", "result": str(res)})
    except Exception as err:
        return json.dumps({"status": "error", "message": f"Recoverable MCP Math Error: {err}"})


if __name__ == "__main__":
    print("[MCP Server] Starting SupportTriageMCPService on stdio transport...")
    mcp_server.run()
