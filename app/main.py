"""
Main CLI Application Controller for the RAG Chatbot & Build Week Agent Engine.

Provides CLI commands:
1. python -m app.main ingest       : Extract text from PDFs, generate embeddings, and index into local Qdrant.
2. python -m app.main query "..."    : Ask a question to the chatbot with optional metadata filters.
3. python -m app.main agent "..."    : Run Hand-Built ReAct Agent with step-by-step visible execution trace.
4. python -m app.main workflow "..." : Run Plain Fixed Workflow pipeline.
5. python -m app.main race           : Run Agent vs. Plain Fixed Workflow comparison benchmark (Speed, Cost, Reliability).
6. python -m app.main chat         : Start interactive terminal chat session.
7. python -m app.main evaluate     : Run evaluation benchmark.
"""

import sys
import os
import argparse
from app.ingest import process_all_documents_in_folder
from app.embeddings import EmbeddingEngine
from app.retrieval import QdrantVectorStore
from app.generation import LLMGenerator
from app.evaluate import evaluate_rag_system, run_week4_experiment
from app.inspection import print_inspection_view
from app.hybrid import HybridSearchEngine
from app.agent import HandBuiltReActAgent
from app.workflow import PlainFixedWorkflow
from app.race import run_agent_vs_workflow_race


