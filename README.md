# 🎴 AI Flashcard Generator (LangChain + RAG)

An intelligent flashcard generator powered by **LangChain**, **Ollama (Llama 3.2)**, and Retrieval-Augmented Generation (**RAG**). This application converts educational PDF documents into active-recall flashcard question-and-answer pairs.

---

## 🌟 Key Features

* **PDF Document Parsing**: Uses LangChain's `PyPDFLoader` to extract educational content from PDF files.
* **Intelligent Question Generation**: Uses local LLMs (via Ollama `llama3.2:3b`) with structured prompt constraints to extract active-recall test concepts.
* **Vector Search & RAG**: Splits document content into semantic chunks using `RecursiveCharacterTextSplitter`, embeds them with `HuggingFaceEmbeddings` (`all-MiniLM-L6-v2`), and stores them in a local `Chroma` vector database.
* **Ground-Truth Answering**: Queries the Chroma vector retriever to ensure generated flashcard answers are factual and directly sourced from the uploaded PDF text.
* **Standalone or Flask-Ready**: Export generated cards to text files or serve them seamlessly through a web interface (`templates/` and `static/`).

---

## 🛠️ Tech Stack & Requirements

* **Language**: Python 3.9+
* **LLM Engine**: [Ollama](https://ollama.com/) running `llama3.2:3b`
* **AI & Orchestration Framework**: LangChain (`langchain`, `langchain-community`, `langchain-core`, `langchain-text-splitters`, `langchain-chroma`)
* **Vector Store**: ChromaDB
* **Embeddings**: HuggingFace (`sentence-transformers/all-MiniLM-L6-v2`)
* **Frontend/UI**: HTML, CSS, JavaScript (Flask templating)

---

## 🚀 Installation & Setup

### 1. Prerequisites
Make sure you have [Ollama](https://ollama.com/) installed and running locally. Pull the Llama 3.2 3B model:

```bash
ollama pull llama3.2:3b
