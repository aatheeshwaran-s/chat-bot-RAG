import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


class RequestLogger:
    """Append-only request log for production observability and support drills."""

    def __init__(self, log_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_path = log_path or os.path.join(base_dir, "logs", "request_log.jsonl")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_request(
        self,
        question: str,
        mode: str,
        answer: str,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
        latency_sec: float = 0.0,
        estimated_cost_usd: float = 0.0,
        trace_id: Optional[str] = None,
        status: str = "ok",
        **extra: Any,
    ) -> Dict[str, Any]:
        entry = {
            "trace_id": trace_id or f"trace-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "mode": mode,
            "answer": answer,
            "retrieved_chunks": retrieved_chunks or [],
            "latency_sec": round(float(latency_sec), 3),
            "cost_usd": round(float(estimated_cost_usd), 6),
            "status": status,
            "metadata": extra,
        }

        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def load_requests(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.log_path):
            return []

        records: List[Dict[str, Any]] = []
        with open(self.log_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    def find_bad_answers(self, complaint: str, max_hits: int = 10) -> List[Dict[str, Any]]:
        complaint_terms = [term.lower() for term in complaint.split() if term]
        if not complaint_terms:
            complaint_terms = ["refund", "notice", "coverage", "deprecated", "termination"]

        matches: List[Dict[str, Any]] = []
        for record in self.load_requests():
            haystack = " ".join([
                record.get("question", ""),
                record.get("answer", ""),
                record.get("status", ""),
            ]).lower()
            if any(term in haystack for term in complaint_terms):
                score = sum(1 for term in complaint_terms if term in haystack)
                matches.append({**record, "match_score": score})

        matches.sort(key=lambda item: item.get("match_score", 0), reverse=True)
        return matches[:max_hits]


def run_week11_support_drill(logs: Optional[List[Dict[str, Any]]] = None, complaint: str = "") -> Dict[str, Any]:
    """Find one suspicious answer by scanning request logs for the complaint keywords."""
    if logs is None:
        logger = RequestLogger()
        logs = logger.load_requests()

    complaint = complaint.strip() or "refund after 14 days"
    terms = [term.lower() for term in complaint.split() if term]
    matches: List[Dict[str, Any]] = []

    for record in logs:
        haystack = " ".join([
            str(record.get("question", "")),
            str(record.get("answer", "")),
            str(record.get("status", "")),
        ]).lower()
        if any(term in haystack for term in terms):
            matches.append(record)

    return {
        "complaint": complaint,
        "bad_match_count": len(matches),
        "matches": matches,
    }


def run_week11_cost_reduction(
    baseline_cost_usd: float,
    optimized_cost_usd: float,
    requests: int = 100,
) -> Dict[str, Any]:
    """Compute cost-per-request before vs after a production optimization."""
    if requests <= 0:
        raise ValueError("requests must be greater than zero")

    avg_baseline = float(baseline_cost_usd) / float(requests)
    avg_optimized = float(optimized_cost_usd) / float(requests)
    savings = avg_baseline - avg_optimized
    savings_percent = ((savings / avg_baseline) * 100.0) if avg_baseline > 0 else 0.0

    return {
        "baseline_cost_usd": float(baseline_cost_usd),
        "optimized_cost_usd": float(optimized_cost_usd),
        "requests": int(requests),
        "avg_baseline_cost_usd": round(avg_baseline, 6),
        "avg_optimized_cost_usd": round(avg_optimized, 6),
        "absolute_savings_usd": round(savings, 6),
        "savings_percent": round(savings_percent, 2),
    }


def build_week11_regression_case() -> Dict[str, Any]:
    """Turn a real failure into a permanent guardrail test for future model regressions."""
    return {
        "name": "refund-policy-after-14-days-regression",
        "question": "Does the refund policy allow a refund after 14 days?",
        "expected_answer": "No. Refunds are only allowed within 14 days and if the item is unopened and in original packaging.",
        "bad_answer": "You may still get a refund after 14 days.",
        "test_guard": "Reject any answer that exceeds the 14-day refund window without mentioning the unopened condition.",
    }


def run_week11_production_suite(verbose: bool = True) -> Dict[str, Any]:
    """Demo production observability, cost reduction, and the failure-to-test loop."""
    logger = RequestLogger()

    sample_requests = [
        {
            "question": "Can I get a refund after 14 days?",
            "mode": "hybrid",
            "answer": "Refunds are only allowed within 14 days and only if the item is still unopened.",
            "retrieved_chunks": [{"filename": "refund_policy.pdf", "page": 2, "text": "Refunds allowed within 14 days only."}],
            "latency_sec": 1.34,
            "estimated_cost_usd": 0.0046,
            "status": "ok",
        },
        {
            "question": "Does the policy allow a refund after 14 days?",
            "mode": "hybrid",
            "answer": "You may still get a refund after 14 days.",
            "retrieved_chunks": [{"filename": "refund_policy.pdf", "page": 2, "text": "Refunds allowed within 14 days only."}],
            "latency_sec": 1.41,
            "estimated_cost_usd": 0.0049,
            "status": "bad-answer",
        },
    ]

    saved = [logger.log_request(**entry) for entry in sample_requests]

    cost_report = run_week11_cost_reduction(baseline_cost_usd=0.010, optimized_cost_usd=0.006, requests=100)
    support_drill = run_week11_support_drill(logs=saved, complaint="refund after 14 days")
    regression_case = build_week11_regression_case()

    if verbose:
        print("\n=== WEEK 11: PRODUCTION OBSERVABILITY & FAILURE LOOP ===")
        print(f"Logged {len(saved)} requests to {logger.log_path}")
        print(f"Average baseline cost/request: ${cost_report['avg_baseline_cost_usd']:.6f}")
        print(f"Average optimized cost/request: ${cost_report['avg_optimized_cost_usd']:.6f}")
        print(f"Savings: {cost_report['savings_percent']}%")
        print(f"Support drill matches: {support_drill['bad_match_count']}")
        print(f"Regression guard: {regression_case['name']}")

    return {
        "logged_requests": saved,
        "cost_report": cost_report,
        "support_drill": support_drill,
        "regression_case": regression_case,
        "log_path": logger.log_path,
    }


if __name__ == "__main__":
    run_week11_production_suite(verbose=True)
