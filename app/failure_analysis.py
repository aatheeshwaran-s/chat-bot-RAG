"""
Module for Categorizing and Labeling RAG Failure Modes.

Week 4 Core Learning Concept:
Tells apart the TWO fundamental kinds of RAG failures:
1. FAILURE_TYPE_1 (Retrieval Failure - "Wrong Document Fetched"):
   The vector/hybrid search engine failed to bring the target document/chunk into top-k.
   Switching to a smarter LLM will NOT fix this. Retrieval fix needed (BM25, Hybrid, Reranking, HyDE).

2. FAILURE_TYPE_2 (Generation Failure - "Right Document, Wrong Answer"):
   The correct document WAS retrieved in top-k, but the LLM hallucinated, missed key details, or abstained.
   Retrieval is working fine. LLM Prompt engineering / context formatting fix needed.
"""

from typing import List, Dict, Any


def categorize_failure(
    question: str,
    expected_document: str,
    expected_keyword: str,
    retrieved_chunks: List[Dict[str, Any]],
    generated_answer: str,
    top_k_check: int = 3
) -> Dict[str, Any]:
    """
    Diagnoses a query execution and classifies outcome into PASS, RETRIEVAL_FAILURE, or GENERATION_FAILURE.

    Args:
        question: User question
        expected_document: Target ground truth PDF filename
        expected_keyword: Expected ground truth phrase/number in final answer
        retrieved_chunks: Top chunks returned by retrieval engine
        generated_answer: Text response produced by LLM generator
        top_k_check: Rank threshold (default top-3) to verify document presence

    Returns:
        Dict containing status label, category description, and explicit evidence.
    """
    check_chunks = retrieved_chunks[:top_k_check]
    retrieved_filenames = [c.get("filename", "") for c in check_chunks]
    
    # 1. Check if target document was retrieved in top_k
    is_doc_retrieved = expected_document in retrieved_filenames

    # 2. Check if generated answer contains ground truth keyword
    ans_lower = generated_answer.lower()
    kw_lower = expected_keyword.lower()
    is_answer_correct = kw_lower in ans_lower

    if is_doc_retrieved and is_answer_correct:
        return {
            "status": "PASS",
            "category": "SUCCESS",
            "is_retrieval_success": True,
            "is_answer_success": True,
            "evidence": f"Correct document '{expected_document}' retrieved in top-{top_k_check} and answer contained '{expected_keyword}'."
        }
    elif not is_doc_retrieved:
        return {
            "status": "FAIL",
            "category": "RETRIEVAL_FAILURE",
            "failure_type": "Failure Type 1 (Wrong document fetched)",
            "is_retrieval_success": False,
            "is_answer_success": is_answer_correct,
            "evidence": f"Expected '{expected_document}' was missing from top-{top_k_check} results (Retrieved: {retrieved_filenames})."
        }
    else:  # Document WAS retrieved, but answer failed
        return {
            "status": "FAIL",
            "category": "GENERATION_FAILURE",
            "failure_type": "Failure Type 2 (Right document fetched, wrong answer)",
            "is_retrieval_success": True,
            "is_answer_success": False,
            "evidence": f"Right document '{expected_document}' was fetched at rank #{retrieved_filenames.index(expected_document)+1}, but answer missed keyword '{expected_keyword}'."
        }
