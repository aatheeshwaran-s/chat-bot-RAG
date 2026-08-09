# 🤖 Local RAG Chatbot — Backend Architecture

A simple, local-first **Retrieval-Augmented Generation (RAG) Chatbot** built in Python. This project ingests company policy PDF documents, extracts text with page metadata, splits documents into chunks, generates local vector embeddings using `SentenceTransformers`, indexes vectors into a local `Qdrant` database, performs similarity searches with metadata filtering, and generates grounded answers with exact source citations while strictly refraining from answering out-of-context questions.

---

## 🏗️ Architecture Overview

```text
                  COMPANY PDF DOCUMENTS
                           │
                           ▼
                  PyMuPDF Text Extraction (with Page Numbers)
                           │
                           ▼
                  Sliding Window Chunking (e.g. 500 words, 50 overlap)
                           │
                           ▼
             Embedding Model (BAAI/bge-small-en-v1.5 - Local CPU)
                           │
                           ▼
                  ┌──────────────────┐
                  │     Qdrant       │
                  │  Vector Database │
                  └────────┬─────────┘
                           │
             Cosine Similarity Search (+ Metadata Filter)
                           │
User Question ─────────────┼──────────────► Top-K Relevant Context Chunks
                                                    │
                                                    ▼
                                           LLM Generation Engine
                                                    │
                                                    ▼
                                       Grounded Answer + Citations
                                          or "I don't know"
```

---

## 📁 Folder Structure

```text
rag-chatbot/
│
├── documents/                       # Company PDF documents
│   ├── employee_handbook.pdf
│   ├── leave_policy.pdf
│   ├── refund_policy.pdf
│   ├── remote_work_policy.pdf
│   └── expense_policy.pdf
│
├── app/                             # Core Backend Application
│   ├── __init__.py
│   ├── ingest.py                    # PDF extraction (PyMuPDF) & chunking
│   ├── embeddings.py                # Local SentenceTransformer embeddings wrapper
│   ├── retrieval.py                 # Qdrant vector database storage & search
│   ├── generation.py                # Grounded LLM engine, prompt & citations
│   ├── experiments.py               # Chunk size comparator (300 vs 500 vs 1000)
│   ├── evaluate.py                  # Benchmark metrics runner
│   └── main.py                      # Easy-to-use CLI entrypoint
│
├── data/
│   └── qdrant/                      # Local persistent Qdrant database storage
│
├── tests/
│   └── test_questions.json          # 10 answerable + 5 unanswerable benchmark dataset
│
├── generate_sample_docs.py          # Helper script to create synthetic company PDFs
├── .env                             # Environment configuration (LLM_API_KEY)
├── .gitignore                       # Ignored files (.env, data/, cache)
├── requirements.txt                 # Python dependency declarations
└── README.md                        # Documentation
```

---

## ⚡ Quick Start Guide

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Generate Sample PDFs
```bash
python generate_sample_docs.py
```

### 3. Ingest Documents into Local Qdrant Store
```bash
python -m app.main ingest
```

### 4. Ask Questions via CLI
```bash
python -m app.main query "How many annual leave days do employees get?"
```

#### Metadata Filtered Search:
```bash
python -m app.main query "What is the daily meal allowance?" --department Finance
```

### 5. Interactive Chat Session
```bash
python -m app.main chat
```

### 6. Run Automated Benchmark Evaluation
```bash
python -m app.main evaluate
```

### 7. Run Chunk Size Experiment Comparison
```bash
python -m app.main experiment
```

---

## 📊 Key Features

- **No Docker Required**: Qdrant runs directly on disk inside `./data/qdrant/`.
- **Zero API Costs for Vector Operations**: Embeddings use `BAAI/bge-small-en-v1.5` on CPU.
- **Strict Grounding & Abstention**: Says *"I couldn't find that information in the provided company documents."* when similarity score is low or when asking unanswerable questions (e.g. CEO salary).
- **Exact Citations**: Displays document name, page number, and chunk ID for every answer.
- **Metadata Filtering**: Supports department-level or document-level query filtering.
