"""
Phase 5: Local Embeddings Generator Module.

Uses SentenceTransformers (BAAI/bge-small-en-v1.5 or all-MiniLM-L6-v2) to convert text chunks
and user questions into dense numerical vector representations.

No API keys are required for local embeddings!
"""

from typing import List
from sentence_transformers import SentenceTransformer


class EmbeddingEngine:
    """
    Handles loading the embedding model and generating embedding vectors.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initializes the SentenceTransformer model.

        Args:
            model_name (str): HuggingFace repository ID for embedding model.
                              Default: BAAI/bge-small-en-v1.5 (384 vector dimension)
        """
        self.model_name = model_name
        print(f"Loading embedding model '{model_name}' on CPU...")
        self.model = SentenceTransformer(model_name)
        self.vector_dim = self.model.get_embedding_dimension()
        print(f"Embedding model loaded successfully! Vector Dimension: {self.vector_dim}")

    def embed_text(self, text: str) -> List[float]:
        """
        Generates an embedding vector for a single string query or passage.
        Automatically prepends instruction for BGE embedding models.
        """
        if "bge" in self.model_name.lower() and not text.startswith("Represent this sentence"):
            text = f"Represent this sentence for searching relevant passages: {text}"
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_chunks(self, chunks: List[dict]) -> List[List[float]]:
        """
        Generates embedding vectors for a list of text chunk dictionaries.

        Args:
            chunks (List[dict]): List of chunk dictionaries containing 'text' key.

        Returns:
            List[List[float]]: List of float embedding vectors.
        """
        texts = [chunk["text"] for chunk in chunks]
        vectors = self.model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
        return vectors.tolist()


if __name__ == "__main__":
    # Quick standalone test
    engine = EmbeddingEngine()
    test_vec = engine.embed_text("How many annual leave days do employees receive?")
    print(f"Generated query vector dimension: {len(test_vec)}")
    print(f"Sample vector prefix: {test_vec[:5]}")
