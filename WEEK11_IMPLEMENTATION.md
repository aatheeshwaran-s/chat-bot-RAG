# Week 11 Implementation: Production Observability, Cost Control & Failure-to-Test Loop

## Overview

This week’s implementation turns the project from a demo into an operational system that can be monitored, debugged, and improved over time. The work focuses on three production goals:

1. Observability: every request should leave a trace that can be inspected later.
2. Cost control: we measure the cost per request and show how to reduce it.
3. Failure-to-test loop: a real bad answer becomes a permanent guard against regressions.

---

## What I implemented

### 1) Request logging for every answer

I added a lightweight request logger in [app/week11_eval.py](app/week11_eval.py).

It records:
- trace ID
- timestamp
- question
- mode used (`vector` / `hybrid`)
- answer text
- retrieved chunks
- latency
- cost
- status (`ok`, `bad-answer`, `abstain`, etc.)

This means if a customer later says “the app gave the wrong answer,” we can find the exact request and replay the context.

### 2) Support-drill search for vague complaints

The implementation includes a support-drill function that scans recent request logs using complaint keywords.

Example workflow:
- complaint: “refund after 14 days”
- the drill scans logs for matching question + answer text
- it returns the relevant traces and makes diagnosis faster than manual inspection

This simulates the real production support workflow: a vague complaint, a search through logs, and a specific bad answer identified from evidence.

### 3) Cost-per-request measurement and optimization

I added a cost reduction summary that calculates:
- baseline cost per request
- optimized cost per request
- absolute savings
- percentage reduction

The implementation uses a simple but production-relevant formula:

$$
\text{avg\_baseline} = \frac{\text{baseline\_total}}{\text{requests}}
$$

$$
\text{avg\_optimized} = \frac{\text{optimized\_total}}{\text{requests}}
$$

$$
\text{savings\_pct} = \frac{\text{avg\_baseline} - \text{avg\_optimized}}{\text{avg\_baseline}} \times 100
$$

This makes cost visible instead of hidden in the system.

### 4) Failure-to-test guardrail

I encoded a real failure case as a permanent regression check:
- question: “Does the refund policy allow a refund after 14 days?”
- expected answer: the policy only allows refunds within 14 days, with the unopened condition
- bad answer: “You may still get a refund after 14 days.”

This is the classic failure-to-test loop: when a real bad answer surfaces, it becomes a guardrail for future releases.

---

## Files added/updated

- [app/week11_eval.py](app/week11_eval.py) — core observability, support drill, cost report, and regression guard
- [app/observability.py](app/observability.py) — convenience exports for the new module
- [app/main.py](app/main.py) — CLI integration and automatic request logging during query execution
- [tests/test_week11_observability.py](tests/test_week11_observability.py) — regression tests covering logging, support drill, and cost savings

---

## How this fits the Week 11 brief

The brief asks for:
- proper per-request logging
- a support drill over real request data
- measurement of cost per request
- at least one improvement in cost
- a failure turned into a permanent test

This implementation satisfies all four by combining:
- log capture for request-level monitoring
- complaint-based debugging workflow
- explicit cost summary reporting
- permanent regression case for the refund-policy bug

---

## Example mentor explanation

> “This is what production readiness looks like: the system records what it did, so we can trace a user complaint back to a specific request. We also measure cost per request so we know whether the app is efficient, and we convert real failures into automated regression tests so the same error cannot quietly reappear.”

---

## Verification evidence

I validated the implementation with commands run in the repo:

1. Unit tests:

```bash
cd /workspaces/chat-bot-RAG && PYTHONPATH=. python -m unittest tests.test_week11_observability -v
```

Result: 3 tests ran and all passed.

2. CLI check:

```bash
cd /workspaces/chat-bot-RAG && PYTHONPATH=. python -m app.main evaluate_w11
```

Result: completed successfully with a cost summary and support-drill output.

---

## Final takeaway

This implementation makes the application observable, measurable, and self-improving. It demonstrates the exact production mindset required for this module: if a bad answer appears, we can find it; if cost rises, we can measure it; and if a failure recurs, it is prevented by a permanent test.
