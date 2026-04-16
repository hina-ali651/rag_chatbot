import os
import textwrap
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

from document_loader import load_document
from rag_engine import RAGEngine
import db

os.environ["TOKENIZERS_PARALLELISM"] = "false"
load_dotenv()

app = FastAPI(title="RAG PDF API", description="FastAPI wrapper for local RAG Engine with History")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=api_key or "DUMMY_KEY")
model = genai.GenerativeModel('gemini-2.5-flash')
engine = RAGEngine()

class SessionRequest(BaseModel):
    user_email: str
    title: Optional[str] = "New Chat"

class ChatMessage(BaseModel):
    role: str
    content: str
    
# We will still accept messages for local context, but also session_id to save to DB.
class ChatRequest(BaseModel):
    session_id: str
    user_email: str
    messages: List[ChatMessage]

@app.post("/api/sessions")
async def create_new_session(req: SessionRequest):
    try:
        return db.create_session(req.user_email, req.title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{user_email}")
async def get_user_sessions(user_email: str):
    try:
        return db.get_sessions(user_email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{session_id}")
async def get_session_history(session_id: str):
    try:
        return db.get_messages(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_document(session_id: str = Form(...), file: UploadFile = File(...)):
    try:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        text = load_document(temp_path)
        num_chunks = engine.add_document(text, file.filename, session_id)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {"success": True, "message": f"Successfully processed {num_chunks} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_document(request: ChatRequest):
    try:
        user_queries = [m.content for m in request.messages if m.role == "user"]
        if not user_queries:
            raise HTTPException(status_code=400, detail="No user message provided.")
            
        latest_question = user_queries[-1]
        
        # Save user message to DB
        db.add_message(request.session_id, "user", latest_question)
        
        chunks = engine.query(latest_question, session_id=request.session_id, n_results=5)
        if not chunks:
            context = "No documents loaded. Database is empty."
        else:
            context = ""
            for i, chunk in enumerate(chunks):
                context += f"\n[Chunk {i+1} | Source: {chunk['source']}]\n{chunk['text']}\n"

        prompt = "You are a professional, helpful assistant answering questions efficiently based *only* on the provided context.\n\n"
        
        # Get history from DB instead of strictly from request (for more robust continuity)
        past_messages = db.get_messages(request.session_id)
        # Exclude the very last one we just inserted to avoid duplication in context if we want, or just show all
        if len(past_messages) > 1:
            prompt += "--- Conversation History ---\n"
            # We only send last 6 messages to prevent context overflow
            for turn in past_messages[-7:-1]:
                role_label = "User" if turn["role"] == "user" else "Assistant"
                prompt += f"{role_label}: {turn['content']}\n"
            prompt += "\n"
            
        prompt += f"--- Document Context ---\n{context}\n\n"
        prompt += f"--- Current Task / Question ---\nUser: {latest_question}\n\n"
        prompt += "Core Instructions:\n- Use facts inside Document Context.\n- If context does not contain answer, say so.\n- Be concise, format nicely in markdown.\n"
        
        response = model.generate_content(prompt)
        answer = response.text.strip()
        
        # Generate Title summary if this is the first interaction (only 2 messages in DB so far)
        if len(past_messages) <= 2:
           # Simple auto-title based on user prompt (first 25 characters)
           new_title = latest_question[:25] + "..." if len(latest_question) > 25 else latest_question
           # Update title in MongoDB via db.py
           db.update_session_title(request.session_id, new_title)

        # Save assistant message
        db.add_message(request.session_id, "assistant", answer)
        
        return {"role": "assistant", "content": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