def run_ingestion(chunk_size: int = 500, chunk_overlap: int = 50):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_folder = os.path.join(base_dir, "documents")

    print("\n=== STEP 1 & 2: PDF Extraction & Chunking ===")
    chunks = process_all_documents_in_folder(docs_folder, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        print(f"No document chunks created. Make sure PDFs exist in '{docs_folder}'.")
        return

    print("\n=== STEP 3: Generating Local Embeddings ===")
    engine = EmbeddingEngine()
    vectors = engine.embed_chunks(chunks)

    print("\n=== STEP 4: Indexing into Local Qdrant Vector Store ===")
    store = QdrantVectorStore()
    store.create_collection(vector_size=engine.vector_dim)
    store.index_chunks(chunks, vectors)

    print("\n=== Ingestion Pipeline Complete! Your RAG vector database is ready ===")


def answer_user_query(question: str, department: str = None, top_k: int = 5, filename: str = None, mode: str = "vector"):
    engine = EmbeddingEngine()
    store = QdrantVectorStore()
    generator = LLMGenerator()

    if mode == "hybrid":
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docs_folder = os.path.join(base_dir, "documents")
        chunks = process_all_documents_in_folder(docs_folder, chunk_size=500, chunk_overlap=50)
        hybrid_searcher = HybridSearchEngine(store, engine, chunks)
        retrieved_chunks = hybrid_searcher.hybrid_search(question, top_k=top_k)
    else:
        q_vector = engine.embed_text(question)
        retrieved_chunks = store.similarity_search(
            query_vector=q_vector,
            top_k=top_k,
            filter_department=department,
            filter_filename=filename
        )

    result = generator.generate_answer(question, retrieved_chunks)

    print("\n" + "="*60)
    print(f"[QUESTION] : {question}")
    print(f"[MODE]     : {mode.upper()}")
    if department:
        print(f"[FILTER]   : Department = {department}")
    print("="*60)
    print(f"[ANSWER]   :\n{result['answer']}")
    print("-" * 60)
    print(f"[SOURCES]  :\n{result['sources']}")
    print("="*60)

    return result


def inspect_question(question: str, expected_doc: str = None, expected_kw: str = None, mode: str = "hybrid"):
    engine = EmbeddingEngine()
    store = QdrantVectorStore()
    generator = LLMGenerator()

    if mode == "hybrid":
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docs_folder = os.path.join(base_dir, "documents")
        all_chunks = process_all_documents_in_folder(docs_folder, chunk_size=500, chunk_overlap=50, verbose=False)
        searcher = HybridSearchEngine(store, engine, all_chunks)
        chunks = searcher.hybrid_search(question, top_k=3)
    else:
        q_vec = engine.embed_text(question)
        chunks = store.similarity_search(q_vec, top_k=3)

    response = generator.generate_answer(question, chunks)

    print_inspection_view(
        question=question,
        retrieved_chunks=chunks,
        answer=response["answer"],
        sources=response["sources"],
        expected_document=expected_doc,
        expected_keyword=expected_kw
    )


def start_interactive_chat():
    print("\n=======================================================")
    print(" Welcome to the Support Agent & RAG System (CLI)")
    print(" Type 'exit' or 'quit' to stop.")
    print("=======================================================\n")

    agent = HandBuiltReActAgent()

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            result = agent.run(user_input, verbose=True)
            print(f"\n[SUMMARY] Steps: {result['steps_taken']} | Time: {result['total_latency']}s | Tokens: {result['total_tokens']} | Cost: ${result['estimated_cost_usd']}")
        except KeyboardInterrupt:
            print("\nSession ended.")
            break


def main():
    parser = argparse.ArgumentParser(description="Build Week Agent & RAG Backend CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command
    parser_ingest = subparsers.add_parser("ingest", help="Ingest PDFs into Qdrant vector database")
    parser_ingest.add_argument("--chunk-size", type=int, default=500, help="Chunk size in words")
    parser_ingest.add_argument("--overlap", type=int, default=50, help="Chunk overlap in words")

    # Query command
    parser_query = subparsers.add_parser("query", help="Ask a question")
    parser_query.add_argument("question", type=str, help="User question string")
    parser_query.add_argument("--department", type=str, default=None, help="Filter by department")
    parser_query.add_argument("--filename", type=str, default=None, help="Filter results by filename")
    parser_query.add_argument("--mode", type=str, default="hybrid", choices=["vector", "hybrid"], help="Search mode")

    # Agent command
    parser_agent = subparsers.add_parser("agent", help="Run Hand-Built ReAct Agent on support ticket or question")
    parser_agent.add_argument("question", type=str, nargs="?", default="Customer Alice requested a refund for order TICK-101 purchased 12 days ago ($120). Check policy and process.", help="Ticket or question text")
    parser_agent.add_argument("--max-steps", type=int, default=5, help="Maximum step budget")

    # Workflow command
    parser_wf = subparsers.add_parser("workflow", help="Run Plain Fixed Workflow on support ticket or question")
    parser_wf.add_argument("question", type=str, nargs="?", default="Customer Alice requested a refund for order TICK-101 purchased 12 days ago ($120). Check policy and process.", help="Ticket or question text")

    # Race command
    subparsers.add_parser("race", help="Run Agent vs Plain Fixed Workflow Race Benchmark (Speed, Cost, Reliability)")

    # Inspect command
    parser_inspect = subparsers.add_parser("inspect", help="Side-by-side inspection view for retrieval & answer")
    parser_inspect.add_argument("question", type=str, nargs="?", default="What is the daily meal allowance cap for business travel expenses?", help="Question to inspect")

    # Interactive chat command
    subparsers.add_parser("chat", help="Start interactive CLI agent chat")

    # Evaluate command
    subparsers.add_parser("evaluate", help="Run benchmark evaluation suite")
    subparsers.add_parser("experiment_w4", help="Run Week 4 single-change hit-rate@3 experiment")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingestion(chunk_size=args.chunk_size, chunk_overlap=args.overlap)
    elif args.command == "query":
        answer_user_query(args.question, department=args.department, filename=args.filename, mode=args.mode)
    elif args.command == "agent":
        agent = HandBuiltReActAgent(max_steps=args.max_steps)
        res = agent.run(args.question, verbose=True)
        print(f"\nExecution Summary: Steps={res['steps_taken']}, Time={res['total_latency']}s, Tokens={res['total_tokens']}, Est Cost=${res['estimated_cost_usd']}")
    elif args.command == "workflow":
        wf = PlainFixedWorkflow()
        res = wf.run(args.question, verbose=True)
        print(f"\nExecution Summary: Steps={res['steps_taken']}, Time={res['total_latency']}s, Tokens={res['total_tokens']}, Est Cost=${res['estimated_cost_usd']}")
    elif args.command == "race":
        run_agent_vs_workflow_race(verbose=True)
    elif args.command == "inspect":
        inspect_question(args.question)
    elif args.command == "chat":
        start_interactive_chat()
    elif args.command in ("evaluate", "experiment_w4"):
        run_week4_experiment()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
