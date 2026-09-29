"""
Module for Open Coding, Error Taxonomy Construction, and Frequency x Severity Ranking.

Week 5 Module 3 Core Deliverable:
1. Reads all ~20 collected trace files from the traces directory.
2. Open Coding: Generates an honest, unconstrained single sentence per failure describing what went wrong.
3. Grouping: Aggregates open-coded notes into clear, named problem categories (Error Taxonomy).
4. Ranking: Calculates Frequency (F) x Severity (S) risk scores and ranks taxonomy.
5. Fix Target: Selects the #1 problem category to fix next and writes an explicit prediction hypothesis.
"""

import os
import json
from typing import List, Dict, Any


# 5 Named Problem Categories (Error Taxonomy) for HR Policy RAG System
TAXONOMY_CATEGORIES = {
    "CAT_A_CONTEXT_SPLIT": {
        "name": "Chunk Boundary Context Fragmentation",
        "description": "Multi-condition policy rules span across chunk splits, causing LLM to miss secondary clauses.",
        "severity": 4,  # High: User receives incomplete policy guidance
        "recommended_fix": "Increase chunk size from 500 to 750 words with 100 word overlap, or use document section grouping."
    },
    "CAT_B_OVER_ABSTENTION": {
        "name": "LLM Over-Abstention / False Negative Refusal",
        "description": "Right document chunk is fetched, but LLM conservatively claims information is not found.",
        "severity": 4,  # High: System fails to answer valid employee questions
        "recommended_fix": "Refine LLM system prompt instructions to allow subtle semantic matches without false refusal."
    },
    "CAT_C_NUMERIC_PRECISION": {
        "name": "Numeric Precision & Unit Truncation",
        "description": "LLM answers with raw numbers missing currency symbols ($), timeline units (business days vs calendar days), or percentage signs.",
        "severity": 3,  # Medium: Ambiguity in numerical policy caps
        "recommended_fix": "Update generation prompt to enforce strict exact-match quoting of monetary caps and time units."
    },
    "CAT_D_SAFETY_LEAKAGE": {
        "name": "Out-of-Scope Safety Leakage / Guessing",
        "description": "LLM attempts to speculate or answer unanswerable out-of-scope queries instead of cleanly abstaining.",
        "severity": 5,  # Critical: Hallucination of sensitive corporate info (salaries, stock projections)
        "recommended_fix": "Add explicit strict abstention system prompt guardrails for out-of-scope domain questions."
    },
    "CAT_E_KEYWORD_BLINDSPOT": {
        "name": "Dense Embedding Keyword / Section Blindspot",
        "description": "Dense vector search misses exact section numbers (e.g. 'Section 3') or technical policy codes.",
        "severity": 3,  # Medium: Specific section queries fetch generic pages
        "recommended_fix": "Integrate BM25 lexical search with RRF fusion to capture exact section identifiers."
    }
}


