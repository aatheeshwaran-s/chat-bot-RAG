# RAG Chatbot — Project Specification & Verification Plan

## 1. Goal
Build a Retrieval-Augmented Generation (RAG) chatbot backend to answer user questions using company PDF documents with local Qdrant vector database, SentenceTransformers embeddings, grounded LLM response generation, citations, and abstention behavior.

## 2. Technology Stack
- **Language**: Python 3.12
- **PDF Extraction**: PyMuPDF (`fitz`)
- **Embeddings**: Local `SentenceTransformer` (`BAAI/bge-small-en-v1.5`)
- **Vector DB**: `QdrantClient` in persistent local disk mode (`./data/qdrant`)
- **LLM**: OpenAI API format / Offline Fallback Generator
- **CLI Framework**: Python `argparse`

## 3. Success Criteria Checklist
- [x] PDFs ingested page-by-page preserving page numbers.
- [x] Text split into configurable sliding window chunks.
- [x] Local embeddings generated on CPU.
- [x] Vectors stored in Qdrant with HNSW index & metadata.
- [x] Similarity search returns top-k context.
- [x] Metadata filtering (e.g. `--department HR`) supported.
- [x] Answers strictly grounded with citations (`[filename — Page X]`).
- [x] Unanswerable questions trigger "I don't know" abstention.
- [x] Benchmark test dataset with 10 answerable + 5 unanswerable questions evaluated.
- [x] Chunk size comparison experiment (300, 500, 1000) evaluated.
