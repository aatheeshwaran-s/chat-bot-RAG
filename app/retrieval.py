"""
Phase 6, 7 & 8: Local Qdrant Vector Database & Retrieval Engine.

This module handles:
1. Connecting to local Qdrant vector database storage (stored on disk in ./data/qdrant).
2. Creating a vector collection named 'company_documents' with HNSW indexing and Cosine distance.
3. Upserting chunks and their embedding vectors with attached payload metadata.
4. Performing Top-K similarity search.
5. Applying metadata filtering (e.g. filter search results by department or document_type).
"""

import os
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

_GLOBAL_QDRANT_STORE = None

def get_qdrant_store(storage_path: str = "./data/qdrant", collection_name: str = "company_documents") -> "QdrantVectorStore":
    global _GLOBAL_QDRANT_STORE
    if _GLOBAL_QDRANT_STORE is None:
        _GLOBAL_QDRANT_STORE = QdrantVectorStore(storage_path=storage_path, collection_name=collection_name)
    return _GLOBAL_QDRANT_STORE


class QdrantVectorStore:
    """
    Wrapper for local Qdrant Vector Store operations.
    """

    def __init__(
        self, 
        storage_path: str = "./data/qdrant", 
        collection_name: str = "company_documents"
    ):
        """
        Initializes local Qdrant client operating on local disk storage.
        """
        self.storage_path = os.path.abspath(storage_path)
        os.makedirs(self.storage_path, exist_ok=True)
        self.collection_name = collection_name
        
        print(f"Connecting to Qdrant local database at: {self.storage_path}")
        self.client = QdrantClient(path=self.storage_path)

    def create_collection(self, vector_size: int, distance: Distance = Distance.COSINE):
        """
        Creates or recreates the target collection with HNSW indexing and specified vector dimensions.
        """
        # Recreate collection to ensure clean state during ingestion
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance)
        )
        print(f"Collection '{self.collection_name}' initialized with vector size {vector_size}.")

    def index_chunks(self, chunks: List[Dict[str, Any]], vectors: List[List[float]]):
        """
        Upserts document chunks and their embedding vectors into Qdrant.

        Args:
            chunks (List[Dict]): Chunk objects containing text and metadata.
            vectors (List[List[float]]): Corresponding embedding vectors.
        """
        points = []
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            payload = {
                "chunk_id": chunk.get("chunk_id", f"chunk_{idx}"),
                "document_id": chunk.get("document_id", ""),
                "filename": chunk.get("filename", ""),
                "page": chunk.get("page", 1),
                "department": chunk.get("department", "General"),
                "document_type": chunk.get("document_type", "document"),
                "text": chunk.get("text", "")
            }
            points.append(
                PointStruct(
                    id=idx + 1,  # Simple integer point ID
                    vector=vector,
                    payload=payload
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Successfully indexed {len(points)} chunk vectors into Qdrant '{self.collection_name}'.")

    def similarity_search(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        filter_department: Optional[str] = None,
        filter_filename: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes Cosine similarity search in Qdrant to find top_k relevant text chunks.
        """
        must_filters = []
        
        if filter_department:
            must_filters.append(
                FieldCondition(
                    key="department",
                    match=MatchValue(value=filter_department)
                )
            )
        
        if filter_filename:
            must_filters.append(
                FieldCondition(
                    key="filename",
                    match=MatchValue(value=filter_filename)
                )
            )

        query_filter = Filter(must=must_filters) if must_filters else None

        try:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter
            )
        except AttributeError:
            res = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter
            )
            search_results = res.points

        retrieved_chunks = []
        for hit in search_results:
            item = dict(hit.payload)
            item["score"] = round(hit.score, 4)
            retrieved_chunks.append(item)

        return retrieved_chunks


if __name__ == "__main__":
    store = get_qdrant_store()
    print("Qdrant store initialized successfully.")
