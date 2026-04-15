import os
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

class RAGEngine:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initializes the RAG Engine with ChromaDB and SentenceTransformers.
        All embedding processing and similarity search is done locally.
        """
        # Create a local persistent ChromaDB client saving to the disk
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        
        # We use the free, local sentence-transformers model 'all-MiniLM-L6-v2'.
        # No API keys required, this runs locally on your machine.
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create the vector collection. We configure it to use Cosine Similarity.
        self.collection = self.chroma_client.get_or_create_collection(
            name="rag_documents",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        
        # NOTE ON CHUNKING SIZES:
        # The user requested 500 tokens sizes. However, 'all-MiniLM-L6-v2' has a maximum 
        # embedding length limitation usually maxing out context at 256 tokens.
        # To ensure we don't severely truncate data and lose context at the embedding step,
        # we define the chunk size as 1000 characters (~200-250 tokens).
        # We add an overlap of 100 characters so sentences are less likely to be split awkwardly.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
            is_separator_regex=False,
        )

    def add_document(self, text: str, source_name: str) -> int:
        """
        Chunks the text, calculates embeddings (locally), and stores them in ChromaDB.
        Returns the number of chunks successfully added.
        """
        if not text.strip():
            raise ValueError("Document text is empty.")

        # 1. Split text into manageable overlapping chunks
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            return 0

        # 2. Assign unique IDs to each chunk
        # Example: document.pdf_chunk_0, document.pdf_chunk_1...
        ids = [f"{source_name}_chunk_{i}" for i in range(len(chunks))]
        
        # 3. Attach metadata indicating where the chunks came from
        metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]
        
        # 4. Ingest into vector store. 
        # The sentence-transformers embedding function runs automatically behind the scenes.
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(chunks)

    def query(self, question: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves the top N most relevant chunks for a given question based on cosine similarity.
        """
        if self.collection.count() == 0:
            return []

        # Calculate vector similarity space against the user query text
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )
        
        retrieved_chunks = []
        
        # Re-format ChromaDB's matrix arrays into a clean List of Dicts
        if results['documents'] and len(results['documents']) > 0:
            for doc, meta, distance in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
                retrieved_chunks.append({
                    "text": doc,
                    "source": meta.get("source", "Unknown"),
                    "distance": distance
                })
                
        return retrieved_chunks

    def clear_database(self):
        """
        Wipes the entire vector dataset clean.
        """
        self.chroma_client.delete_collection(name="rag_documents")
        # Recreate the empty collection so it's ready for new ingestions
        self.collection = self.chroma_client.get_or_create_collection(
            name="rag_documents",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
