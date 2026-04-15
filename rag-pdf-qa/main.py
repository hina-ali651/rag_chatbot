import os
import textwrap
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

# Import from their existing local modules
from document_loader import load_document
from rag_engine import RAGEngine

# Suppress HuggingFace/tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

load_dotenv()

app = FastAPI(title="RAG PDF API", description="FastAPI wrapper for local RAG Engine with Gemini")

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all. Change in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Validation
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    # Just a placeholder error so it doesn't crash on boot if env is missing
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=api_key or "DUMMY_KEY")
model = genai.GenerativeModel('gemini-2.5-flash')
engine = RAGEngine()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    role: str
    content: str

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a PDF/TXT/DOCX file, chunks it, and adds it to local ChromaDB."""
    try:
        # Save temp file
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        text = load_document(temp_path)
        
        num_chunks = engine.add_document(text, file.filename)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {"success": True, "message": f"Successfully processed {num_chunks} chunks from {file.filename}."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):
    """Processes a chat request using Gemini and the Vector DB Context."""
    try:
        messages_dict = [{"role": m.role, "text": m.content} for m in request.messages]
        
        # Extract the latest user question
        user_queries = [m.content for m in request.messages if m.role == "user"]
        if not user_queries:
            raise HTTPException(status_code=400, detail="No user message provided.")
            
        latest_question = user_queries[-1]
        
        # Vector Similarity Search
        if engine.collection.count() == 0:
            context = "No documents currently loaded. The user's database is empty."
            chunks = []
        else:
            chunks = engine.query(latest_question, n_results=5)
            context = ""
            for i, chunk in enumerate(chunks):
                context += f"\n[Context Chunk {i+1} | Source: {chunk['source']}]\n"
                context += chunk['text'] + "\n"

        # Build prompt using context and history
        prompt = "You are a professional, helpful assistant answering questions efficiently based *only* on the provided context.\n\n"
        
        if len(request.messages) > 1:
            prompt += "--- Conversation History ---\n"
            for turn in request.messages[:-1]:
                role_label = "User" if turn.role == "user" else "Assistant"
                prompt += f"{role_label}: {turn.content}\n"
            prompt += "\n"
            
        prompt += f"--- Document Context ---\n{context}\n\n"
        prompt += f"--- Current Task / Question ---\nUser: {latest_question}\n\n"
        
        prompt += "Core Instructions:\n"
        prompt += "- Use the facts inside the Document Context to answer.\n"
        prompt += "- If the context does not contain the answer, politely state that you cannot answer based on the provided documents.\n"
        prompt += "- Be clean, highly readable, and concise. Format nicely in markdown.\n"
        
        # Ask Gemini
        response = model.generate_content(prompt)
        answer = response.text.strip()
        
        return ChatResponse(role="assistant", content=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/clear")
async def clear_database():
    """Wipes the entire vector dataset."""
    try:
        engine.clear_database()
        return {"success": True, "message": "Database cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
