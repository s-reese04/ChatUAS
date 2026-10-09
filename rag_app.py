from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Initiate Ollama model and embedding
embeddings = OllamaEmbeddings(model="bge-m3")
llm = ChatOllama(model="qwen2.5:7b", temperature=0.2)

collection_name = "chatuas_qdrant_store"

vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=collection_name,
        url="http://localhost:6333"
        )

system_prompt = (
        "Du bist ein präziser Assistent. Beantworte die Frage ausschließlich "
        "auf Basis des folgenden Kontexts: \n\n{context}"
        )


def rag(question: str) -> dict:
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    chunks = retriever.invoke(question)

    context_parts = []
    sources = []

    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(chunk.page_content)

        sources.append({
            "index": i,
            "source": chunk.metadata.get("source", chunk.metadata.get("quelle", "Unbekannte Quelle")),
            "page": chunk.metadata.get("page", chunk.metadata.get("seite", "N/A")),
            "snippet": chunk.page_content[:150] + "..."  
        })

    context_text = "\n\n".join(context_parts)
 
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
    ])

    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context_text, "question": question})

    return {
        "answer": answer,
        "sources": sources
    }

if __name__ == "__main__":
    result = rag("In welcher Programmiersprache wurde Qdrant geschrieben?")

    print(f"Antwort: {result["answer"]}")
    print("Sources:")
    for src in result["sources"]:
        print(f"[{src['index']}] Datei: {src['source']} (Seite {src['page']})")
        print(f"    Ausschnitt: \"{src['snippet']}\"")
