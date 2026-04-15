import os
import sys
import textwrap
import warnings

# Suppress Google Generative AI deprecation and HuggingFace warnings for clean CLI output
warnings.filterwarnings("ignore")

import google.generativeai as genai
from dotenv import load_dotenv

from document_loader import load_document
from rag_engine import RAGEngine

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Try loading .env file (safely fails if no .env exists and assumes system env)
load_dotenv()

class RAGChatApp:
    def __init__(self):
        """
        Initializes the CLI App, Gemini SDK configuration, and conversation memory.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("❌ Error: GEMINI_API_KEY value is missing.")
            print("Please create a .env file with 'GEMINI_API_KEY=your_key' or set it as a system environment variable.")
            sys.exit(1)
            
        genai.configure(api_key=api_key)
        
        # 'gemini-1.5-flash' is perfect for this: extremely fast and free-tier generous
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        print("⏳ Initializing Local Engine & Embeddings (Please wait...)")
        self.engine = RAGEngine()
        
        # Conversation memory tracks lists of dicts: {"role": "user"/"assistant", "text": "..."}
        self.history = []
        self.max_history = 5 # Remembers the last 5 Q&A pairs (10 entries total)
        
    def _print_help(self):
        """Displays available commands in the CLI."""
        commands = """
        ---------------------------------------------------------
        Available Commands:
          /help     - Show this help message
          /load     - Ingest a document (prompts for file path)
          /summary  - Let the AI summarize the loaded documents
          /topics   - Ask the AI to extract main topics into bullet points
          /clear    - Delete vector database and conversation history
          /exit     - Exit the application gracefully
        ---------------------------------------------------------
        """
        print(textwrap.dedent(commands))

    def _get_context_from_chunks(self, chunks) -> str:
        """Packs the visually isolated text chunks into a unified String for the LLM prompt."""
        context = ""
        for i, chunk in enumerate(chunks):
            context += f"\n[Context Chunk {i+1} | Source: {chunk['source']}]\n"
            context += chunk['text'] + "\n"
        return context

    def _format_prompt(self, question: str, context: str) -> str:
        """Builds a structured prompt merging System Instructions, History, Context, and Current Query."""
        prompt = "You are a professional, helpful assistant answering questions efficiently based *only* on the provided context.\n\n"
        
        # 1. Inject Conversation Memory Context
        if self.history:
            prompt += "--- Conversation History ---\n"
            for turn in self.history:
                role = "User" if turn["role"] == "user" else "Assistant"
                prompt += f"{role}: {turn['text']}\n"
            prompt += "\n"
            
        # 2. Inject Vector Retrieved Context
        prompt += f"--- Document Context ---\n{context}\n\n"
        
        # 3. Current Question
        prompt += f"--- Current Task / Question ---\nUser: {question}\n\n"
        
        # 4. Strict instruction bounding
        prompt += "Core Instructions:\n"
        prompt += "- Use the facts inside the Document Context to answer.\n"
        prompt += "- Maintain the conversational thread shown in the History if applicable.\n"
        prompt += "- If the context does not contain the answer, politely state that you cannot answer based on the provided documents.\n"
        prompt += "- Be clean, highly readable, and concise.\n"
        prompt += "Assistant Response: "
        
        return prompt

    def handle_load(self):
        """Flow for manually loading a specified document interactively into ChromaDB."""
        file_path = input("\nEnter file path (TXT, PDF, DOCX): ").strip()
        
        # Auto-remove quotation marks if user dragged-and-dropped file into terminal
        file_path = file_path.strip("'\"")
        
        if not os.path.exists(file_path):
            print(f"❌ Error: Cannot find file at path '{file_path}'. Try again.")
            return
            
        try:
            print(f"📄 Extracting text from {os.path.basename(file_path)}...")
            text = load_document(file_path)
            
            print("🔪 Chunking text and generating local vector embeddings...")
            filename = os.path.basename(file_path)
            num_chunks = self.engine.add_document(text, filename)
            
            print(f"✅ Success! Injected {num_chunks} vector chunks into local database.")
        except Exception as e:
            print(f"❌ Document load failed: {e}")

    def generate_answer(self, question: str):
        """Unified orchestrator to search, wrap context, prompt Gemini, print results, and log memory."""
        # Standardize fallback scenario strings
        if self.engine.collection.count() == 0:
            print("⚠️ Warning: Your Vector DB is empty. Answering strictly using Gemini's base knowledge.")
            context = "No documents currently loaded. The user's database is empty."
            chunks = []
        else:
            # Vector Search: Query local DB to get top 5 chunks
            chunks = self.engine.query(question, n_results=5)
            context = self._get_context_from_chunks(chunks)

        # Forge structural Prompt
        prompt = self._format_prompt(question, context)
        
        try:
            # Query Gemini API via SDK
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            
            # Print aesthetics
            print("\n" + "="*60)
            print("🤖 Assistant:\n")
            print(answer)
            print("="*60)
            
            # Optionally print citation sources to increase pipeline trust
            if chunks:
                print("\nSources accessed for this answer:")
                sources = set([c['source'] for c in chunks])
                for s in sources:
                    print(f" → {s}")
            print()
            
            # Record Interaction for follow up memory
            self.history.append({"role": "user", "text": question})
            self.history.append({"role": "assistant", "text": answer})
            
            # Enforce max bounds on memory (oldest items slide out)
            if len(self.history) > (self.max_history * 2):
                self.history = self.history[-(self.max_history * 2):]
                
        except Exception as e:
            print(f"❌ Error during API payload generation: {e}")

    def run(self):
        """Infinite app lifecycle loop listening for commands or questions."""
        print("\n" + "✨" * 30)
        print("🚀 Welcome to Local RAG CLI (Powered by Gemini API)")
        print("✨" * 30)
        
        self._print_help()
        
        while True:
            try:
                user_input = input("\nQuery / Command > ").strip()
                
                # Check for empty string return gaps
                if not user_input:
                    continue
                    
                # CLI Routing Logic
                if user_input.startswith('/'):
                    command = user_input.lower()
                    
                    if command == '/help':
                        self._print_help()
                        
                    elif command == '/load':
                        self.handle_load()
                        
                    elif command == '/clear':
                        self.engine.clear_database()
                        self.history.clear()
                        print("🗑️ Vector Database and Conversation Memory have been fully cleared.")
                        
                    elif command == '/summary':
                        print("⏳ Extracting contextual summaries...")
                        self.generate_answer("Please provide a comprehensive summary of the loaded documents.")
                        
                    elif command == '/topics':
                        print("⏳ Analyzing themes...")
                        self.generate_answer("What are the main topics or themes discussed in the loaded documents? List them as concise bullet points.")
                        
                    elif command == '/exit':
                        print("👋 Ending session. Goodbye!")
                        break
                    else:
                        print(f"⚠️ Unknown command '{command}'. Type /help to see all options.")
                        
                else:
                    # Anything not starting with '/' is treated as a context conversation query
                    self.generate_answer(user_input)
                    
            except KeyboardInterrupt:
                # Catching Ctrl+C exits gracefully
                print("\nUse /exit to quit properly, or press Ctrl+C again to force quit.")
            except Exception as e:
                print(f"❌ An unexpected application error occurred: {e}")

if __name__ == "__main__":
    app = RAGChatApp()
    app.run()
