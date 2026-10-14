import json
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document


# Initiate Ollama model and embedding
embeddings = OllamaEmbeddings(model="bge-m3")  # Oder nomic-embed-text

chunks = []

# Read from chunks.jsonl
with open("chunks.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        record = json.loads(line)
        text = record.pop("text")
        chunks.append(Document(page_content=text, metadata=record))

# Save to quadrant
collection_name = "chatuas_qdrant_store"

vector_store = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    url="http://localhost:6333",
    collection_name=collection_name,
)

print(f"Hochladen von {len(chunks)} Chunks in Qdrant-Collection: {collection_name} erfolgreich!")
