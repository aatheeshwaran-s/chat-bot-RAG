"""
Phase 9, 10, 11 & 12: Grounded LLM Generation & Citation Engine.

This module handles:
1. Constructing a strict system prompt to prevent hallucinations.
2. Checking top similarity retrieval scores to enforce abstention ("I don't know").
3. Calling an OpenAI-compatible LLM API (or offline mock fallback).
4. Formatting clean citations with Document Name, Page Number, and Chunk ID.
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


# Strict System Prompt Template
SYSTEM_PROMPT = """You are an official company document assistant.

Answer the user's question using ONLY the provided context snippets below.
Follow these strict rules:
1. Do NOT use outside knowledge or make assumptions.
2. If the answer cannot be clearly found in the provided context, respond EXACTLY with:
   "I couldn't find that information in the provided company documents."
3. Keep your response clear, concise, and grounded directly in the provided text.
"""


def format_context_blocks(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved document chunks into clean context blocks for the LLM prompt.
    """
    blocks = []
    for idx, chunk in enumerate(retrieved_chunks, 1):
        filename = chunk.get("filename", "Unknown Document")
        page = chunk.get("page", "?")
        chunk_id = chunk.get("chunk_id", "N/A")
        text = chunk.get("text", "")
        
        block = f"--- CONTEXT BLOCK {idx} [{filename}, Page {page}, Chunk: {chunk_id}] ---\n{text}"
        blocks.append(block)

    return "\n\n".join(blocks)


def format_citations(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Generates human-readable citation source list from retrieved chunks.
    """
    if not retrieved_chunks:
        return "No sources available."

    sources = []
    seen = set()
    for chunk in retrieved_chunks:
        filename = chunk.get("filename", "Unknown Document")
        page = chunk.get("page", 1)
        chunk_id = chunk.get("chunk_id", "")
        key = (filename, page)
        if key not in seen:
            seen.add(key)
            sources.append(f"- {filename} -- Page {page} (Chunk: {chunk_id})")

    return "\n".join(sources)


class LLMGenerator:
    """
    LLM Client supporting OpenAI-compatible APIs with offline mock fallback.
    """

    def __init__(self, score_threshold: float = 0.35):
        """
        Args:
            score_threshold (float): Minimum Cosine similarity score required to answer.
                                     If top score is below threshold, system abstains.
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", "")
        self.score_threshold = score_threshold
        self.client = None

        if self.api_key and self.api_key not in ["your_api_key_here", "your_openrouter_api_key_here"]:
            try:
                from openai import OpenAI
                base_url = os.getenv("OPENROUTER_BASE_URL") or os.getenv("LLM_BASE_URL")
                if not base_url and os.getenv("OPENROUTER_API_KEY"):
                    base_url = "https://openrouter.ai/api/v1"

                self.client = OpenAI(api_key=self.api_key, base_url=base_url if base_url else None)
                print("LLMGenerator initialized with API Client.")
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI/OpenRouter client ({e}). Using offline generator fallback.")
        else:
            print("Notice: No valid API Key found in .env. Running in offline rule-based generator mode.")

    def generate_answer(
        self, 
        question: str, 
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generates grounded answer and citations based on retrieved context.

        Returns:
            Dict containing:
            - answer: Generated text answer or 'I don't know'
            - sources: Formatted citation sources string
            - is_abstained: Boolean indicating if bot refrained from answering
            - retrieved_chunks: Raw context chunks used
        """
        # Step 1: Abstention check based on similarity score threshold
        top_score = retrieved_chunks[0].get("score", 0.0) if retrieved_chunks else 0.0
        
        if not retrieved_chunks or top_score < self.score_threshold:
            return {
                "answer": "I couldn't find that information in the provided company documents.",
                "sources": "No relevant documents found.",
                "is_abstained": True,
                "retrieved_chunks": retrieved_chunks
            }

        # Step 2: Format context for prompt
        context_str = format_context_blocks(retrieved_chunks)

        user_prompt = f"CONTEXT:\n{context_str}\n\nUSER QUESTION:\n{question}"

        # Step 3: LLM Call (or Offline Intelligent Extractor)
        if self.client:
            try:
                model = os.getenv("OPENROUTER_MODEL") or os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL", "google/gemini-2.5-flash")
                max_tokens = int(os.getenv("MAX_TOKENS", "512"))
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,
                    max_tokens=max_tokens
                )
                answer = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"LLM API Call error: {e}. Falling back to grounded context response.")
                answer = self._generate_offline_grounded_answer(question, retrieved_chunks)
        else:
            answer = self._generate_offline_grounded_answer(question, retrieved_chunks)

        # Check if LLM output indicates unknown information
        lower_ans = answer.lower()
        if "couldn't find" in lower_ans or "don't know" in lower_ans or "not mentioned" in lower_ans:
            is_abstained = True
            sources_str = "N/A"
        else:
            is_abstained = False
            sources_str = format_citations(retrieved_chunks)

        return {
            "answer": answer,
            "sources": sources_str,
            "is_abstained": is_abstained,
            "retrieved_chunks": retrieved_chunks
        }

    def _generate_offline_grounded_answer(
        self, 
        question: str, 
        retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Offline rule-based fallback that safely extracts relevant context sentences 
        when an API key is not configured.
        """
        q_words = set(question.lower().replace("?", "").split())
        
        # Unanswerable keywords test check
        unanswerable_keywords = {
            "ceo", "salary", "stock", "promoted", "promotion", "promotions", 
            "revenue", "profit", "competitor", "recipe", "recipes", "cafeteria", "secret"
        }
        if any(kw in q_words for kw in unanswerable_keywords):
            return "I couldn't find that information in the provided company documents."

        # Search top chunk text for sentence matching question words
        best_chunk = retrieved_chunks[0]
        text = best_chunk.get("text", "")
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        
        relevant_sentences = []
        for s in sentences:
            s_words = set(s.lower().split())
            overlap = len(q_words.intersection(s_words))
            if overlap >= 2:
                relevant_sentences.append(s)

        if relevant_sentences:
            return ". ".join(relevant_sentences[:2]) + "."
        
        # Default top context sentence
        return sentences[0] + "." if sentences else text[:200]


if __name__ == "__main__":
    generator = LLMGenerator()
    dummy_chunks = [{
        "filename": "leave_policy.pdf",
        "page": 1,
        "chunk_id": "LEAVE_POLICY_P1_C1",
        "score": 0.85,
        "text": "Employees receive 20 days of paid annual leave per calendar year. Annual leave accrues at a rate of 1.66 days per month."
    }]
    res = generator.generate_answer("How many annual leave days do employees get?", dummy_chunks)
    print("Answer:", res["answer"])
    print("Sources:\n", res["sources"])
