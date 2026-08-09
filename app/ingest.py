"""
Phase 2 & 3: PDF Document Text Extraction and Chunking Module.

This module is responsible for:
1. Extracting text from PDF files using PyMuPDF (fitz) page-by-page.
2. Splitting the text into smaller chunks with controllable chunk size and overlap.
3. Attaching rich metadata (filename, page number, chunk ID, department, etc.) for citations and filtering.
"""

import os
import glob
import pymupdf as fitz  # PyMuPDF


def extract_text_from_pdf(filepath: str) -> list[dict]:
    """
    Extracts text page by page from a single PDF document.

    Args:
        filepath (str): Absolute or relative path to the PDF file.

    Returns:
        list[dict]: List of page dictionaries, each containing:
            - filename: Name of the PDF file
            - page: 1-indexed page number
            - text: Extracted plain text content of that page
    """
    filename = os.path.basename(filepath)
    pages = []

    # Open PDF document with PyMuPDF
    doc = fitz.open(filepath)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text").strip()

        if text:  # Ignore completely empty pages
            pages.append({
                "filename": filename,
                "page": page_num + 1,  # 1-indexed page number for human readability
                "text": text
            })

    doc.close()
    return pages


def derive_metadata_from_filename(filename: str) -> dict:
    """
    Helper function to infer metadata (department, document_type) from file names.
    This enables metadata filtering in Qdrant vector search.
    """
    lower = filename.lower()
    
    # Ingest metadata inference rules
    department = "General"
    doc_type = "document"

    if "leave" in lower or "handbook" in lower:
        department = "HR"
        doc_type = "policy" if "leave" in lower else "handbook"
    elif "refund" in lower:
        department = "Customer Support"
        doc_type = "policy"
    elif "remote" in lower:
        department = "Operations"
        doc_type = "policy"
    elif "expense" in lower:
        department = "Finance"
        doc_type = "policy"

    return {
        "department": department,
        "document_type": doc_type
    }


def chunk_document_pages(
    pages: list[dict], 
    chunk_size: int = 500, 
    chunk_overlap: int = 50
) -> list[dict]:
    """
    Splits page-level text into smaller overlapping chunks.

    Args:
        pages (list[dict]): Page items extracted from PDF.
        chunk_size (int): Target maximum number of words per chunk.
        chunk_overlap (int): Number of overlapping words between consecutive chunks.

    Returns:
        list[dict]: List of chunk dictionaries ready for embedding and vector indexing.
    """
    chunks = []
    
    for page_info in pages:
        filename = page_info["filename"]
        page_number = page_info["page"]
        full_text = page_info["text"]

        # Split text into words for clean sliding window chunking
        words = full_text.split()
        if not words:
            continue

        doc_prefix = os.path.splitext(filename)[0].upper().replace(" ", "_").replace("-", "_")
        chunk_index = 1
        
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            # Unique chunk identifier, e.g., LEAVE_POLICY_P1_C1
            chunk_id = f"{doc_prefix}_P{page_number}_C{chunk_index}"
            
            meta = derive_metadata_from_filename(filename)

            chunks.append({
                "chunk_id": chunk_id,
                "document_id": filename,
                "filename": filename,
                "page": page_number,
                "department": meta["department"],
                "document_type": meta["document_type"],
                "text": chunk_text,
                "word_count": len(chunk_words)
            })

            chunk_index += 1
            
            # Advance start window by (chunk_size - chunk_overlap)
            step = chunk_size - chunk_overlap
            if step <= 0:
                step = 1
            start += step

    return chunks


def process_all_documents_in_folder(
    folder_path: str, 
    chunk_size: int = 500, 
    chunk_overlap: int = 50
) -> list[dict]:
    """
    Scans a folder for all PDF files, extracts page text, and splits into chunks.
    """
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    all_chunks = []

    print(f"Found {len(pdf_files)} PDF documents in '{folder_path}'")

    for pdf_path in sorted(pdf_files):
        print(f"  Extracting text from: {os.path.basename(pdf_path)}...")
        pages = extract_text_from_pdf(pdf_path)
        chunks = chunk_document_pages(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        print(f"  -> Generated {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
        all_chunks.extend(chunks)

    return all_chunks


if __name__ == "__main__":
    # Test script standalone execution
    docs_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documents")
    if os.path.exists(docs_folder):
        result_chunks = process_all_documents_in_folder(docs_folder)
        print(f"\nTotal chunks produced: {len(result_chunks)}")
        if result_chunks:
            print("\nSample Chunk 1:")
            print(result_chunks[0])
