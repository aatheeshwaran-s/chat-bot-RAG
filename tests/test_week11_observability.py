import os
import tempfile
import unittest

from app.week11_eval import RequestLogger, run_week11_support_drill, run_week11_cost_reduction


class Week11ObservabilityTests(unittest.TestCase):
    def test_request_logger_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = os.path.join(tmp_dir, "request_log.jsonl")
            logger = RequestLogger(log_path=log_path)

            record = logger.log_request(
                question="Can I get a refund after 20 days?",
                mode="hybrid",
                answer="Refunds are allowed only within 14 days.",
                retrieved_chunks=[{"filename": "refund_policy.pdf", "page": 2, "text": "Refunds within 14 days."}],
                latency_sec=1.2,
                estimated_cost_usd=0.004,
                trace_id="trace-001",
                status="bad-answer",
            )

            self.assertEqual(record["trace_id"], "trace-001")
            self.assertEqual(record["cost_usd"], 0.004)
            self.assertEqual(logger.load_requests()[0]["trace_id"], "trace-001")

    def test_support_drill_finds_the_bad_answer(self):
        bad_answer = {
            "trace_id": "trace-900",
            "answer": "You may still get a refund after 14 days.",
            "status": "bad-answer",
            "question": "Does the policy allow a refund after 14 days?",
        }

        drill = run_week11_support_drill(logs=[bad_answer], complaint="refund after 14 days")

        self.assertEqual(drill["bad_match_count"], 1)
        self.assertEqual(drill["matches"][0]["trace_id"], "trace-900")

    def test_cost_reduction_summary_reports_savings(self):
        summary = run_week11_cost_reduction(
            baseline_cost_usd=0.010,
            optimized_cost_usd=0.006,
            requests=100,
        )

        self.assertAlmostEqual(summary["avg_baseline_cost_usd"], 0.0001)
        self.assertAlmostEqual(summary["avg_optimized_cost_usd"], 0.00006)
        self.assertGreater(summary["savings_percent"], 0)


if __name__ == "__main__":
    unittest.main()
