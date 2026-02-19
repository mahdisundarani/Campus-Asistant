"""
parser.py — PDF text extraction using pdfplumber.

Extracts text from each page of a PDF and returns a list of dicts with
the text, source filename, and page number.
"""

import os
import pdfplumber


def parse_pdf(filepath: str) -> list[dict]:
    """
    Extract text from a PDF file, page by page.

    Args:
        filepath: Path to the PDF file.

    Returns:
        List of dicts: [{"text": "...", "source": "filename.pdf", "page": 1}, ...]
    """
    pages = []
    filename = os.path.basename(filepath)

    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "text": text.strip(),
                    "source": filename,
                    "page": i + 1,
                })

    return pages


def parse_all_pdfs(docs_dir: str) -> list[dict]:
    """
    Parse all PDF files in a directory.

    Args:
        docs_dir: Path to directory containing PDF files.

    Returns:
        List of dicts with text, source, and page for every page across all PDFs.
    """
    all_pages = []

    for filename in os.listdir(docs_dir):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(docs_dir, filename)
            print(f"  Parsing: {filename}")
            pages = parse_pdf(filepath)
            all_pages.extend(pages)
            print(f"    → {len(pages)} pages extracted")

    return all_pages
