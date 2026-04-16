import os
import uuid
import certifi
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from dotenv import load_dotenv
load_dotenv()

# MongoDB Connection String
MONGO_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
# Notice serverSelectionTimeoutMS=2000. This prevents 30-sec freezes natively.
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=2000)
db = client["nexus_rag"]

sessions_collection = db["sessions"]
messages_collection = db["messages"]

# Automatic Local Fallback if your college WiFi or local IP isn't whitelisted in Atlas yet!
mock_sessions = []
mock_messages = []

def ping_db():
    try:
        client.admin.command('ping')
        return True
    except ServerSelectionTimeoutError:
        return False

def init_db():
    pass

def create_session(user_email: str, title: str = "New Chat"):
    session_id = str(uuid.uuid4())
    doc = {
        "id": session_id,
        "user_email": user_email,
        "title": title,
        "created_at": datetime.utcnow()
    }
    
    if ping_db():
        sessions_collection.insert_one(doc)
    else:
        mock_sessions.append(doc)
        
    return {"id": session_id, "title": title}

def get_sessions(user_email: str):
    if ping_db():
        rows = sessions_collection.find({"user_email": user_email}).sort("created_at", -1)
        return [{"id": row["id"], "title": row["title"]} for row in rows]
    else:
        # Sort in memory for correct chat load sequencing locally
        sorted_sessions = sorted([s for s in mock_sessions if s["user_email"] == user_email], key=lambda x: x["created_at"], reverse=True)
        return [{"id": s["id"], "title": s["title"]} for s in sorted_sessions]

def add_message(session_id: str, role: str, content: str):
    doc = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow()
    }
    if ping_db():
        messages_collection.insert_one(doc)
    else:
        mock_messages.append(doc)

def get_messages(session_id: str):
    if ping_db():
        rows = messages_collection.find({"session_id": session_id}).sort("created_at", 1)
        return [{"role": row["role"], "content": row["content"]} for row in rows]
    else:
        sorted_messages = sorted([m for m in mock_messages if m["session_id"] == session_id], key=lambda x: x["created_at"])
        return [{"role": m["role"], "content": m["content"]} for m in sorted_messages]

def update_session_title(session_id: str, new_title: str):
    if ping_db():
        sessions_collection.update_one({"id": session_id}, {"$set": {"title": new_title}})
    else:
        for s in mock_sessions:
            if s["id"] == session_id:
                s["title"] = new_title

init_db()
