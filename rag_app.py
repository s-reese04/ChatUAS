import os
import sys
import time

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# URLs
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

embeddings = OllamaEmbeddings(model="bge-m3")
llm = ChatOllama(model=os.getenv("LLM_MODEL", "qwen2.5:7b"), temperature=0.0, base_url=OLLAMA_URL, keep_alive="5m")

collection_name = "chatuas_qdrant_store"

vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    collection_name=collection_name,
    url=QDRANT_URL
)

retriever = vector_store.as_retriever(search_kwargs={"k": 5})

system_prompt = (
    "Du bist ein präziser Assistent. Beantworte die Frage ausschließlich "
    "auf Basis des folgenden Kontexts: \n\n{context}"
    "Lässt sich die Frage nicht mit den Kontext beantworten, dann sag:"
    "Ich kann dies leider nicht beantworten, bitte melden Sie sich an die Studienberatung"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{question}"),
])

chain = prompt | llm | StrOutputParser()


def rag(question: str) -> dict:
    beforeRetrieve = time.time()
    chunks = retriever.invoke(question)
    afterRetrieve = time.time()

    with open("stats.txt", "a") as s:
        s.write(f"Retrieve Time: {afterRetrieve - beforeRetrieve:.2f} seconds\n")

    context_parts = []
    sources = []

    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(chunk.page_content)

        sources.append({
            "Index": i,
            "Url": chunk.metadata.get("url", "Quelle unbekannt"),
            "Sektion": chunk.metadata.get("section", "Sektion unbekannt"),
            "Seiten_Name": chunk.metadata.get("page_title", "Seiten Name unbekannt"),
            "Datum": chunk.metadata.get("scraped_at", "Kein Datum vorhanden"),
            "Ausschnitt": chunk.page_content[:150],
        })

    context_text = "\n\n".join(context_parts)

    beforeModel = time.time()
    answer = chain.invoke({"context": context_text, "question": question})
    afterModel = time.time()

    with open("stats.txt", "a") as s:
        s.write(f"Model time: {afterModel - beforeModel:.2f} seconds\n")

    return {
        "answer": answer,
        "sources": sources
    }


def print_result(result: dict) -> None:
    print(f"\nAntwort: {result['answer']}\n")
    print("Quellen:")
    for src in result['sources']:
        print(f"[{src['Index']}] Url: {src['Url']} Datum: {src['Datum']}")
        print(f"    \"{src['Ausschnitt']}\"")


def main() -> None:
    if len(sys.argv) > 1:
        print_result(rag(" ".join(sys.argv[1:])))
        return

    print("Willkommen zu ChatUAS. Leere Eingabe beendet das Programm.")

    while True:
        question = input("\nFrage: ").strip()
        if not question:
            break
        print_result(rag(question))


if __name__ == "__main__":
    main()
