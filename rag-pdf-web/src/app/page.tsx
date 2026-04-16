"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, UploadCloud, Loader2, Bot, User, CheckCircle2, AlertCircle, LogOut, MessageSquarePlus, MessageSquare } from "lucide-react";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import Image from "next/image";

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

    const [sessions, setSessions] = useState<{id: string, title: string}[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const { data: session, status } = useSession();
    const router = useRouter();

    useEffect(() => {
        if (status === "unauthenticated") {
            router.push("/login");
        }
    }, [status, router]);

    // Initial load of history
    useEffect(() => {
        if (session?.user?.email && status === "authenticated") {
            fetch(`http://127.0.0.1:8000/api/sessions/${session.user.email}`)
            .then(r => r.json())
            .then(data => {
                if (data && data.length > 0) {
                    setSessions(data);
                    loadSession(data[0].id);
                } else {
                    createNewSession();
                }
            }).catch(e => console.error(e));
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [session, status]);

    const createNewSession = async () => {
        if (!session?.user?.email) return;
        const res = await fetch("http://127.0.0.1:8000/api/sessions", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({user_email: session.user.email, title: "New Chat"})
        });
        const data = await res.json();
        setSessions(prev => [data, ...prev]);
        setActiveSessionId(data.id);
        setMessages([{ role: "assistant", content: "Hello! I am your AI assistant. Upload a document to start a conversation with your data." }]);
    };

    const loadSession = async (id: string) => {
        setActiveSessionId(id);
        const res = await fetch(`http://127.0.0.1:8000/api/history/${id}`);
        const data = await res.json();
        if (data && data.length > 0) {
            setMessages(data);
        } else {
            setMessages([{ role: "assistant", content: "Hello! I am your AI assistant. Upload a document to start a conversation with your data." }]);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isThinking]);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!activeSessionId) {
            setUploadStatus({ message: "Please select or start a chat first.", isError: true });
            return;
        }

        setIsUploading(true);
        setUploadStatus(null);
        
        const formData = new FormData();
        formData.append("file", file);
        formData.append("session_id", activeSessionId);

        try {
            const res = await fetch("http://127.0.0.1:8000/api/upload", {
                method: "POST",
                body: formData,
            });
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.detail || data.error || "Upload failed");
            
            setUploadStatus({ message: data.message || "File uploaded and processed!", isError: false });
        } catch (error: unknown) {
            const err = error as Error;
            setUploadStatus({ message: err.message, isError: true });
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleChat = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isThinking || !activeSessionId) return;

        const userMessage = input.trim();
        setInput("");
        
        const newMessages: Message[] = [...messages, { role: "user", content: userMessage }];
        setMessages(newMessages);
        setIsThinking(true);

        try {
            const res = await fetch("http://127.0.0.1:8000/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    session_id: activeSessionId,
                    user_email: session?.user?.email,
                    messages: newMessages 
                }),
            });
            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || data.error || "Failed to fetch response");

            setMessages([...newMessages, { role: "assistant", content: data.content }]);
        } catch (error: unknown) {
            const err = error as Error;
            setMessages([...newMessages, { role: "assistant", content: `❌ Error: ${err.message}` }]);
        } finally {
            setIsThinking(false);
        }
    };

    if (status === "loading" || status === "unauthenticated") {
        return (
            <div className="flex justify-center items-center h-screen w-full">
                <Loader2 className="w-10 h-10 text-primary animate-spin" />
            </div>
        );
    }

    return (
        <div className="flex justify-center items-center h-screen w-full px-6 py-2 md:px-10 md:py-4 pointer-events-none relative z-10 bg-background box-border">
            {/* Main Application Container */}
            <main className="w-full max-w-6xl h-[calc(100dvh-1rem)] md:h-[calc(100vh-2rem)] flex flex-row gap-4 sm:gap-6 pointer-events-auto relative">
                
                {/* Mobile Sidebar Overlay */}
                {isSidebarOpen && (
                    <div className="fixed inset-0 bg-black/60 z-40 md:hidden pb-10" onClick={() => setIsSidebarOpen(false)} />
                )}

                {/* Sidebar area */}
                <motion.div 
                    initial={{ opacity: 0, filter: 'blur(10px)' }}
                    animate={{ opacity: 1, filter: 'blur(0px)' }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                    className={`fixed md:relative inset-y-0 left-0 md:inset-auto h-full w-[85%] sm:w-80 md:w-1/3 max-w-sm flex-col gap-3 sm:gap-4 z-50 md:z-10 bg-[#09090b] md:bg-transparent p-5 md:p-1 border-r border-white/10 md:border-none shadow-2xl md:shadow-none shrink-0 ${isSidebarOpen ? 'flex' : 'hidden md:flex'}`}
                >
                    {/* Brand Card */}
                    <div className="glass-panel rounded-3xl p-5 sm:p-6 flex flex-col justify-center items-start shadow-2xl relative overflow-hidden group shrink-0">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 rounded-full blur-3xl -translate-y-12 translate-x-12 group-hover:bg-primary/30 transition-colors duration-500"></div>
                        <h1 className="text-2xl font-black tracking-tight mb-1 bg-gradient-to-br from-white to-primary/60 bg-clip-text text-transparent">Nexus RAG</h1>
                        <p className="text-muted-foreground text-[13px] leading-relaxed mb-3">Turn any PDF document into an interactive knowledge base.</p>
                        
                        <div className="w-full flex items-center justify-between border-t border-white/10 pt-3 mt-auto">
                           <div className="flex items-center gap-2">
                               {session?.user?.image && <Image src={session.user.image} alt="User" width={28} height={28} className="w-7 h-7 rounded-full border border-white/20" />}
                               <span className="text-sm font-medium text-white/80">{session?.user?.name?.split(' ')[0]}</span>
                           </div>
                           <button onClick={() => signOut()} className="text-xs flex items-center gap-1 text-muted-foreground hover:text-white transition-colors">
                               <LogOut className="w-3.5 h-3.5" /> Sign out
                           </button>
                        </div>
                    </div>

                    {/* Chat History List */}
                    <div className="glass-panel rounded-3xl p-4 flex flex-col shadow-xl relative overflow-hidden flex-1 min-h-[100px] max-h-[35%] shrink">
                        <div className="flex items-center justify-between mb-2 px-1">
                           <h2 className="text-[13px] font-semibold text-white/90">Chat History</h2>
                           <button onClick={createNewSession} className="text-primary hover:bg-primary/20 p-1 rounded-lg transition-colors" title="New Chat">
                               <MessageSquarePlus className="w-4 h-4" />
                           </button>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                           {sessions.map(s => (
                               <button 
                                   key={s.id} 
                                   onClick={() => loadSession(s.id)}
                                   className={`w-full text-left px-2 py-2 rounded-xl text-xs flex items-center gap-2 truncate transition-colors ${activeSessionId === s.id ? 'bg-primary/20 text-primary font-medium border border-primary/30' : 'text-muted-foreground hover:bg-white/5 hover:text-white border border-transparent'}`}
                               >
                                   <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                                   <span className="truncate">{s.title || "New Chat"}</span>
                               </button>
                           ))}
                        </div>
                    </div>

                    {/* Upload Card */}
                    <div className="glass-panel rounded-3xl p-4 sm:p-5 flex flex-col shadow-xl relative overflow-hidden shrink-0">
                        <h2 className="text-base font-semibold mb-2 sm:mb-3 text-white flex items-center gap-2">
                            <UploadCloud className="w-4 h-4 text-primary" />
                            Data Source
                        </h2>
                        
                        <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-white/10 hover:border-primary/50 transition-colors rounded-2xl bg-white/5 relative cursor-pointer group py-4"
                             onClick={() => fileInputRef.current?.click()}>
                            <input 
                                type="file" 
                                className="hidden" 
                                accept="application/pdf" 
                                onChange={handleUpload}
                                ref={fileInputRef}
                            />
                            {isUploading ? (
                                <div className="flex flex-col items-center gap-3">
                                    <Loader2 className="w-6 h-6 text-primary animate-spin" />
                                    <p className="text-xs text-muted-foreground font-medium">Processing...</p>
                                </div>
                            ) : (
                                <div className="text-center px-4 flex flex-col items-center gap-2">
                                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                                        <UploadCloud className="w-5 h-5 text-primary" />
                                    </div>
                                    <p className="text-xs font-medium text-white/80">Click to upload PDF</p>
                                </div>
                            )}
                        </div>

                        {uploadStatus && (
                            <motion.div 
                                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                className={`mt-3 p-2 rounded-xl text-xs flex items-start gap-2 ${uploadStatus.isError ? 'bg-destructive/20 text-destructive-foreground border border-destructive/30' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}
                            >
                                {uploadStatus.isError ? <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" /> : <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0" />}
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
                    className="flex-1 glass-panel md:rounded-3xl flex flex-col overflow-hidden shadow-2xl border-none md:border border-white/5 h-full relative z-20 w-full"
                >
                    {/* Mobile Header */}
                    <div className="md:hidden flex items-center justify-between p-4 border-b border-white/10 bg-[#09090b]">
                        <span className="font-bold text-white tracking-tight">Nexus RAG</span>
                        <button onClick={() => setIsSidebarOpen(true)} className="p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors">
                           <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" /></svg>
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 sm:p-6 sm:px-8 space-y-6 custom-scrollbar">
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
