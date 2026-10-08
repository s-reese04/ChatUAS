from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Initiate Ollama model and embedding
embeddings = OllamaEmbeddings(model="bge-m3")  # Oder "nomic-embed-text"
llm = ChatOllama(model="qwen2.5:7b", temperature=0.2)

collection_name = "mein_wissensnetz"

vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=collection_name,
        url="http://localhost:6333"
        )

# Pull chunks form Qdrant 
retriever = vector_store.as_retriever(search_kwargs={"k": 5}) # k = How many chunks to pull from Qdrant

system_prompt = (
    "Du bist ein präziser Assistent. Beantworte die Frage ausschließlich "
    "auf Basis des folgenden Kontexts:\n\n{context}"
)

# Gives template for the Chat
SysPrompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{question}"),
])

# Retreive chunks from Qdrant
# Joins all into a single string
def get_context(question: str) -> str:
    docs = retriever.invoke(question)
    return "\n\n".join(doc.page_content for doc in docs)

# Dictionary of Qdrant String and the users question
chain_input = {
    "context": get_context,
    "question": RunnablePassthrough()
    }

# Chain of QDrant String and user input -> System Prommpt -> Model -> Output
rag_chain = chain_input | SysPrompt_template | llm | StrOutputParser()

# Test answer on fixxed question 
frage = "In welcher Programmiersprache wurde Qdrant geschrieben?"
antwort = rag_chain.invoke(frage)

print("Frage:", frage)
print("Antwort:", antwort)
