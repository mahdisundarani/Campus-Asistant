import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import os
from dotenv import load_dotenv
load_dotenv()
from rag import embeddings, vectorstore

def main():
    query = "Can I change my elective courses"
    print(f"Querying FAISS for: {query}")
    
    emb = embeddings.get_embeddings()
    index = vectorstore.load_index(emb)
    docs = vectorstore.search(index, query, top_k=5)
    
    print(f"Found {len(docs)} chunks.")
    for i, doc in enumerate(docs):
        print(f"\n--- Chunk {i+1} [{doc.metadata.get('source', 'Unknown')}, p.{doc.metadata.get('page', '?')}] ---")
        print(doc.page_content)

if __name__ == "__main__":
    main()
