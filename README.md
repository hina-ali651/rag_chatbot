# 📄 Nexus RAG – PDF Intelligence Chatbot

**Nexus RAG** is a full-stack AI-powered document assistant that lets users upload PDF files and have intelligent, context-aware conversations with their content. Built on Retrieval-Augmented Generation (RAG) architecture, it semantically searches your document and answers questions using Google Gemini LLM — no hallucinations, only answers from your actual document.

🔗 **Live Demo:** [rag-chatbot-seven-theta.vercel.app](https://rag-chatbot-seven-theta.vercel.app)

---

## 🎥 Demo
[![Watch Demo](https://img.youtube.com/vi/SwshNk5FhVE/0.jpg)](https://youtu.be/SwshNk5FhVE)

---

## 🧠 Features

- 📂 Upload any PDF and instantly chat with its content
- 🔍 Semantic search powered by Pinecone vector database
- 🤖 Google Gemini LLM for accurate, document-grounded answers
- 🔐 Secure authentication with NextAuth.js + Google OAuth
- 💾 Chat history stored in MongoDB
- 🧩 RAG architecture — answers only from your document, no hallucinations
- ⚡ Separate frontend & backend deployed on Vercel

---

## 🏗️ Architecture

```
User uploads PDF
      ↓
PDF is chunked & converted to embeddings
      ↓
Embeddings stored in Pinecone vector DB
      ↓
User asks a question
      ↓
Relevant chunks retrieved from Pinecone
      ↓
Google Gemini generates answer from chunks
      ↓
Answer + Chat history saved in MongoDB
```

---

## 🛠️ Tech Stack

| Layer           | Technology                 |
|-----------------|----------------------------|
| Frontend        | Next.js, TypeScript        |
| Backend         | Python                     |
| LLM             | Google Gemini              |
| Vector Database | Pinecone                   |
| Database        | MongoDB                    |
| Auth            | NextAuth.js + Google OAuth |
| Deploy          | Vercel                     |

---

## 🚀 Getting Started

```bash
git clone https://github.com/hina-ali651/rag_chatbot.git
cd rag_chatbot

# Frontend
cd rag-pdf-web
npm install
cp .env.example .env.local
npm run dev

# Backend
cd ../rag-pdf-qa
pip install -r requirements.txt
python main.py
```

---

## 📌 Environment Variables

### Frontend `.env.local`

```env
NEXTAUTH_SECRET=your_secret
NEXTAUTH_URL=https://your-frontend.vercel.app
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MONGODB_URI=your_mongodb_uri
```

### Backend `.env`

```env
GEMINI_API_KEY=your_gemini_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=your_index_name
```
