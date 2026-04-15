"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, UploadCloud, Loader2, Bot, User, CheckCircle2, AlertCircle } from "lucide-react";

type Message = {
    role: "user" | "assistant";
    content: string;
};

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([
        { role: "assistant", content: "Hello! I am your AI assistant. Upload a document to start a conversation with your data." }
    ]);
    const [input, setInput] = useState("");
    const [isUploading, setIsUploading] = useState(false);
    const [isThinking, setIsThinking] = useState(false);
    const [uploadStatus, setUploadStatus] = useState<{ message: string; isError: boolean } | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isThinking]);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        setUploadStatus(null);
        
        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("http://127.0.0.1:8000/api/upload", {
                method: "POST",
                body: formData,
            });
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.detail || data.error || "Upload failed");
            
            setUploadStatus({ message: data.message || "File uploaded and processed!", isError: false });
        } catch (err: any) {
            setUploadStatus({ message: err.message, isError: true });
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleChat = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isThinking) return;

        const userMessage = input.trim();
        setInput("");
        
        const newMessages: Message[] = [...messages, { role: "user", content: userMessage }];
        setMessages(newMessages);
        setIsThinking(true);

        try {
            const res = await fetch("http://127.0.0.1:8000/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ messages: newMessages }),
            });
            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || data.error || "Failed to fetch response");

            setMessages([...newMessages, { role: "assistant", content: data.content }]);
        } catch (err: any) {
            setMessages([...newMessages, { role: "assistant", content: `❌ Error: ${err.message}` }]);
        } finally {
            setIsThinking(false);
        }
    };

    return (
        <div className="flex justify-center items-center h-screen w-full px-4 sm:px-8 py-8 overflow-hidden pointer-events-none relative z-10">
            {/* Main Application Container */}
            <main className="w-full max-w-6xl h-full flex flex-col md:flex-row gap-6 pointer-events-auto">
                
                {/* Sidebar area */}
                <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className="w-full md:w-1/3 max-w-sm flex flex-col gap-6"
                >
                    {/* Brand Card */}
                    <div className="glass-panel rounded-3xl p-8 flex flex-col justify-center items-start shadow-2xl relative overflow-hidden group">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 rounded-full blur-3xl -translate-y-12 translate-x-12 group-hover:bg-primary/30 transition-colors duration-500"></div>
                        <h1 className="text-3xl font-black tracking-tight mb-2 bg-gradient-to-br from-white to-primary/60 bg-clip-text text-transparent">Nexus RAG</h1>
                        <p className="text-muted-foreground text-sm leading-relaxed">Turn any PDF document into an interactive, conversational knowledge base.</p>
                    </div>

                    {/* Upload Card */}
                    <div className="glass-panel rounded-3xl p-6 flex flex-col grow shadow-xl relative overflow-hidden">
                        <h2 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
                            <UploadCloud className="w-5 h-5 text-primary" />
                            Data Source
                        </h2>
                        
                        <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-white/10 hover:border-primary/50 transition-colors rounded-2xl bg-white/5 relative cursor-pointer group"
                             onClick={() => fileInputRef.current?.click()}>
                            <input 
                                type="file" 
                                className="hidden" 
                                accept="application/pdf" 
                                onChange={handleUpload}
                                ref={fileInputRef}
                            />
                            {isUploading ? (
                                <div className="flex flex-col items-center gap-4">
                                    <Loader2 className="w-8 h-8 text-primary animate-spin" />
                                    <p className="text-sm text-muted-foreground font-medium">Processing Document...</p>
                                </div>
                            ) : (
                                <div className="text-center p-6 flex flex-col items-center gap-3">
                                    <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                                        <UploadCloud className="w-6 h-6 text-primary" />
                                    </div>
                                    <p className="text-sm font-medium text-white/80">Click to upload PDF</p>
                                    <p className="text-xs text-muted-foreground">Extracts context via embeddings</p>
                                </div>
                            )}
                        </div>

                        {uploadStatus && (
                            <motion.div 
                                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                className={`mt-4 p-3 rounded-xl text-sm flex items-start gap-2 ${uploadStatus.isError ? 'bg-destructive/20 text-destructive-foreground border border-destructive/30' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}
                            >
                                {uploadStatus.isError ? <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" /> : <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />}
                                <span>{uploadStatus.message}</span>
                            </motion.div>
                        )}
                    </div>
                </motion.div>

                {/* Chat Area */}
                <motion.div 
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
                    className="flex-1 glass-panel rounded-3xl flex flex-col overflow-hidden shadow-2xl border border-white/5"
                >
                    <div className="flex-1 overflow-y-auto p-4 sm:p-6 sm:px-8 space-y-6">
                        <AnimatePresence initial={false}>
                            {messages.map((msg, i) => (
                                <motion.div 
                                    key={i}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`flex items-start gap-3 sm:gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                                >
                                    <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center shrink-0 shadow-inner ${msg.role === 'assistant' ? 'bg-primary/20 border border-primary/30 text-primary' : 'bg-white/10 border border-white/20 text-white'}`}>
                                        {msg.role === 'assistant' ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
                                    </div>
                                    <div className={`max-w-[85%] rounded-2xl p-4 shadow-sm text-[15px] leading-relaxed ${msg.role === 'user' ? 'bg-primary text-white rounded-tr-sm' : 'bg-white/5 border border-white/5 text-white/90 rounded-tl-sm'}`}>
                                        <div className="whitespace-pre-wrap">{msg.content}</div>
                                    </div>
                                </motion.div>
                            ))}
                            {isThinking && (
                                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex items-start gap-4">
                                     <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-inner bg-primary/20 border border-primary/30 text-primary">
                                        <Bot className="w-5 h-5" />
                                    </div>
                                    <div className="bg-white/5 border border-white/5 rounded-2xl p-4 rounded-tl-sm flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce"></span>
                                        <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '150ms' }}></span>
                                        <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: '300ms' }}></span>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                        <div ref={messagesEndRef} />
                    </div>
                    
                    {/* Input Area */}
                    <div className="p-4 sm:p-6 bg-black/20 border-t border-white/5 relative z-20">
                        <form onSubmit={handleChat} className="flex items-end gap-3 max-w-4xl mx-auto">
                            <div className="flex-1 bg-white/5 border border-white/10 rounded-2xl focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/50 transition-all flex items-center p-1 px-4">
                                <input 
                                    type="text" 
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Ask anything about your document..."
                                    className="flex-1 bg-transparent border-none py-3 outline-none text-white placeholder-muted-foreground"
                                    disabled={isThinking}
                                />
                            </div>
                            <button 
                                type="submit" 
                                disabled={!input.trim() || isThinking}
                                className="w-12 h-12 bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:hover:bg-primary rounded-xl flex items-center justify-center text-white transition-all shadow-lg shadow-primary/20"
                            >
                                <Send className="w-5 h-5 ml-1" />
                            </button>
                        </form>
                    </div>
                </motion.div>
            </main>
        </div>
    );
}
