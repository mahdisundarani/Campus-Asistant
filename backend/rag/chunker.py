"""
chunker.py — Split parsed document pages into smaller text chunks.

Uses LangChain's RecursiveCharacterTextSplitter to create chunks
suitable for embedding and retrieval.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def chunk_documents(pages: list[dict], chunk_size: int = 600, chunk_overlap: int = 100) -> list[Document]:
    """
    Split parsed pages into smaller chunks with metadata.

    Args:
        pages: List of dicts from parser.py: [{"text": ..., "source": ..., "page": ...}]
        chunk_size: Maximum characters per chunk (default: 600).
        chunk_overlap: Overlap between chunks (default: 100).

    Returns:
        List of LangChain Document objects with metadata (source, page).
    """
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    documents = []

    for page in pages:
        chunks = splitter.split_text(page["text"])
        for chunk in chunks:
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": page["source"],
                    "page": page["page"],
                },
            )
            documents.append(doc)

    print(f"  -> {len(documents)} chunks created from {len(pages)} pages")
    return documents
