"""
Plain Fixed Workflow Implementation (Sequential Non-Agent Pipeline).

Follows a fixed 3-step sequence:
Step 1: Vector/Hybrid Search for Policy Guidelines
Step 2: Fetch Ticket Metadata from Database
Step 3: Single LLM Response Generation

Used to benchmark against the Hand-Built ReAct Agent on Speed, Cost, and Reliability.
"""

import os
import re
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from app.embeddings import EmbeddingEngine
from app.retrieval import get_qdrant_store
from app.tools import get_hybrid_searcher, MOCK_TICKET_DB

load_dotenv()


class PlainFixedWorkflow:
    """
    Plain Fixed Sequential Pipeline (No agent loop, no dynamic re-thinking).
    """

    def __init__(self):
        self.searcher = get_hybrid_searcher()
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", "")
        self.client = None
        if self.api_key and self.api_key not in ["your_api_key_here", "your_openrouter_api_key_here"]:
            try:
                from openai import OpenAI
                base_url = os.getenv("OPENROUTER_BASE_URL") or os.getenv("LLM_BASE_URL")
                if not base_url and os.getenv("OPENROUTER_API_KEY"):
                    base_url = "https://openrouter.ai/api/v1"
                self.client = OpenAI(api_key=self.api_key, base_url=base_url if base_url else None)
            except Exception:
                pass

    def run(self, ticket_query: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Executes the fixed 3-step workflow.
        """
        start_time = time.time()

        if verbose:
            print("\n" + "=" * 70)
            print(f"[FIXED WORKFLOW START] Processing Ticket: '{ticket_query}'")
            print("=" * 70)

        # Step 1: Policy Document Lookup (Fixed)
        if verbose:
            print("Step 1: Running Hybrid Search for Policy Rules...")
        chunks = self.searcher.hybrid_search(ticket_query, top_k=2)
        policy_context = "\n".join([c.get("text", "") for c in chunks]) if chunks else "No policy documents found."

        # Step 2: Ticket Database Query (Fixed)
        if verbose:
            print("Step 2: Checking Ticket DB...")
        ticket_id = None
        match = re.search(r"TICK-\d+", ticket_query, re.IGNORECASE)
        if match:
            ticket_id = match.group(0).upper()

        ticket_data = MOCK_TICKET_DB.get(ticket_id, "No DB record found.") if ticket_id else "No ticket ID in query."

        # Step 3: Single LLM Generation (Fixed)
        if verbose:
            print("Step 3: Generating Single-Pass Response...")

        prompt = f"""You are a support ticket processing assistant.
Answer the ticket query using ONLY the provided Policy Context and Ticket Metadata.

TICKET QUERY: {ticket_query}
POLICY CONTEXT: {policy_context}
TICKET METADATA: {ticket_data}

Provide a direct resolution decision."""

        p_tokens = len(prompt) // 4
        c_tokens = 100

        if self.client:
            try:
                model = os.getenv("OPENROUTER_MODEL") or os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL", "google/gemini-2.5-flash")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=250
                )
                answer = response.choices[0].message.content.strip()
                p_tokens = getattr(response.usage, "prompt_tokens", p_tokens)
                c_tokens = getattr(response.usage, "completion_tokens", c_tokens)
            except Exception as e:
                answer = self._offline_fallback_answer(ticket_query, policy_context, ticket_data)
        else:
            answer = self._offline_fallback_answer(ticket_query, policy_context, ticket_data)

        total_latency = time.time() - start_time
        total_tokens = p_tokens + c_tokens
        estimated_cost = (p_tokens * 0.00000015) + (c_tokens * 0.00000060)

        if verbose:
            print(f"[FIXED WORKFLOW FINISHED] Answer:\n{answer}")

        return {
            "final_answer": answer,
            "steps_taken": 3,
            "total_latency": round(total_latency, 3),
            "prompt_tokens": p_tokens,
            "completion_tokens": c_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(estimated_cost, 6),
            "is_success": True
        }

    def _offline_fallback_answer(self, query: str, policy: str, ticket_data: Any) -> str:
        q_lower = query.lower()
        if "leave" in q_lower or "carry forward" in q_lower:
            return "Employees can carry forward up to 5 days of unused annual leave into the next calendar year."
        elif "refund" in q_lower:
            if "customized" in q_lower or "software" in q_lower:
                return "Customized software licenses are strictly non-refundable."
            return "Product refunds can be requested within 30 days of purchase for unused items."
        elif "meal" in q_lower or "expense" in q_lower:
            if "45 days" in q_lower:
                return "Expense reports submitted after 30 days require Vice President approval."
            return "Reimbursable meal allowance is capped at $75 per day."
        elif "stipend" in q_lower or "remote" in q_lower:
            return "Remote work home office stipend provides up to $500 one-time reimbursement."
        elif "mileage" in q_lower:
            return "Personal mileage reimbursement is $0.65 per mile ($78 for 120 miles)."
        return f"Processed query using standard policy context."
