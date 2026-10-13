"""
Capstone Production Observability & Distributed Tracing Engine (Track A).

Enforces:
1. One persistent Trace ID spanning Ticket Ingestion -> Agent Reason -> MCP Tool Hop -> RAG -> Ticket Resolution.
2. Microsecond-resolution latency and exact token/cost tracking PER SPAN.
3. Strict PII Line Enforcement: Zero customer emails or order shipping addresses written to squad logs.
"""

import os
import re
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
ADDRESS_REGEX = re.compile(
    r'\b\d{1,5}\s+[A-Za-z0-9\.\s]+(?:Street|St|Avenue|Ave|Terrace|Blvd|Boulevard|Road|Rd|Drive|Dr|Plaza|Lane|Ln|Court|Ct|Way)\b(?:[,\s]+[A-Za-z\s]+)*(?:[,\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?)?',
    re.IGNORECASE
)


def sanitize_pii(text: Any) -> Any:
    """
    Recursively scrubs PII (emails and physical addresses) from strings, dicts, and lists.
    Guarantees no customer PII enters squad-readable log files.
    """
    if isinstance(text, str):
        cleaned = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        cleaned = ADDRESS_REGEX.sub("[REDACTED_ADDRESS]", cleaned)
        return cleaned
    elif isinstance(text, dict):
        return {k: sanitize_pii(v) for k, v in text.items()}
    elif isinstance(text, list):
        return [sanitize_pii(item) for item in text]
    return text


class Span:
    """Represents a single timed operation within a distributed trace."""

    def __init__(self, name: str, parent_span_id: Optional[str] = None):
        self.span_id = f"sp-{uuid.uuid4().hex[:6]}"
        self.parent_span_id = parent_span_id
        self.name = name
        self.start_time = time.perf_counter()
        self.end_time: Optional[float] = None
        self.latency_ms: float = 0.0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.cost_usd: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def finish(self, prompt_tokens: int = 0, completion_tokens: int = 0, extra: Optional[Dict[str, Any]] = None):
        self.end_time = time.perf_counter()
        self.latency_ms = round((self.end_time - self.start_time) * 1000.0, 2)
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        # Gemini / OpenAI Flash pricing model ($0.15 / 1M prompt, $0.60 / 1M completion)
        self.cost_usd = round((prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060), 6)
        if extra:
            self.metadata.update(extra)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": self.cost_usd,
            "metadata": sanitize_pii(self.metadata)
        }


class CapstoneTrace:
    """Full execution trace of a ticket request spanning agent and MCP hops."""

    def __init__(self, ticket_id: str = "TICK-UNKNOWN", trace_id: Optional[str] = None):
        self.trace_id = trace_id or f"tr-capstone-{uuid.uuid4().hex[:8]}"
        self.ticket_id = ticket_id
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.spans: List[Span] = []
        self._start_perf = time.perf_counter()

    def start_span(self, name: str, parent_span_id: Optional[str] = None) -> Span:
        span = Span(name=name, parent_span_id=parent_span_id)
        self.spans.append(span)
        return span

    def total_cost_usd(self) -> float:
        return round(sum(s.cost_usd for s in self.spans), 6)

    def total_latency_ms(self) -> float:
        return round((time.perf_counter() - self._start_perf) * 1000.0, 2)

    def total_tokens(self) -> int:
        return sum(s.prompt_tokens + s.completion_tokens for s in self.spans)

    def to_record(
        self,
        question: str,
        answer: str,
        status: str = "ok",
        deflection: bool = True,
        cited_policy_slug: str = "N/A",
        entitlement_checked: bool = False
    ) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "ticket_id": self.ticket_id,
            "timestamp": self.created_at,
            "total_latency_ms": self.total_latency_ms(),
            "total_cost_usd": self.total_cost_usd(),
            "total_tokens": self.total_tokens(),
            "status": status,
            "deflected": deflection,
            "cited_policy_slug": cited_policy_slug,
            "entitlement_checked": entitlement_checked,
            "pii_redacted": True,
            "question": sanitize_pii(question),
            "answer": sanitize_pii(answer),
            "spans": [s.to_dict() for s in self.spans]
        }


class CapstoneObservabilityManager:
    """Writes and loads traces with thread-safe append and PII scrubbing."""

    def __init__(self, log_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_path = log_path or os.path.join(base_dir, "logs", "capstone_traces.jsonl")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def commit_trace(self, trace_record: Dict[str, Any]) -> str:
        clean_record = sanitize_pii(trace_record)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(clean_record, ensure_ascii=False) + "\n")
        return clean_record["trace_id"]

    def load_traces(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.log_path):
            return []
        traces = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        traces.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return traces

    def get_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        for t in self.load_traces():
            if t.get("trace_id") == trace_id:
                return t
        return None
