"""
Week 10 Evaluation & Benchmark Suite: Single Agent vs. Multi-Agent Triage Squad Race.

Races:
1. Single Agent: HandBuiltReActAgent (Week 7 ReAct loop)
2. Multi-Agent Squad: TriageManagerAgent + 2 Specialists (Policy + Ticket/Math)

Measures 4 Key Evaluated Metrics:
1. Quality / Accuracy (%)
2. Speed / Avg Latency (seconds)
3. Total Tokens Used (including Context Re-send Overhead)
4. Total Estimated Cost ($ USD)

Produces an honest, empirical verdict on which architecture to keep.
"""

import os
import json
import time
import sys
import io
from typing import Dict, Any, List

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.agent import HandBuiltReActAgent
from app.multi_agent import MultiAgentTriageSquad
from app.race import load_ticket_benchmark, evaluate_response_correctness


def run_week10_single_vs_multi_race(verbose: bool = True) -> Dict[str, Any]:
    """
    Executes the Week 10 Race: Single Agent vs Multi-Agent Triage Squad.
    """
    tickets = load_ticket_benchmark()

    single_agent = HandBuiltReActAgent(max_steps=5, timeout_sec=15.0)
    multi_squad = MultiAgentTriageSquad()

    single_results = []
    multi_results = []

    print("\n" + "=" * 85)
    print("      [WEEK 10 BENCHMARK RACE] SINGLE AGENT VS. MULTI-AGENT TRIAGE SQUAD")
    print("=" * 85)
    print(f"Loaded {len(tickets)} benchmark support tickets from tests/ticket_eval_set.json.\n")

    single_correct_count = 0
    multi_correct_count = 0

    single_multi_correct = 0
    multi_multi_correct = 0
    multistep_total = 0

    for idx, t in enumerate(tickets, 1):
        t_id = t["ticket_id"]
        text = t["ticket_text"]
        expected_kw = t["expected_keyword"]
        expected_act = t["expected_action"]
        is_multi = t["is_multistep"]

        if is_multi:
            multistep_total += 1

        if verbose:
            print(f"--- Running Ticket {idx}/{len(tickets)} [{t_id}] (Multi-Step: {is_multi}) ---")

        # 1. Run Single Agent (Hand-Built ReAct Agent)
        s_res = single_agent.run(text, verbose=False)
        s_correct = evaluate_response_correctness(s_res["final_answer"], expected_kw, expected_act)
        s_res["is_correct"] = s_correct
        single_results.append(s_res)
        if s_correct:
            single_correct_count += 1
            if is_multi:
                single_multi_correct += 1

        # 2. Run Multi-Agent Triage Squad (Manager + 2 Specialists)
        m_res = multi_squad.run(text, verbose=False)
        m_correct = evaluate_response_correctness(m_res["final_answer"], expected_kw, expected_act)
        m_res["is_correct"] = m_correct
        multi_results.append(m_res)
        if m_correct:
            multi_correct_count += 1
            if is_multi:
                multi_multi_correct += 1

        if verbose:
            print(f"  Single Agent : Time={s_res['total_latency']}s | Tokens={s_res['total_tokens']} | Correct={s_correct}")
            print(f"  Multi-Squad  : Time={m_res['total_latency']}s | Tokens={m_res['total_tokens']} (Re-send: {m_res.get('context_resend_tokens', 0)}) | Correct={m_correct}")
            print("-" * 85)

    total_q = len(tickets)

    # Compute Single Agent Metrics
    s_avg_time = sum(r["total_latency"] for r in single_results) / total_q
    s_total_tokens = sum(r["total_tokens"] for r in single_results)
    s_total_cost = sum(r["estimated_cost_usd"] for r in single_results)
    s_accuracy = (single_correct_count / total_q) * 100
    s_multi_acc = (single_multi_correct / multistep_total * 100) if multistep_total else 0.0

    # Compute Multi-Agent Squad Metrics
    m_avg_time = sum(r["total_latency"] for r in multi_results) / total_q
    m_total_tokens = sum(r["total_tokens"] for r in multi_results)
    m_resend_tokens = sum(r.get("context_resend_tokens", 0) for r in multi_results)
    m_total_cost = sum(r["estimated_cost_usd"] for r in multi_results)
    m_accuracy = (multi_correct_count / total_q) * 100
    m_multi_acc = (multi_multi_correct / multistep_total * 100) if multistep_total else 0.0

    # Print Full Comparative Table
    print("\n" + "=" * 85)
    print("                WEEK 10 BENCHMARK: SINGLE AGENT VS MULTI-AGENT SQUAD               ")
    print("=" * 85)
    print(f" Evaluated Metric           | Single Agent        | Multi-Agent Squad   | Overhead / Diff")
    print("-" * 85)
    print(f" Quality (Overall Accuracy) | {s_accuracy:>14.1f}% | {m_accuracy:>16.1f}% | {m_accuracy - s_accuracy:>+6.1f}%")
    print(f" Multi-Step Task Accuracy   | {s_multi_acc:>14.1f}% | {m_multi_acc:>16.1f}% | {m_multi_acc - s_multi_acc:>+6.1f}%")
    print(f" Avg Speed (Latency/ticket) | {s_avg_time:>14.3f} s | {m_avg_time:>16.3f} s | {m_avg_time - s_avg_time:>+6.3f} s")
    print(f" Total Tokens Used          | {s_total_tokens:>14d}   | {m_total_tokens:>16d}   | {m_total_tokens - s_total_tokens:>+6d} ({((m_total_tokens-s_total_tokens)/s_total_tokens)*100:+.1f}%)")
    print(f" Context Re-send Overhead   | {'0 tokens':>14s}   | {m_resend_tokens:>16d}   | +{m_resend_tokens} tokens")
    print(f" Total Estimated Cost ($)   | ${s_total_cost:>14.6f} | ${m_total_cost:>16.6f} | ${m_total_cost - s_total_cost:>+8.6f}")
    print("=" * 85)

    # Print Evidence-Based Verdict
    print("\n" + "=" * 85)
    print("                        [WEEK 10 VERDICT & FINDINGS]                                ")
    print("=" * 85)

    if s_accuracy >= m_accuracy:
        verdict_winner = "SINGLE AGENT"
        verdict_reason = (
            f"The Single Agent achieved equal or higher quality ({s_accuracy:.1f}% vs {m_accuracy:.1f}%) "
            f"while saving {((m_total_tokens-s_total_tokens)/s_total_tokens)*100:.1f}% in tokens and "
            f"running in {m_avg_time - s_avg_time:.3f}s faster average latency per ticket."
        )
    else:
        verdict_winner = "MULTI-AGENT TRIAGE SQUAD"
        verdict_reason = (
            f"The Multi-Agent Squad achieved higher quality ({m_accuracy:.1f}% vs {s_accuracy:.1f}%), "
            f"justifying the token and latency overhead."
        )

    print(f"VERDICT WINNER: {verdict_winner}")
    print(f"WHY: {verdict_reason}\n")
    print("ANALYSIS OF MULTI-AGENT HAND-OFF COSTS:")
    print(f"1. Context Re-send Cost: Every hand-off re-sent query & context envelopes, adding {m_resend_tokens} extra tokens.")
    print(f"2. Latency Impact: Sequential A2A specialist invocations added ~{m_avg_time - s_avg_time:.3f}s per request.")
    print("3. When Multi-Agent IS Worth It:")
    print("   - When tasks can run truly in parallel across independent workers (e.g. parallel document extraction).")
    print("   - When specialists require completely distinct prompt constraints, tools, or model parameters.")
    print("4. When Single Agent IS Superior:")
    print("   - For standard sequential customer ticket resolution where 1 tool-calling ReAct agent can inspect policy, fetch DB records, and answer directly in a single context window.")
    print("=" * 85 + "\n")

    return {
        "single_agent": {
            "accuracy": round(s_accuracy, 1),
            "multi_step_accuracy": round(s_multi_acc, 1),
            "avg_latency_sec": round(s_avg_time, 3),
            "total_tokens": s_total_tokens,
            "context_resend_tokens": 0,
            "total_cost_usd": round(s_total_cost, 6)
        },
        "multi_agent_squad": {
            "accuracy": round(m_accuracy, 1),
            "multi_step_accuracy": round(m_multi_acc, 1),
            "avg_latency_sec": round(m_avg_time, 3),
            "total_tokens": m_total_tokens,
            "context_resend_tokens": m_resend_tokens,
            "total_cost_usd": round(m_total_cost, 6)
        },
        "verdict_winner": verdict_winner,
        "verdict_reason": verdict_reason
    }


if __name__ == "__main__":
    run_week10_single_vs_multi_race()
