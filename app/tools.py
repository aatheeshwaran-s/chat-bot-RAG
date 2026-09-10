"""
Tool Definitions & Tool Registry for Hand-Built ReAct Agent.

Provides clear, explicit tools with detailed descriptions for:
1. Hybrid Vector + BM25 Policy Document Search (`lookup_policy`)
2. Ticket Metadata DB Query (`check_ticket_db`)
3. Financial / Math Calculation (`calculate_amount`)
4. Exception Escalation (`escalate_ticket`)
5. Final Answer Resolution (`final_answer`)
"""

import ast
import operator
import re
from typing import Dict, Any, List, Callable, Optional
from app.embeddings import EmbeddingEngine
from app.retrieval import get_qdrant_store
from app.hybrid import HybridSearchEngine
from app.ingest import process_all_documents_in_folder
import os


_GLOBAL_SEARCHER = None

def get_hybrid_searcher() -> HybridSearchEngine:
    global _GLOBAL_SEARCHER
    if _GLOBAL_SEARCHER is None:
        store = get_qdrant_store()
        engine = EmbeddingEngine()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docs_folder = os.path.join(base_dir, "documents")
        all_chunks = process_all_documents_in_folder(docs_folder, chunk_size=500, chunk_overlap=50, verbose=False)
        _GLOBAL_SEARCHER = HybridSearchEngine(store, engine, all_chunks)
    return _GLOBAL_SEARCHER


# ----------------------------------------------------
# Mock Ticket Database for Customer & HR Support
# ----------------------------------------------------
MOCK_TICKET_DB: Dict[str, Dict[str, Any]] = {
    "TICK-101": {
        "ticket_id": "TICK-101",
        "customer_name": "Alice",
        "order_id": "ORD-501",
        "product_type": "Standard Physical Product",
        "purchase_days_ago": 12,
        "amount": 120.0,
        "condition": "Unused in original packaging",
        "status": "OPEN"
    },
    "TICK-102": {
        "ticket_id": "TICK-102",
        "customer_name": "Bob",
        "order_id": "ORD-502",
        "product_type": "Customized Software License",
        "purchase_days_ago": 10,
        "amount": 250.0,
        "condition": "Downloaded",
        "status": "OPEN"
    },
    "TICK-103": {
        "ticket_id": "TICK-103",
        "employee_name": "Charlie",
        "expense_type": "Business Travel Meals",
        "days_submitted_after_trip": 5,
        "daily_expenses": [85.0, 60.0],
        "receipts_attached": True,
        "status": "OPEN"
    },
    "TICK-104": {
        "ticket_id": "TICK-104",
        "employee_name": "David",
        "expense_type": "Business Travel Flight",
        "days_submitted_after_trip": 45,
        "amount": 420.0,
        "receipts_attached": True,
        "status": "OPEN"
    },
    "TICK-107": {
        "ticket_id": "TICK-107",
        "employee_name": "Grace",
        "expense_type": "Home Office Equipment",
        "items": ["Ergonomic Chair", "4K Monitor"],
        "requested_amount": 650.0,
        "status": "OPEN"
    },
    "TICK-109": {
        "ticket_id": "TICK-109",
        "employee_name": "Henry",
        "expense_type": "Personal Mileage Reimbursement",
        "miles_driven": 120,
        "status": "OPEN"
    },
    "TICK-110": {
        "ticket_id": "TICK-110",
        "customer_name": "Iris",
        "order_id": "ORD-503",
        "product_type": "Standard Physical Product",
        "purchase_days_ago": 45,
        "amount": 90.0,
        "status": "OPEN"
    }
}


# ----------------------------------------------------
# Safe Math Expression Evaluator
# ----------------------------------------------------
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos
}

def safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        op_type = type(node.op)
        if op_type in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported math operator: {op_type}")
    elif isinstance(node, ast.UnaryOp):
        operand = safe_eval(node.operand)
        op_type = type(node.op)
        if op_type in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type}")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in ("min", "max", "round", "abs"):
            args = [safe_eval(arg) for arg in node.args]
            func_map = {"min": min, "max": max, "round": round, "abs": abs}
            return func_map[node.func.id](*args)
        raise ValueError(f"Unsupported function call in math expression: {node.func}")
    else:
        raise ValueError(f"Invalid math expression node: {type(node)}")


# ----------------------------------------------------
# Concrete Tool Definitions
# ----------------------------------------------------
class Tool:
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def run(self, **kwargs) -> str:
        try:
            return str(self.func(**kwargs))
        except Exception as e:
            return f"Error executing tool '{self.name}': {str(e)}"


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._init_default_tools()

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def format_tools_for_prompt(self) -> str:
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(f"- Tool: `{name}`\n  Description: {tool.description}")
        return "\n\n".join(descriptions)

    def _init_default_tools(self):
        def lookup_policy_fn(query: str, department: Optional[str] = None) -> str:
            searcher = get_hybrid_searcher()
            chunks = searcher.hybrid_search(query, top_k=3)
            if not chunks:
                return "No matching policy guidelines found in documents."
            results = []
            for c in chunks:
                filename = c.get("filename", "Doc")
                page = c.get("page", 1)
                text = c.get("text", "")
                results.append(f"[{filename} Page {page}]: {text}")
            return "\n".join(results)

        def check_ticket_db_fn(ticket_id: str) -> str:
            ticket_id = ticket_id.strip().upper()
            if ticket_id in MOCK_TICKET_DB:
                data = MOCK_TICKET_DB[ticket_id]
                return f"Ticket {ticket_id} Details: {data}"
            for k, v in MOCK_TICKET_DB.items():
                if k in ticket_id or ticket_id in k:
                    return f"Ticket {k} Details: {v}"
            return f"No record found for Ticket ID '{ticket_id}' in Database."

        def calculate_amount_fn(expression: str) -> str:
            clean_expr = expression.replace("$", "").replace(",", "").strip()
            try:
                tree = ast.parse(clean_expr, mode='eval')
                result = safe_eval(tree.body)
                return f"Calculation Result: {result}"
            except Exception as err:
                return f"Error evaluating expression '{expression}': {err}"

        def escalate_ticket_fn(ticket_id: str, reason: str) -> str:
            return f"TICKET ESCALATED: Ticket '{ticket_id}' escalated to Vice President/Manager. Reason: {reason}"

        def final_answer_fn(resolution: str) -> str:
            return f"FINAL RESOLUTION: {resolution}"

        self.register(Tool(
            name="lookup_policy",
            description="Search official company policy documents (expense policy, leave policy, refund policy, remote work policy, employee handbook). Parameters: query (str).",
            func=lookup_policy_fn
        ))

        self.register(Tool(
            name="check_ticket_db",
            description="Lookup customer order date, product type, expense details, or days elapsed in ticket database. Parameters: ticket_id (str, e.g. 'TICK-101').",
            func=check_ticket_db_fn
        ))

        self.register(Tool(
            name="calculate_amount",
            description="Perform exact numerical calculation (e.g. meal allowance caps, mileage rate * miles, refund totals). Parameters: expression (str, e.g. 'min(85, 75) + 60').",
            func=calculate_amount_fn
        ))

        self.register(Tool(
            name="escalate_ticket",
            description="Escalate ticket for special VP or Manager approval when policy limits are exceeded or late. Parameters: ticket_id (str), reason (str).",
            func=escalate_ticket_fn
        ))

        self.register(Tool(
            name="final_answer",
            description="Output final decision and resolution to complete the ticket. Parameters: resolution (str).",
            func=final_answer_fn
        ))
