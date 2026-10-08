from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. Embedding-Modell & LLM aus Ollama laden
embeddings = OllamaEmbeddings(model="bge-m3")  # Oder "nomic-embed-text"
llm = ChatOllama(model="qwen2.5:7b", temperature=0.2)

# 2. Beispiel-Dokumente vorbereiten
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

# 3. Dokumente in kleinere Chunks zerlegen
text_splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=30)
chunks = text_splitter.split_documents(sample_docs)

# 4. In Qdrant speichern
collection_name = "mein_wissensnetz"
vector_store = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    url="http://localhost:6333",
    collection_name=collection_name,
)

# 5. RAG Chain mit LCEL aufbauen
retriever = vector_store.as_retriever(search_kwargs={"k": 2})

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

system_prompt = (
    "Du bist ein präziser Assistent. Beantworte die Frage ausschließlich "
    "auf Basis des folgenden Kontexts:\n\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{question}"),
])

# LCEL Pipeline: Context holen -> Prompt füllen -> LLM -> Text-Antwort
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 6. Testabfrage durchführen
frage = "In welcher Programmiersprache wurde Qdrant geschrieben?"
antwort = rag_chain.invoke(frage)

print("Frage:", frage)
print("Antwort:", antwort)
