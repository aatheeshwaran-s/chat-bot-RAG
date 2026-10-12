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

    def test_langfuse_logger_integration(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = os.path.join(tmp_dir, "request_log_langfuse.jsonl")
            logger = RequestLogger(log_path=log_path, use_langfuse=True)

            record = logger.log_request(
                question="What is the shipping time for domestic orders?",
                mode="hybrid",
                answer="Standard domestic shipping takes 2-3 business days.",
                retrieved_chunks=[{"filename": "shipping_policy.pdf", "text": "2-3 business days"}],
                latency_sec=0.85,
                estimated_cost_usd=0.0025,
                status="ok",
            )

            self.assertTrue(record["langfuse_enabled"])
            self.assertTrue(record["trace_id"].startswith("trace-") or len(record["trace_id"]) >= 8)
            self.assertEqual(record["cost_usd"], 0.0025)

            # Test flush
            logger.flush()
            self.assertEqual(len(logger.load_requests()), 1)

    def test_langfuse_with_custom_keys(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = os.path.join(tmp_dir, "request_log_keys.jsonl")
            logger = RequestLogger(
                log_path=log_path,
                public_key="pk-lf-mock",
                secret_key="sk-lf-mock",
                host="http://localhost:12000",
                use_langfuse=True,
            )

            record = logger.log_request(
                question="Can I exchange an open item?",
                mode="vector",
                answer="Opened items cannot be exchanged.",
                latency_sec=0.45,
                estimated_cost_usd=0.0015,
                status="bad-answer",
            )

            self.assertIn("trace_id", record)
            self.assertEqual(record["status"], "bad-answer")
            logger.flush()


if __name__ == "__main__":
    unittest.main()

