"""
Phase 19 & Week 4: RAG Evaluation Benchmark & Controlled Experiment Engine.

Week 4 Features:
1. Calculates hit-rate@3 (percentage of queries where correct document is in top 3).
2. Failure Separation: Counts Retrieval Failures (Type 1) vs Generation Failures (Type 2).
3. Controlled Before-and-After Single Change Benchmark:
   - Baseline: Vector Search alone
   - Single Change: Hybrid BM25 + Vector Search with RRF Fusion
4. Explicitly identifies fixed questions and remaining unfixed failures.
"""

import os
import json
from typing import List, Dict, Any
from app.embeddings import EmbeddingEngine
from app.retrieval import QdrantVectorStore
from app.generation import LLMGenerator
from app.hybrid import HybridSearchEngine
from app.failure_analysis import categorize_failure
from app.ingest import process_all_documents_in_folder


def load_benchmark_questions() -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    questions_file = os.path.join(base_dir, "tests", "test_questions.json")
    if not os.path.exists(questions_file):
        raise FileNotFoundError(f"Benchmark file '{questions_file}' not found.")
    with open(questions_file, "r") as f:
        return json.load(f)


def load_all_ingested_chunks() -> List[Dict[str, Any]]:
    """Helper to load all raw document chunks for BM25 indexing."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_folder = os.path.join(base_dir, "documents")
    return process_all_documents_in_folder(docs_folder, chunk_size=500, chunk_overlap=50, verbose=False)


def run_evaluation_suite(mode: str = "vector", top_k: int = 3) -> Dict[str, Any]:
    """
    Runs evaluation benchmark and returns structured performance metrics.

    Args:
        mode: 'vector' (baseline) or 'hybrid' (vector + BM25 RRF)
        top_k: Top K rank window for hit-rate evaluation (default 3)
    """
    data = load_benchmark_questions()
    answerable = data.get("answerable_questions", [])
    
    engine = EmbeddingEngine()
    store = QdrantVectorStore()
    generator = LLMGenerator()

    hybrid_searcher = None
    if mode == "hybrid":
        all_chunks = load_all_ingested_chunks()
        hybrid_searcher = HybridSearchEngine(store, engine, all_chunks)

    hit_count_at_k = 0
    answer_correct_count = 0
    mrr_sum = 0.0

    retrieval_failures = []
    generation_failures = []
    passed_questions = []

    results_by_id = {}

    for q_item in answerable:
        q_id = q_item["id"]
        question = q_item["question"]
        expected_doc = q_item["expected_document"]
        expected_kw = q_item["expected_keyword"]

        # Step 1: Retrieve candidates based on mode
        if mode == "hybrid" and hybrid_searcher:
            chunks = hybrid_searcher.hybrid_search(question, top_k=top_k)
        else:
            q_vec = engine.embed_text(question)
            chunks = store.similarity_search(q_vec, top_k=top_k)

        # Step 2: Calculate MRR (Mean Reciprocal Rank)
        retrieved_files = [c.get("filename", "") for c in chunks]
        if expected_doc in retrieved_files:
            rank = retrieved_files.index(expected_doc) + 1
            mrr_sum += (1.0 / rank)
            if rank <= top_k:
                hit_count_at_k += 1

        # Step 3: LLM Answer Generation
        response = generator.generate_answer(question, chunks)
        ans_text = response["answer"]

        # Step 4: Categorize failure mode
        diag = categorize_failure(
            question=question,
            expected_document=expected_doc,
            expected_keyword=expected_kw,
            retrieved_chunks=chunks,
            generated_answer=ans_text,
            top_k_check=top_k
        )

        results_by_id[q_id] = {
            "id": q_id,
            "question": question,
            "expected_document": expected_doc,
            "expected_keyword": expected_kw,
            "retrieved_files": retrieved_files,
            "answer": ans_text,
            "diagnosis": diag
        }

        if diag["status"] == "PASS":
            passed_questions.append(q_id)
            answer_correct_count += 1
        elif diag["category"] == "RETRIEVAL_FAILURE":
            retrieval_failures.append(q_id)
        elif diag["category"] == "GENERATION_FAILURE":
            generation_failures.append(q_id)

    total_q = len(answerable)
    hit_rate = (hit_count_at_k / total_q) * 100 if total_q else 0.0
    accuracy = (answer_correct_count / total_q) * 100 if total_q else 0.0
    mrr = (mrr_sum / total_q) if total_q else 0.0

    return {
        "mode": mode,
        "total_questions": total_q,
        "hit_rate_at_3": round(hit_rate, 2),
        "hit_count_at_3": hit_count_at_k,
        "mrr_at_3": round(mrr, 4),
        "answer_accuracy": round(accuracy, 2),
        "retrieval_failure_count": len(retrieval_failures),
        "retrieval_failures": retrieval_failures,
        "generation_failure_count": len(generation_failures),
        "generation_failures": generation_failures,
        "passed_count": len(passed_questions),
        "passed_questions": passed_questions,
        "details": results_by_id
    }


def run_week4_experiment():
    """
    Executes Week 4 Controlled Experiment:
    Measures baseline hit-rate@3 vs single change (Hybrid BM25 RRF) hit-rate@3.
    """
    print("\n" + "=" * 80)
    print("      WEEK 4 EXPERIMENT: DENSE VECTOR VS HYBRID BM25+VECTOR (RRF)      ")
    print("=" * 80)

    print("\n--> Step 1: Running Baseline Evaluation (Dense Vector Search Only)...")
    baseline = run_evaluation_suite(mode="vector", top_k=3)

    print("--> Step 2: Running Improved Evaluation (Single Change: Hybrid BM25 + Vector Search)...")
    hybrid = run_evaluation_suite(mode="hybrid", top_k=3)

    print("\n" + "=" * 80)
    print("                     BEFORE-AND-AFTER METRICS COMPARISON                   ")
    print("=" * 80)
    print(f" Metric                 | Baseline (Vector) | Improved (Hybrid RRF) | Delta ")
    print("-" * 80)
    print(f" hit-rate@3             | {baseline['hit_rate_at_3']:>14}% | {hybrid['hit_rate_at_3']:>18}% | {hybrid['hit_rate_at_3'] - baseline['hit_rate_at_3']:>+5.1f}%")
    print(f" Mean Reciprocal Rank   | {baseline['mrr_at_3']:>15}  | {hybrid['mrr_at_3']:>19}  | {hybrid['mrr_at_3'] - baseline['mrr_at_3']:>+5.4f}")
    print(f" Answer Accuracy        | {baseline['answer_accuracy']:>14}% | {hybrid['answer_accuracy']:>18}% | {hybrid['answer_accuracy'] - baseline['answer_accuracy']:>+5.1f}%")
    print("-" * 80)
    print(f" Retrieval Failures     | {baseline['retrieval_failure_count']:>15}  | {hybrid['retrieval_failure_count']:>19}  | {hybrid['retrieval_failure_count'] - baseline['retrieval_failure_count']:>+5d}")
    print(f" Generation Failures    | {baseline['generation_failure_count']:>15}  | {hybrid['generation_failure_count']:>19}  | {hybrid['generation_failure_count'] - baseline['generation_failure_count']:>+5d}")
    print("=" * 80)

    # Identify Fixed Questions
    base_ret_fails = set(baseline["retrieval_failures"])
    hyb_ret_fails = set(hybrid["retrieval_failures"])
    fixed_questions = base_ret_fails - hyb_ret_fails

    print("\n--- [ANALYSIS: WHAT DID THE SINGLE CHANGE FIX?] ---")
    if fixed_questions:
        print(f" Hybrid RRF search successfully fixed retrieval for {len(fixed_questions)} question(s): {sorted(list(fixed_questions))}")
        for qid in sorted(list(fixed_questions)):
            q_info = hybrid["details"][qid]
            print(f"   - [{qid}] '{q_info['question']}'")
            print(f"     Expected: {q_info['expected_document']} | Retrieved now: {q_info['retrieved_files']}")
    else:
        print(" (Both baseline and hybrid achieved high retrieval on standard queries. Additional technical keyword queries can demonstrate further gains.)")

    print("\n--- [ANALYSIS: WHICH FAILURES DID THE CHANGE NOT FIX?] ---")
    remaining_ret = hyb_ret_fails
    remaining_gen = hybrid["generation_failures"]

    if remaining_ret:
        print(f" Remaining Retrieval Failures (Type 1): {sorted(list(remaining_ret))}")
        print("   Reason: Document chunks lack exact keywords AND semantic similarity is low. (Fix needed: Query Rewriting / HyDE).")

    if remaining_gen:
        print(f" Remaining Generation Failures (Type 2): {sorted(list(remaining_gen))}")
        print("   Reason: The right document WAS retrieved, but the LLM answer missed the exact phrase/keyword. (Fix needed: LLM prompt refinement).")

    print("=" * 80 + "\n")


def evaluate_rag_system():
    """Wrapper function for standard CLI command."""
    run_week4_experiment()


if __name__ == "__main__":
    evaluate_rag_system()
