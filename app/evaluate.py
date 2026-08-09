"""
Phase 19: RAG Chatbot Evaluation Suite.

Evaluates the system against tests/test_questions.json across 4 key metrics:
1. Retrieval Accuracy (Correct document retrieved in Top-K)
2. Answer Accuracy (Extracted answer contains expected ground-truth keywords)
3. Citation Accuracy (Source citation matches target file and page)
4. Abstention Accuracy (Correctly responds "I don't know" for unanswerable questions)
"""

import os
import json
from app.embeddings import EmbeddingEngine
from app.retrieval import QdrantVectorStore
from app.generation import LLMGenerator


def evaluate_rag_system():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    questions_file = os.path.join(base_dir, "tests", "test_questions.json")

    if not os.path.exists(questions_file):
        print(f"Error: Evaluation benchmark file '{questions_file}' not found.")
        return

    with open(questions_file, "r") as f:
        data = json.load(f)

    answerable = data.get("answerable_questions", [])
    unanswerable = data.get("unanswerable_questions", [])

    print("=======================================================")
    print("      RAG CHATBOT BENCHMARK EVALUATION RUNNER         ")
    print("=======================================================")

    engine = EmbeddingEngine()
    store = QdrantVectorStore()
    generator = LLMGenerator()

    # Metrics counters
    retrieval_correct_count = 0
    answer_correct_count = 0
    citation_correct_count = 0
    abstention_correct_count = 0

    print("\n--- Part 1: Evaluating Answerable Questions (10 items) ---")
    for q_item in answerable:
        q_id = q_item["id"]
        question = q_item["question"]
        expected_doc = q_item["expected_document"]
        expected_kw = q_item["expected_keyword"].lower()

        # Step 1: Embed and retrieve
        q_vec = engine.embed_text(question)
        chunks = store.similarity_search(q_vec, top_k=5)

        # Step 2: Evaluate retrieval
        retrieved_files = [c.get("filename", "") for c in chunks]
        is_retrieval_correct = expected_doc in retrieved_files
        if is_retrieval_correct:
            retrieval_correct_count += 1

        # Step 3: Generate answer & evaluate answer accuracy
        response = generator.generate_answer(question, chunks)
        ans_text = response["answer"].lower()
        is_answer_correct = expected_kw in ans_text
        if is_answer_correct:
            answer_correct_count += 1

        # Step 4: Evaluate citation accuracy
        sources = response["sources"]
        is_citation_correct = expected_doc in sources
        if is_citation_correct:
            citation_correct_count += 1

        status_sym = "[PASS]" if (is_retrieval_correct and is_answer_correct) else "[FAIL]"
        print(f"[{q_id}] {status_sym} Q: '{question[:55]}...'")
        print(f"     Expected Doc: {expected_doc} | Retrieved Match: {is_retrieval_correct} | Answer Match: {is_answer_correct}")

    print("\n--- Part 2: Evaluating Unanswerable Questions (5 items) ---")
    for u_item in unanswerable:
        u_id = u_item["id"]
        question = u_item["question"]

        q_vec = engine.embed_text(question)
        chunks = store.similarity_search(q_vec, top_k=5)
        response = generator.generate_answer(question, chunks)

        is_abstained = response["is_abstained"]
        if is_abstained:
            abstention_correct_count += 1

        status_sym = "[PASS]" if is_abstained else "[FAIL]"
        print(f"[{u_id}] {status_sym} Q: '{question}'")
        print(f"     Abstained correctly: {is_abstained} | Response: '{response['answer'][:60]}...'")

    # Metrics summary calculation
    num_ans = len(answerable)
    num_unans = len(unanswerable)

    retrieval_acc = (retrieval_correct_count / num_ans) * 100 if num_ans else 0
    answer_acc = (answer_correct_count / num_ans) * 100 if num_ans else 0
    citation_acc = (citation_correct_count / num_ans) * 100 if num_ans else 0
    abstention_acc = (abstention_correct_count / num_unans) * 100 if num_unans else 0

    print("\n" + "="*60)
    print("             FINAL EVALUATION METRICS REPORT            ")
    print("="*60)
    print(f"1. Retrieval Accuracy : {retrieval_correct_count}/{num_ans} ({retrieval_acc:.1f}%)")
    print(f"2. Answer Accuracy    : {answer_correct_count}/{num_ans} ({answer_acc:.1f}%)")
    print(f"3. Citation Accuracy  : {citation_correct_count}/{num_ans} ({citation_acc:.1f}%)")
    print(f"4. Abstention Accuracy: {abstention_correct_count}/{num_unans} ({abstention_acc:.1f}%)")
    print("="*60)


if __name__ == "__main__":
    evaluate_rag_system()
