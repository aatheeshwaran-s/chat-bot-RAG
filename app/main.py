"""
Main CLI Application Controller for the RAG Chatbot Backend.

Provides beginner-friendly commands:
1. python -m app.main ingest    : Extract text from PDFs, generate embeddings, and index into local Qdrant.
2. python -m app.main query "..." : Ask a question to the chatbot with optional metadata filters.
3. python -m app.main chat      : Start an interactive terminal chat session.
4. python -m app.main evaluate  : Run the automated evaluation benchmark.
5. python -m app.main experiment: Compare chunking sizes (300 vs 500 vs 1000).
"""

import sys
import os
import argparse
from app.ingest import process_all_documents_in_folder
from app.embeddings import EmbeddingEngine
from app.retrieval import QdrantVectorStore
from app.generation import LLMGenerator
from app.evaluate import evaluate_rag_system
from app.experiments import run_all_experiments


def run_ingestion(chunk_size: int = 500, chunk_overlap: int = 50):
    """
    Full document ingestion pipeline: PDFs -> Text -> Chunks -> Embeddings -> Qdrant
    """
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


def answer_user_query(question: str, department: str = None, top_k: int = 8):
    """
    Single question answer workflow with optional metadata filtering.
    """
    engine = EmbeddingEngine()
    store = QdrantVectorStore()
    generator = LLMGenerator()

    # Step 1: Embed question
    q_vector = engine.embed_text(question)

    # Step 2: Vector search with optional metadata filter
    retrieved_chunks = store.similarity_search(
        query_vector=q_vector,
        top_k=top_k,
        filter_department=department
    )

    # Step 3: LLM generation & citations
    result = generator.generate_answer(question, retrieved_chunks)

    print("\n" + "="*60)
    print(f"[QUESTION] : {question}")
    if department:
        print(f"[FILTER]   : Department = {department}")
    print("="*60)
    print(f"[ANSWER]   :\n{result['answer']}")
    print("-" * 60)
    print(f"[SOURCES]  :\n{result['sources']}")
    print("="*60)

    return result


def start_interactive_chat():
    """
    Interactive CLI Chat loop.
    """
    print("\n=======================================================")
    print(" Welcome to the Company Document RAG Chatbot (CLI)")
    print(" Type 'exit' or 'quit' to stop.")
    print("=======================================================\n")

    engine = EmbeddingEngine()
    store = QdrantVectorStore()
    generator = LLMGenerator()

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            q_vector = engine.embed_text(user_input)
            retrieved = store.similarity_search(q_vector, top_k=5)
            result = generator.generate_answer(user_input, retrieved)

            print(f"\nAssistant:\n{result['answer']}\n")
            print(f"Source:\n{result['sources']}\n")
        except KeyboardInterrupt:
            print("\nSession ended.")
            break


def main():
    parser = argparse.ArgumentParser(description="RAG Chatbot Backend CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command
    parser_ingest = subparsers.add_parser("ingest", help="Ingest PDFs into Qdrant vector database")
    parser_ingest.add_argument("--chunk-size", type=int, default=500, help="Chunk size in words")
    parser_ingest.add_argument("--overlap", type=int, default=50, help="Chunk overlap in words")

    # Query command
    parser_query = subparsers.add_parser("query", help="Ask a question")
    parser_query.add_argument("question", type=str, help="User question string")
    parser_query.add_argument("--department", type=str, default=None, help="Filter by department (e.g. HR, Operations)")

    # Interactive chat command
    subparsers.add_parser("chat", help="Start interactive CLI chat")

    # Evaluate command
    subparsers.add_parser("evaluate", help="Run benchmark evaluation suite")

    # Experiment command
    subparsers.add_parser("experiment", help="Run chunk size comparison experiment")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingestion(chunk_size=args.chunk_size, chunk_overlap=args.overlap)
    elif args.command == "query":
        answer_user_query(args.question, department=args.department)
    elif args.command == "chat":
        start_interactive_chat()
    elif args.command == "evaluate":
        evaluate_rag_system()
    elif args.command == "experiment":
        run_all_experiments()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
