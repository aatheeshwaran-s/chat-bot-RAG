"""
Module for Collecting & Persisting Execution Traces for Error Analysis.

Week 5 Module 3 Core Concept:
A complete "trace" is a full record of one request:
- Question & Query Category
- System state / Search mode
- Top-K Retrieved Chunks (Rank, Filename, Page, Score, Snippet)
- LLM Generated Answer & Source Citations
- Ground truth metadata (expected document, keyword, answerability)
- Automated diagnosis & evidence
"""

import os
import json
import datetime
from typing import List, Dict, Any
from app.embeddings import EmbeddingEngine
from app.retrieval import QdrantVectorStore
from app.generation import LLMGenerator
from app.hybrid import HybridSearchEngine
from app.failure_analysis import categorize_failure
from app.ingest import process_all_documents_in_folder


def get_traces_dir() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    traces_dir = os.path.join(base_dir, "traces")
    os.makedirs(traces_dir, exist_ok=True)
    return traces_dir


def load_trace_questions() -> List[Dict[str, Any]]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    questions_file = os.path.join(base_dir, "tests", "trace_questions.json")
    if not os.path.exists(questions_file):
        raise FileNotFoundError(f"Trace questions file '{questions_file}' not found.")
    with open(questions_file, "r") as f:
        data = json.load(f)
        return data.get("trace_questions", [])


def collect_all_traces(mode: str = "hybrid", top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Executes the 20 benchmark queries and records complete trace data to JSON files.
    """
    questions = load_trace_questions()
    traces_dir = get_traces_dir()

    print(f"\n--> Initializing RAG Pipeline for Trace Collection (Mode: {mode.upper()}, Top-K: {top_k})...")
    engine = EmbeddingEngine()
    store = QdrantVectorStore()
    generator = LLMGenerator()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_folder = os.path.join(base_dir, "documents")
    all_chunks = process_all_documents_in_folder(docs_folder, chunk_size=500, chunk_overlap=50, verbose=False)
    hybrid_searcher = HybridSearchEngine(store, engine, all_chunks) if mode == "hybrid" else None

    recorded_traces = []

    for idx, item in enumerate(questions, 1):
        q_id = item["id"]
        q_cat = item["category_type"]
        question = item["question"]
        expected_doc = item["expected_document"]
        expected_kw = item["expected_keyword"]
        is_answerable = item.get("is_answerable", True)

        # Step 1: Retrieve candidate chunks
        if mode == "hybrid" and hybrid_searcher:
            raw_chunks = hybrid_searcher.hybrid_search(question, top_k=top_k)
        else:
            q_vec = engine.embed_text(question)
            raw_chunks = store.similarity_search(q_vec, top_k=top_k)

        formatted_chunks = []
        for rank, c in enumerate(raw_chunks, 1):
            formatted_chunks.append({
                "rank": rank,
                "filename": c.get("filename", "Unknown"),
                "page": c.get("page", 1),
                "chunk_id": c.get("chunk_id", "N/A"),
                "score": float(c.get("score", c.get("rrf_score", 0.0))),
                "text_snippet": c.get("text", "")[:250]
            })

        # Step 2: Generate Answer
        response = generator.generate_answer(question, raw_chunks)
        ans_text = response["answer"]
        sources_text = response["sources"]

        # Step 3: Run Diagnosis (for answerable queries)
        if is_answerable:
            diag = categorize_failure(
                question=question,
                expected_document=expected_doc,
                expected_keyword=expected_kw,
                retrieved_chunks=raw_chunks,
                generated_answer=ans_text,
                top_k_check=top_k
            )
        else:
            is_abstain = ("cannot find" in ans_text.lower() or 
                          "does not contain" in ans_text.lower() or 
                          "no information" in ans_text.lower() or
                          "not mentioned" in ans_text.lower() or
                          "i don't know" in ans_text.lower())
            diag = {
                "status": "PASS" if is_abstain else "FAIL",
                "category": "SUCCESS" if is_abstain else "GENERATION_FAILURE",
                "failure_type": "None" if is_abstain else "Failure Type 2 (Hallucinated out-of-scope answer)",
                "is_retrieval_success": True,
                "is_answer_success": is_abstain,
                "evidence": "Correctly abstained on out-of-scope query." if is_abstain else "Failed to abstain on unanswerable query."
            }

        trace_obj = {
            "trace_id": q_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "category_type": q_cat,
            "question": question,
            "search_mode": mode,
            "top_k": top_k,
            "retrieved_chunks": formatted_chunks,
            "generated_answer": ans_text,
            "sources": sources_text,
            "ground_truth": {
                "expected_document": expected_doc,
                "expected_keyword": expected_kw,
                "is_answerable": is_answerable
            },
            "diagnosis": diag
        }

        recorded_traces.append(trace_obj)

        # Write individual trace file
        file_path = os.path.join(traces_dir, f"trace_{q_id.lower()}.json")
        with open(file_path, "w") as f:
            json.dump(trace_obj, f, indent=2)

        print(f" Recorded [{q_id}] ({q_cat}) -> Status: {diag['status']} ({diag['category']})")

    # Write combined traces file
    combined_path = os.path.join(traces_dir, "all_traces.json")
    with open(combined_path, "w") as f:
        json.dump(recorded_traces, f, indent=2)

    print(f"\n=== Successfully recorded {len(recorded_traces)} trace files in '{traces_dir}' ===")
    return recorded_traces


if __name__ == "__main__":
    collect_all_traces()
