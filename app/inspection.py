"""
Module for Side-by-Side Visual Inspection of RAG System Runs.

Week 4 Learning Concept:
Provides a clear inspection view showing:
- User Question
- Top-K Retrieved Chunks (Rank, Filename, Page, Score, Content Snippet)
- LLM Generated Answer & Source Citations
- Failure Mode Classifier (Pass vs Retrieval Failure vs Generation Failure)
"""

from typing import List, Dict, Any, Optional
from app.failure_analysis import categorize_failure


def print_inspection_view(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    answer: str,
    sources: str,
    expected_document: Optional[str] = None,
    expected_keyword: Optional[str] = None
):
    """
    Renders a clear CLI inspection view comparing fetched chunks and final answer.
    """
    print("\n" + "=" * 80)
    print("                      RAG RETRIEVAL INSPECTION VIEW                      ")
    print("=" * 80)
    print(f"QUESTION: {question}")
    print("=" * 80)

    # Left Column: Retrieved Chunks
    print("\n--- [TOP-K RETRIEVED CHUNKS] ---")
    if not retrieved_chunks:
        print("  (No chunks retrieved)")
    else:
        for idx, chunk in enumerate(retrieved_chunks, 1):
            fname = chunk.get("filename", "Unknown")
            page = chunk.get("page", 1)
            cid = chunk.get("chunk_id", "N/A")
            score = chunk.get("score", chunk.get("rrf_score", 0.0))
            text_snippet = chunk.get("text", "").replace("\n", " ")[:120]
            
            print(f" Rank #{idx} | Score: {score:.4f} | Doc: {fname} (Page {page}, Chunk: {cid})")
            print(f"   Snippet: \"{text_snippet}...\"")
            print("-" * 75)

    # Right Column: Generated Answer & Citations
    print("\n--- [GENERATED ANSWER & CITATIONS] ---")
    print(f"Answer:\n{answer}\n")
    print(f"Sources:\n{sources}")
    print("=" * 80)

    # Failure Separation Diagnosis (if ground truth expected)
    if expected_document and expected_keyword:
        diag = categorize_failure(
            question=question,
            expected_document=expected_document,
            expected_keyword=expected_keyword,
            retrieved_chunks=retrieved_chunks,
            generated_answer=answer
        )
        print("--- [FAILURE SEPARATION DIAGNOSIS] ---")
        if diag["status"] == "PASS":
            print(f" Status    : [PASS] SUCCESS")
        else:
            print(f" Status    : [FAIL] {diag['failure_type']}")
        print(f" Evidence  : {diag['evidence']}")
        print("=" * 80 + "\n")
        return diag

    print("=" * 80 + "\n")
    return None
