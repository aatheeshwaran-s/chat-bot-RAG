"""
Unit & Regression Test Suite: Closed Failure-to-Test Loop Guard (Track A).

Permanently guards against the real production failure that produced CEO escalations:
An agent or bot quoting the retired 14-day refund window to a customer on the active 30-day policy.
"""

import unittest
from app.capstone_agent import Tier1DeflectionAssistant


class ClosedFailureLoopRegressionTests(unittest.TestCase):
    """Permanent regression test guard for Track A refund terms."""

    @classmethod
    def setUpClass(cls):
        cls.agent = Tier1DeflectionAssistant(verbose=False)

    def test_ceo_escalation_failure_is_permanently_guarded(self):
        """
        REGRESSION GUARD: Customer Charlie (ORD-503, CUST-103) requested a refund on Day 18.
        The old retired macro would falsely reject this at 14 days.
        The guarded integrated system MUST:
        1. Check customer plan entitlement (STANDARD_CURRENT).
        2. Approve the refund ($85.00).
        3. Cite the Current 30-Day Policy [help-center/refund-policy-current-30day].
        4. NEVER cite the retired 14-day window.
        """
        ticket = "Customer Charlie (Order #ORD-503) requests a refund for wireless headset purchased 18 days ago ($85.00)."
        res = self.agent.run(ticket_query=ticket, ticket_id="TICK-103")
        reply = res["final_answer"]

        # Assertion 1: Entitlement tool check was executed
        self.assertTrue(res["entitlement_checked"], "Entitlement check tool MUST be called before resolution.")

        # Assertion 2: Full refund is approved, not falsely rejected
        self.assertTrue(res["deflected"], "Valid refund within 30 days must be deflected/approved.")
        self.assertIn("$85.00", reply, "Approved refund dollar amount ($85.00) must appear in reply.")

        # Assertion 3: Correct policy slug is cited
        self.assertIn("help-center/refund-policy-current-30day", reply, "Reply MUST cite the active 30-day policy slug.")

        # Assertion 4: Permanent negative guard - never quote the retired 14-day window to 30-day customers!
        self.assertNotIn("refund-policy-legacy-14day", reply, "REGRESSION DETECTED: Superseded legacy 14-day policy cited to active 30-day customer!")
        self.assertNotIn("14 calendar days", reply, "REGRESSION DETECTED: Quoted retired 14-day return window!")

    def test_legacy_grandfathered_customer_receives_legacy_cutoff(self):
        """
        Asserts that grandfathered accounts (e.g. David ORD-504) on Day 16 correctly receive
        the legacy 14-day cutoff with appropriate citation of help-center/refund-policy-legacy-14day.
        """
        ticket = "Customer David (Order #ORD-504) requests refund on legacy terminal controller purchased 16 days ago ($190.00)."
        res = self.agent.run(ticket_query=ticket, ticket_id="TICK-104")
        reply = res["final_answer"]

        self.assertIn("help-center/refund-policy-legacy-14day", reply, "Legacy account must cite legacy terms slug.")
        self.assertIn("14", reply, "Legacy terms cutoff must specify 14-calendar-day window.")
        self.assertTrue("cannot" in reply.lower() or "denied" in reply.lower(), "Request beyond 14 days must be declined.")

    def test_trace_id_survives_mcp_hop_and_pii_is_scrubbed(self):
        """
        Observability verification:
        Ensures trace_id survives across all spans and customer email/address are scrubbed.
        """
        incoming_tid = "tr-test-guard-99"
        ticket = "Customer Alice (Order #ORD-501) requested refund 12 days ago ($120.00)."
        res = self.agent.run(ticket_query=ticket, ticket_id="TICK-101", incoming_trace_id=incoming_tid)

        record = res["trace_record"]
        self.assertEqual(record["trace_id"], incoming_tid, "Incoming trace_id must be preserved end-to-end.")

        # Assert no PII entered the record
        rec_str = str(record)
        self.assertNotIn("@", rec_str, "Customer email leaked in trace record!")
        self.assertNotIn("Evergreen Terrace", rec_str, "Customer address leaked in trace record!")


if __name__ == "__main__":
    unittest.main()
