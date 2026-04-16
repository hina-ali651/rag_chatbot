import os
from typing import List, Dict, Any
from pinecone import Pinecone
from langchain_text_splitters import RecursiveCharacterTextSplitter
import google.generativeai as genai

class RAGEngine:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initializes the RAG Engine with Pinecone.
        Embeddings are generated via Gemini API (No local models!), stored in the Cloud natively.
        """
        api_key = os.environ.get("PINECONE_API_KEY")
        index_name = os.environ.get("PINECONE_INDEX_NAME", "rag-pdf-cloud-idx")
        
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
            
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
        
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
            is_separator_regex=False,
        )

    def _get_embedding(self, text: str) -> List[float]:
        # Uses Gemini cloud model directly (sliced to strictly 768 dimensions)
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding'][:768]

    def _get_query_embedding(self, text: str) -> List[float]:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding'][:768]

    def add_document(self, text: str, source_name: str, session_id: str) -> int:
        if not text.strip():
            raise ValueError("Document text is empty.")

        chunks = self.text_splitter.split_text(text)
        if not chunks:
            return 0
        
        vectors = []
        for i, chunk in enumerate(chunks):
            emb = self._get_embedding(chunk)
            vector_id = f"{session_id}_{source_name}_chunk_{i}"
            meta = {
                "source": source_name, 
                "chunk_index": i, 
                "session_id": session_id,
                "text": chunk
            }
            vectors.append((vector_id, emb, meta))
            
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            self.index.upsert(vectors=vectors[i:i + batch_size])
            
        return len(chunks)

    def query(self, question: str, session_id: str, n_results: int = 5) -> List[Dict[str, Any]]:
        query_vector = self._get_query_embedding(question)

        response = self.index.query(
            vector=query_vector,
            top_k=n_results,
            include_metadata=True,
            filter={"session_id": session_id}
        )
        
        retrieved_chunks = []
        for match in response.matches:
            retrieved_chunks.append({
                "text": match.metadata.get("text", ""),
                "source": match.metadata.get("source", "Unknown"),
                "distance": match.score
            })
                
        return retrieved_chunks

    def clear_database(self):
        self.index.delete(delete_all=True)
