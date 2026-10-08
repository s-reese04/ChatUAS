# ChatUAS
![University](https://img.shields.io/badge/University-Frankfurt%20UAS-008ec8)
![Ollama](https://img.shields.io/badge/Ollama-fff?logo=ollama&logoColor=000)

Chatbot Application for Questions regarding the Websites of the Frankfurt University of Applied Sciences
- https://www.frankfurt-university.de/
- https://asta-fra-uas.de/

## Table of Contents
- [Overview](#overview)
- [File Structure](#file-structure)


## Overview
ChatUAS is a Chatbot Application that uses [LangChain](https://github.com/langchain-ai/langchain) for RAG.
It uses the Qwen3.5:7b model that is hosted locally via [Ollama](https://github.com/ollama/ollama).
ChatUAS uses [QDrant](https://github.com/qdrant/qdrant) as a Vector Database to hold embeddings of all Sentences within the websites https://www.frankfurt-university.de/ and https://asta-fra-uas.de/ .
Any Prompts posed to ChatUAS are processed in steps:
- Retrieve "close" Chunks/Embeddings from QDrant
- Merge them into a single sentence, that is inserted before the UserPrompt
- Add the SystemPrompt
- Process the final prompt with the Model
- Output the given answer

## File Structure
- README.md
- rag_app.py -- performs rag on the local model
- setUp_Qdrant.py -- initializes the Qdrant DB with sentences
- start_ChatUAS.sh -- starts the Qdrant -> calls setUp_Qdrant.py -> rag_app.py
