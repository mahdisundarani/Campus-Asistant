"""
chunker.py — Split parsed document pages into smaller text chunks.

Uses LangChain's RecursiveCharacterTextSplitter to create chunks
suitable for embedding and retrieval.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def chunk_documents(pages: list[dict], chunk_size: int = 600, chunk_overlap: int = 100, tags_map: dict = None) -> list[Document]:
    """
    Split parsed pages into smaller chunks with metadata.

    Args:
        pages: List of dicts from parser.py: [{"text": ..., "source": ..., "page": ...}]
        chunk_size: Maximum characters per chunk (default: 600).
        chunk_overlap: Overlap between chunks (default: 100).
        tags_map: Optional dict mapping filenames to tag dicts {department, year, course}.

    Returns:
        List of LangChain Document objects with metadata (source, page, + optional tags).
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
        
        # Resolve tags for this file
        source = page["source"]
        file_tags = (tags_map or {}).get(source, {})

        for chunk in chunks:
            metadata = {
                "source": source,
                "page": page["page"],
            }
            if file_tags.get("department"):
                metadata["department"] = file_tags["department"]
            if file_tags.get("year"):
                metadata["year"] = file_tags["year"]
            if file_tags.get("course"):
                metadata["course"] = file_tags["course"]

            doc = Document(
                page_content=chunk,
                metadata=metadata,
            )
            documents.append(doc)

    print(f"  -> {len(documents)} chunks created from {len(pages)} pages")
    return documents
