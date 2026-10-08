from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Initiate Ollama model and embedding
embeddings = OllamaEmbeddings(model="bge-m3")  # Oder nomic-embed-text
llm = ChatOllama(model="qwen2.5:7b", temperature=0.2)

# Sample Sentences
sample_docs = [
    Document(
        page_content="Qdrant ist eine in Rust geschriebene Vektordatenbank, die extrem schnell Vektorsuchen durchführen kann."
    ),
    Document(
        page_content="Qwen 2.5 7B ist ein Sprachmodell von Alibaba Cloud mit starker Sprach- und Code-Leistung."
    ),
    Document(
        page_content="RAG erweitert ein Sprachmodell um eine Vektordatenbank, um präzise Antworten aus eigenen Dokumenten zu liefern."
    ),
]

# Generate Text Splitter, chunk_size = How big is a chunk, chunk_overlap = How many chars are overlapped between chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)

# Splits sample_docs into the chunks with the text splitter
chunks = text_splitter.split_documents(sample_docs)

# Save to quadrant
collection_name = "mein_wissensnetz"

vector_store = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    url="http://localhost:6333",
    collection_name=collection_name,
)

print(f"Hochladen von {len(chunks)} Chunks in Qdrant-Collection: {collection_name} erfolgreich!")
