# Local RAG QA Pipeline with Gemini API

A command-line tool designed to let you securely chat with your distinct documents. It orchestrates a fully local Retrieval-Augmented Generation (RAG) system to ingest documents, securely chunk them, embed semantic meanings, and retrieve context locally. That specific context parameter is then intelligently passed to Google's Gemini API for highly accurate human-readable response generation.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Local%20Vector%20Store-orange.svg)
![Gemini](https://img.shields.io/badge/Gemini-Generative%20AI-blueviolet.svg)
![SentenceTransformers](https://img.shields.io/badge/SentenceTransformers-all--MiniLM--L6--v2-green.svg)

## 🏗 Architecture Overview

1. **Ingestion**: Supports loading `.txt`, `.pdf`, and `.docx` using standard IO parsers (`pdfplumber` and `python-docx`).
2. **Dynamic Chunking**: Uses `langchain-text-splitters` to split incoming document sets into length-aware intersecting chunks to maintain continuity across sentence breaks. *(Context sizing is tightly bound to support strict local model thresholds)*
3. **Local Embedding Computation**: Creates mathematical representation vectors completely localized onto your hardware via `sentence-transformers` using the `all-MiniLM-L6-v2` model. No proprietary private data leaks via Cloud API embedding keys are needed for mapping!
4. **Local Vector Database Hub**: Permanently and freely saves vectorized data states locally utilizing `ChromaDB`.
5. **Distance Retrieval Search**: Executes real-time spatial calculations implementing Cosine Similarity protocols to fetch the Top-5 most relevant chunks relative to your question string.
6. **Bounded Generation Engine**: Automates a smart prompt combining conversational history lists + Isolated chunk context vectors + your active question, strictly telling the **Gemini API** framework to synthesize responses originating exclusively from given data pools.

## ✨ Features
- **Cost-effective API Operations**: Your embedding index runs entirely locally in your RAM/Disk. Only exact snippet references transmit outwards to Gemini Generation tier.
- **Advanced Flow Memory**: Seamlessly remembers the past 5 interactive queries automatically to process conversational follow-up questions beautifully.
- **Built-In Macro Interactions**: Run simple CLI slash-commands like `/summary` and `/topics` to jumpstart analytical observations off newly ingested bulk files instantly.

## 🎓 What I Learned Building This
- **AI Pipeline Decentralization**: Gained strong proficiency managing external data parsing, overlapping contextual chunks, and API generation links explicitly without leaning onto over-abstracted heavy 'magic' platforms entirely.
- **Embedded Matrix Mathematics**: Explored deep understandings associated with unstructured NLP text mappings into mathematical Float formats and evaluating Cosine spatial dimensions mathematically inside DB stores (ChromaDB).
- **Prompt Architectures and Sliding Windows**: Dealt carefully managing systemic limitations related to tokens usage inside model contexts by employing array manipulation 'Sliding Windows' techniques to govern conversational memory buffers successfully avoiding arbitrary length bounds! 
- **Robustness in Error Handlers**: Successfully mapped gracefully recovering Exception loops dealing closely against malformed document schemas (Blank PDFs, Unlinked Word files) preserving the execution engine flawlessly. 

## 🚀 Setup Instructions for Windows

### Prerequisites
- Python 3.9 or higher already added to your `%PATH%` environmental variables.
- An Active Gemini API key (you can generate one via [Google AI Studio](https://aistudio.google.com/)).

### 1. Clone or Extract the Application
Extract the codebase folders to your workspace.

### 2. Form your Virtual Environment (Recommended on Windows)
Open an administrative PowerShell or Terminal inside the repository folder and form an isolated environment:
```shell
python -m venv venv
venv\Scripts\activate
```

### 3. Bootstrap Application Dependencies
Execute standard package installations:
```shell
pip install -r requirements.txt
```
*(Note: Be patient during this step. Initializing machine-learning dependency downloads such as transformer datasets inherently pulls heavy files locally!)*

### 4. Inject Environment Credentials
Make a brand-new file accurately named `.env` locally within root alongside `app.py`. Provide your key directly via:
```text
GEMINI_API_KEY=your_actual_api_key_here
```

### 5. Launch
Start the primary CLI app execution file:
```shell
python app.py
```
Enjoy chatting with your offline documents iteratively! Start by firing `/load`!
