# Langfuse Observability & Terminal Query Guide

A complete guide to why observability is critical for AI systems, how to query your RAG chatbot from the terminal, and how to inspect, trace, and debug requests in the Langfuse Cloud dashboard.

---

## 1. Why Observability? (The "Why")

### The Silent Failure Problem
In traditional software, an error usually crashes the application or throws an HTTP `500 Internal Server Error`. Tools like **Datadog** or **New Relic** alert you immediately.

In Generative AI and RAG applications, **silent failures** occur:
- The server returns an HTTP `200 OK`.
- The database lookup succeeds.
- But the model hallucinates: e.g., falsely telling a customer *"You can get a full refund after 30 days"* when the official policy allows only 14 days.

Traditional APM tools cannot detect this. **LLM Observability (Langfuse)** solves this by tracking:
1. **Inputs & Outputs**: The exact question asked and the text generated.
2. **Retrieved Context**: Which specific PDF chunks and pages were passed to the LLM.
3. **Economics & Latency**: Token usage, cost per request in USD, total latency, and Time to First Token (TTFT).
4. **Failure-to-Test Loop**: Converting customer complaints into searchable traces and automated regression tests.

---

## 2. Environment Configuration

Your credentials are configured in [`.env`](file:///d:/chat%20bot/.env):

```ini
# Langfuse Project Credentials
LANGFUSE_PUBLIC_KEY="pk-lf-9b3542cf-0c88-4fef-8b8b-46dc823ae786"
LANGFUSE_SECRET_KEY="sk-lf-9db02458-e015-41d2-b6b5-1dc3dfa50fcb"
LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"
```

The system's [`RequestLogger`](file:///d:/chat%20bot/app/week11_eval.py) automatically reads these variables, strips surrounding quotes, connects to the US cloud endpoint, and handles trace exports with fail-safe fallbacks.

---

## 3. How to Ask Queries in the Terminal

You can interact with the chatbot in multiple ways from your terminal:

### Command 1: Single Question (Standard Vector Search)
Runs similarity search over document embeddings, generates a grounded answer, and pushes the trace to Langfuse.

```bash
python -m app.main query "What is the standard refund window?"
```

### Command 2: Hybrid Search (Vector + BM25 Keyword Search)
Combines dense semantic vectors with sparse BM25 keyword matching for maximum retrieval accuracy.

```bash
python -m app.main query "Can I get a refund after 20 days?" --mode hybrid
```

### Command 3: Filter by Department or Document
Narrow the search space to a specific business domain:

```bash
python -m app.main query "What is the meal allowance limit?" --filename "expense_policy.pdf"
```

### Command 4: Interactive CLI Chat (Turn-by-Turn)
Starts an interactive terminal conversation where every turn logs its own trace:

```bash
python -m app.main chat
```
- Type your question at the `You: ` prompt.
- The assistant displays the thought process, answer, latency, and Langfuse `Trace ID`.
- Type `exit` or `quit` to exit.

### Command 5: Week 11 Production Suite & Support Drill
Simulates production requests, computes cost reduction summaries, and runs a support drill:

```bash
python -m app.main week11 --complaint "refund after 14 days"
```

---

## 4. What Happens Behind the Scenes (Trace Lifecycle)

```
Terminal User Query
         │
         ▼
[1] Document Retrieval (Qdrant Vector DB + BM25)
         │  └─ Retrieves top matching chunks (e.g. refund_policy.pdf, Page 1)
         ▼
[2] LLM Generation
         │  └─ Feeds context into prompt, enforces strict grounding
         ▼
[3] Observability Measurement
         │  ├─ Measures exact latency (seconds)
         │  ├─ Computes token counts & estimated cost in USD
         │  └─ Captures Time to First Token (TTFT)
         ▼
[4] Dual-Write Logging
         ├─ Writes to local append-only log: logs/request_log.jsonl
         └─ Dispatches span to Langfuse Cloud (logger.flush())
```

---

## 5. How to View & Inspect Logs in Langfuse

1. Open your browser and navigate to **[us.cloud.langfuse.com](https://us.cloud.langfuse.com)**.
2. Log in and select your project.
3. Click **Tracing** in the left sidebar.

### Understanding the Dashboard Columns

| Column | What It Means | Why It Matters |
| :--- | :--- | :--- |
| **Type** | Set to `GENERATION` (or `CHAIN`) | Tells Langfuse this is an LLM inference call, unlocking Cost and Model columns. |
| **Status** | `Default` / `ok` / `bad-answer` | Indicates whether the query was successful or flagged for review. |
| **Latency (s)** | Time from request start to finish (e.g., `1.34s`) | Tracks end-to-end performance and latency regressions. |
| **Cost ($)** | Model cost in USD (e.g., `$0.0048`) | Tracks spend per request and verifies cost-optimization experiments. |
| **Time To First Token (s)** | Time until the 1st token arrives (e.g., `0.38s`) | Crucial for streaming UX; measures perceived responsiveness. |
| **Provided Model Name** | e.g. `google/gemini-2.5-flash` | Tracks which model generated the response for multi-model comparisons. |

### Inspecting a Specific Trace

1. **Locate the Trace**:
   - The latest terminal query will appear at the **top of the table**.
   - Alternatively, copy the `Trace ID` printed in your terminal (e.g., `5eb2151d0e3f3dbac37e9261cf4b9d97`) and paste it into the search box.
2. **Click the row** to open the inspection drawer:
   - **Input Tab**: Displays your terminal prompt.
   - **Output Tab**: Displays the exact answer generated.
   - **Metadata Tab**: Displays `chunks` (the exact PDF names, page numbers, and chunk IDs retrieved).
   - **Metrics Tab**: Full breakdown of prompt tokens, completion tokens, latency, and estimated cost.

---

## 6. Support Drill: Finding Bad Answers from Real Complaints

When a user complains that the bot gave incorrect information, use the **Support Drill**:

```bash
python -m app.main support-drill --complaint "refund after 14 days"
```

The drill automatically:
1. Searches recent traces for the complaint keywords.
2. Isolates the exact matching `trace_id` and bad answer.
3. Displays the faulty retrieved chunks.
4. Ties directly into the regression test in [`tests/test_week11_observability.py`](file:///d:/chat%20bot/tests/test_week11_observability.py) so the bug is permanently guarded against future regressions.
