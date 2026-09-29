"""
Module for Second-Pass Reranking (Cross-Encoder), Query Rewriting & HyDE.

Learning Concepts:
1. Reranking (Cross-Encoder):
   First-pass (Vector/Hybrid) retrieves top candidates (e.g. top-10) fast.
   Second-pass (Cross-Encoder) evaluates query + text joint attention for deep relevance, pushing the best result to #1.
2. Query Rewriting:
   Strips unnecessary filler phrases from user questions ("Can you tell me...", "Please explain...").
3. HyDE (Hypothetical Document Embeddings):
   Generates a hypothetical answer passage first, then uses that passage for vector search instead of raw question.
"""

from typing import List, Dict, Any

try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False


class CrossEncoderReranker:
    """
    Reranks initial retrieved chunks using a Cross-Encoder scoring model.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        if HAS_CROSS_ENCODER:
            try:
                print(f"Loading Cross-Encoder reranker model: {model_name}...")
                self.model = CrossEncoder(model_name)
            except Exception as e:
                print(f"Warning: Could not load CrossEncoder model ({e}). Using heuristic reranker fallback.")

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate chunks for a given query and returns top_k.
        """
        if not chunks:
            return []

        if self.model:
            # Pair query with each chunk's text
            pairs = [[query, chunk.get("text", "")] for chunk in chunks]
            scores = self.model.predict(pairs)

            ranked_chunks = []
            for chunk, score in zip(chunks, scores):
                c_copy = dict(chunk)
                c_copy["cross_encoder_score"] = float(score)
                c_copy["score"] = float(score)
                ranked_chunks.append(c_copy)

            ranked_chunks.sort(key=lambda x: x["cross_encoder_score"], reverse=True)
            return ranked_chunks[:top_k]
        else:
            # Simple heuristic reranker fallback: term overlap + initial rank boost
            q_words = set(query.lower().split())
            scored = []
            for idx, c in enumerate(chunks):
                text_words = set(c.get("text", "").lower().split())
                overlap = len(q_words.intersection(text_words))
                # Combine initial rank position and term match
                composite_score = overlap * 2.0 + (len(chunks) - idx) * 0.5
                c_copy = dict(c)
                c_copy["cross_encoder_score"] = round(composite_score, 2)
                scored.append(c_copy)
            scored.sort(key=lambda x: x["cross_encoder_score"], reverse=True)
            return scored[:top_k]


def rewrite_query(query: str) -> str:
    """
    Simple rule-based Query Rewriting to clean up messy user inputs.
    Strips conversational filler phrases to boost search precision.
    """
    fillers = [
        "can you please tell me",
        "could you explain to me",
        "i want to know",
        "please let me know",
        "tell me about",
        "what is the policy on",
        "do you know"
    ]
    cleaned = query.strip()
    lower = cleaned.lower()
    for filler in fillers:
        if lower.startswith(filler):
            cleaned = cleaned[len(filler):].strip(" ?,.")
            break
    return cleaned if cleaned else query


def generate_hyde_query(query: str) -> str:
    """
    Hypothetical Document Embeddings (HyDE) helper.
    Transforms user question into a hypothetical answer clause for search matching.
    """
    cleaned = rewrite_query(query)
    return f"The official policy states regarding {cleaned}:"
