"""
Module for Hybrid Search combining Lexical Search (BM25) and Semantic Vector Search (Qdrant)
using Reciprocal Rank Fusion (RRF).

Learning Concept:
- Semantic Vector Search catches conceptual meaning ("how much vacation do I get?").
- Lexical BM25 Keyword Search catches exact terms, codes, and numbers ("ERR-4032", "5 days", "85%").
- Reciprocal Rank Fusion (RRF) merges candidate lists by summing inverse ranks:
  score(d) = 1/(k + rank_vector(d)) + 1/(k + rank_bm25(d))
"""

import re
from typing import List, Dict, Any, Optional

try:
    from rank_bm25 import BM25Okapi
    HAS_RANK_BM25 = True
except ImportError:
    HAS_RANK_BM25 = False


def simple_tokenize(text: str) -> List[str]:
    """Basic lowercased word tokenizer for BM25 keyword matching."""
    return re.findall(r'\w+', text.lower())


class BM25SearchEngine:
    """
    In-memory BM25 Keyword Retriever over document text chunks.
    """

    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        self.corpus_tokens = [simple_tokenize(c.get("text", "")) for c in chunks]
        
        if HAS_RANK_BM25 and self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
        else:
            self.bm25 = None

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Executes BM25 keyword search over indexed chunks.
        """
        if not self.chunks:
            return []

        query_tokens = simple_tokenize(query)

        if self.bm25:
            scores = self.bm25.get_scores(query_tokens)
            ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            
            results = []
            for idx in ranked_indices:
                if scores[idx] > 0:  # Only include positive keyword matches
                    chunk_copy = dict(self.chunks[idx])
                    chunk_copy["bm25_score"] = float(scores[idx])
                    results.append(chunk_copy)
            return results
        else:
            # Fallback simple keyword overlap scorer if rank-bm25 is missing
            scored_chunks = []
            q_set = set(query_tokens)
            for idx, (chunk, tokens) in enumerate(zip(self.chunks, self.corpus_tokens)):
                overlap = len(q_set.intersection(set(tokens)))
                if overlap > 0:
                    chunk_copy = dict(chunk)
                    chunk_copy["bm25_score"] = float(overlap)
                    scored_chunks.append(chunk_copy)
            scored_chunks.sort(key=lambda x: x["bm25_score"], reverse=True)
            return scored_chunks[:top_k]


def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    rrf_k: int = 60,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Combines Vector Search results and BM25 Keyword Search results using Reciprocal Rank Fusion (RRF).

    Formula:
      RRF_Score(doc) = 1 / (rrf_k + vector_rank) + 1 / (rrf_k + bm25_rank)

    Args:
        vector_results: Chunks retrieved by Vector Similarity Search
        bm25_results: Chunks retrieved by BM25 Lexical Keyword Search
        rrf_k: RRF smoothing constant (default standard is 60)
        top_k: Number of combined results to return
    """
    doc_scores = {}
    doc_data = {}

    # 1. Process Vector Search ranks (1-indexed)
    for rank, chunk in enumerate(vector_results, 1):
        doc_id = chunk.get("chunk_id") or chunk.get("text")[:50]
        doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))
        if doc_id not in doc_data:
            doc_data[doc_id] = dict(chunk)

    # 2. Process BM25 Keyword Search ranks (1-indexed)
    for rank, chunk in enumerate(bm25_results, 1):
        doc_id = chunk.get("chunk_id") or chunk.get("text")[:50]
        doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank))
        if doc_id not in doc_data:
            doc_data[doc_id] = dict(chunk)

    # 3. Sort documents by combined RRF score descending
    sorted_doc_ids = sorted(doc_scores.keys(), key=lambda d: doc_scores[d], reverse=True)

    fused_results = []
    for doc_id in sorted_doc_ids[:top_k]:
        chunk = doc_data[doc_id]
        chunk["rrf_score"] = round(doc_scores[doc_id], 6)
        chunk["score"] = chunk["rrf_score"]  # Normalize for compatibility
        fused_results.append(chunk)

    return fused_results


class HybridSearchEngine:
    """
    High-level Hybrid Retriever executing Dense Vector Search + BM25 Lexical Search with RRF Fusion.
    """

    def __init__(self, vector_store, embedding_engine, all_chunks: List[Dict[str, Any]]):
        self.vector_store = vector_store
        self.embedding_engine = embedding_engine
        self.bm25_engine = BM25SearchEngine(all_chunks)

    def hybrid_search(self, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Runs vector search and BM25 search, then fuses results with RRF.
        """
        # Vector Search
        q_vector = self.embedding_engine.embed_text(question)
        vector_chunks = self.vector_store.similarity_search(q_vector, top_k=top_k * 2)

        # BM25 Keyword Search
        bm25_chunks = self.bm25_engine.search(question, top_k=top_k * 2)

        # Reciprocal Rank Fusion
        fused_chunks = reciprocal_rank_fusion(vector_chunks, bm25_chunks, top_k=top_k)
        return fused_chunks