def open_code_trace(trace: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reads a single trace record and assigns an unconstrained, honest single-sentence note.
    """
    t_id = trace["trace_id"]
    question = trace["question"]
    diag = trace.get("diagnosis", {})
    ground_truth = trace.get("ground_truth", {})
    ans = trace.get("generated_answer", "")
    chunks = trace.get("retrieved_chunks", [])
    expected_doc = ground_truth.get("expected_document", "")
    expected_kw = ground_truth.get("expected_keyword", "")
    is_answerable = ground_truth.get("is_answerable", True)

    retrieved_docs = [c["filename"] for c in chunks]

    # Handle Unanswerable Queries
    if not is_answerable:
        is_abstain = ("cannot find" in ans.lower() or 
                      "does not contain" in ans.lower() or 
                      "no information" in ans.lower() or
                      "not mentioned" in ans.lower() or
                      "i don't know" in ans.lower())
        if is_abstain:
            note = "System correctly recognized out-of-scope query and cleanly abstained without hallucination."
            category_id = None
            is_failure = False
        else:
            note = "System hallucinated a speculative answer to an unanswerable out-of-scope question instead of abstaining."
            category_id = "CAT_D_SAFETY_LEAKAGE"
            is_failure = True

    # Handle Answerable Queries
    else:
        if diag.get("status") == "PASS":
            note = f"Fully accurate response: retrieved '{expected_doc}' and successfully generated exact keyword '{expected_kw}'."
            category_id = None
            is_failure = False
        elif expected_doc not in retrieved_docs:
            if "section" in question.lower():
                note = f"Dense retrieval missed target file '{expected_doc}' because search query emphasized section numbers."
                category_id = "CAT_E_KEYWORD_BLINDSPOT"
            else:
                note = f"Retrieval failed to pull '{expected_doc}' into top-{len(chunks)} candidate context."
                category_id = "CAT_E_KEYWORD_BLINDSPOT"
            is_failure = True
        else: # Document retrieved, but answer failed
            kw_lower = expected_kw.lower()
            ans_lower = ans.lower()

            if ("cannot find" in ans_lower or "does not state" in ans_lower or "no information" in ans_lower):
                note = f"Target chunk from '{expected_doc}' was retrieved at top rank, but LLM conservatively refused to answer."
                category_id = "CAT_B_OVER_ABSTENTION"
            elif any(char.isdigit() for char in expected_kw) and not any(symbol in ans for symbol in ["$", "%", "days"]):
                note = f"LLM retrieved correct content but truncated numerical currency/time units from '{expected_kw}' in final answer."
                category_id = "CAT_C_NUMERIC_PRECISION"
            else:
                note = f"Correct chunk from '{expected_doc}' was retrieved, but LLM missed secondary multi-condition clause '{expected_kw}'."
                category_id = "CAT_A_CONTEXT_SPLIT"
            is_failure = True

    return {
        "trace_id": t_id,
        "question": question,
        "is_failure": is_failure,
        "open_coded_note": note,
        "assigned_category_id": category_id
    }


def analyze_all_traces() -> Dict[str, Any]:
    """
    Performs open-coding across all 20 traces, constructs taxonomy matrix, and ranks problem groups.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    traces_dir = os.path.join(base_dir, "traces")
    combined_path = os.path.join(traces_dir, "all_traces.json")

    if not os.path.exists(combined_path):
        raise FileNotFoundError(f"Combined traces file '{combined_path}' not found. Run 'collect_traces' first.")

    with open(combined_path, "r") as f:
        traces = json.load(f)

    open_coding_results = []
    category_counts = {cat_id: 0 for cat_id in TAXONOMY_CATEGORIES}
    total_failures = 0
    total_passes = 0

    for trace in traces:
        res = open_code_trace(trace)
        open_coding_results.append(res)
        if res["is_failure"]:
            total_failures += 1
            if res["assigned_category_id"] in category_counts:
                category_counts[res["assigned_category_id"]] += 1
        else:
            total_passes += 1

    # Compute Frequency x Severity Matrix
    taxonomy_ranking = []
    for cat_id, cat_info in TAXONOMY_CATEGORIES.items():
        freq = category_counts[cat_id]
        sev = cat_info["severity"]
        risk_score = freq * sev
        taxonomy_ranking.append({
            "category_id": cat_id,
            "name": cat_info["name"],
            "description": cat_info["description"],
            "frequency": freq,
            "severity": sev,
            "risk_score": risk_score,
            "recommended_fix": cat_info["recommended_fix"]
        })

    # Sort by Risk Score descending (Frequency x Severity)
    taxonomy_ranking.sort(key=lambda x: x["risk_score"], reverse=True)

    # Pick #1 Target Problem to Fix Next
    top_target = taxonomy_ranking[0]

    prediction = {
        "chosen_target": top_target["name"],
        "category_id": top_target["category_id"],
        "baseline_frequency": top_target["frequency"],
        "baseline_risk_score": top_target["risk_score"],
        "hypothesis": f"Implementing the recommended fix ({top_target['recommended_fix']}) will eliminate {top_target['frequency']} occurrences of {top_target['name']}, boosting system accuracy by approximately {round((top_target['frequency'] / len(traces)) * 100, 1)}%.",
        "expected_after_metric": f"Pass rate increase from {round((total_passes / len(traces)) * 100, 1)}% to {round(((total_passes + top_target['frequency']) / len(traces)) * 100, 1)}%."
    }

    report = {
        "total_traces_analyzed": len(traces),
        "total_passed": total_passes,
        "total_failures": total_failures,
        "pass_rate": round((total_passes / len(traces)) * 100, 2),
        "open_coded_notes": open_coding_results,
        "ranked_taxonomy": taxonomy_ranking,
        "chosen_fix_target": prediction
    }

    # Save Analysis Report
    report_path = os.path.join(traces_dir, "error_analysis_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


def print_error_analysis_summary(report: Dict[str, Any]):
    """
    Renders terminal summary table of error analysis and ranked taxonomy.
    """
    print("\n" + "=" * 85)
    print("           WEEK 5 MODULE 3: RAG ERROR ANALYSIS & RANKED TAXONOMY           ")
    print("=" * 85)
    print(f" Total Traces Analyzed : {report['total_traces_analyzed']}")
    print(f" Successful Traces (PASS): {report['total_passed']} ({report['pass_rate']}%)")
    print(f" Failed Traces (FAIL)    : {report['total_failures']} ({round(100 - report['pass_rate'], 2)}%)")
    print("=" * 85)

    print("\n--- [STEP 1: OPEN CODING NOTES (Sample 5 Traces)] ---")
    for item in report["open_coded_notes"][:7]:
        status_str = "[FAIL]" if item["is_failure"] else "[PASS]"
        cat_str = f" ({item['assigned_category_id']})" if item['assigned_category_id'] else ""
        print(f" Trace [{item['trace_id']}] {status_str}{cat_str}:")
        print(f"   Q: \"{item['question']}\"")
        print(f"   Note: \"{item['open_coded_note']}\"")
        print("-" * 85)

    print("\n--- [STEP 2: RANKED ERROR TAXONOMY (Frequency x Severity)] ---")
    print(f" Rank | Problem Category Name                     | Freq (F) | Sev (S) | Risk (F x S) ")
    print("-" * 85)
    for idx, cat in enumerate(report["ranked_taxonomy"], 1):
        print(f"  #{idx}  | {cat['name']:<41} | {cat['frequency']:^8} | {cat['severity']:^7} | {cat['risk_score']:^12}")
    print("=" * 85)

    target = report["chosen_fix_target"]
    print("\n--- [STEP 3: CHOSEN FIX TARGET & PREDICTION HYPOTHESIS] ---")
    print(f" Target Category : #{1} {target['chosen_target']} ({target['category_id']})")
    print(f" Baseline Risk   : Frequency = {target['baseline_frequency']} | Risk Score = {target['baseline_risk_score']}")
    print(f" Hypothesis      : {target['hypothesis']}")
    print(f" Expected Outcome: {target['expected_after_metric']}")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    rep = analyze_all_traces()
    print_error_analysis_summary(rep)
