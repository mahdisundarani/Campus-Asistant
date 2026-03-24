import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { apiFetch } from "../../lib/api-client";

interface Message {
    role: "user" | "assistant";
    content: string;
    traces?: string[];
}

export default function ChatInterface({ 
    currentSessionId, 
    onNewSession,
    onHistoryLoadingChange
}: { 
    currentSessionId: string | null, 
    onNewSession: (id: string | null) => void,
    onHistoryLoadingChange?: (loading: boolean) => void 
}) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isHistoryLoading, setIsHistoryLoading] = useState(false);
    const [expandedTerminals, setExpandedTerminals] = useState<Record<number, boolean>>({});
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const lastLoadedSessionId = useRef<string | null>(null);
    const isStreaming = useRef(false);

    const scrollToBottom = (instant = false) => {
        if (!scrollContainerRef.current) return;
        
        const container = scrollContainerRef.current;
        const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 150;
        
        if (isNearBottom || instant || isStreaming.current) {
            messagesEndRef.current?.scrollIntoView({ behavior: instant ? "auto" : "smooth" });
        }
    };

    useEffect(() => {
        // Use instant scroll for streaming, smooth for switching sessions/new user messages
        scrollToBottom(isStreaming.current);
    }, [messages]);

    // When the currentSessionId prop changes (from sidebar click or "new chat"), load messages
    useEffect(() => {
        // CRITICAL BUG FIX: If we just started a chat and got a session_id back, 
        // DO NOT reload history as it will overwrite our streaming message.
        if (currentSessionId === lastLoadedSessionId.current) return;

        if (!currentSessionId) {
            setMessages([]);
            lastLoadedSessionId.current = null;
            return;
        }

        const loadSession = async () => {
            setIsHistoryLoading(true);
            onHistoryLoadingChange?.(true);
            try {
                const res = await apiFetch(`/chat/sessions/${currentSessionId}`);
                if (res.ok) {
                    const data = await res.json();
                    setMessages(data);
                    lastLoadedSessionId.current = currentSessionId;
                    // Force an instant scroll to bottom after loading history
                    setTimeout(() => scrollToBottom(true), 50);
                } else {
                    console.error("Failed to load session history");
                }
            } catch (err) {
                console.error("Error loading session:", err);
            } finally {
                setIsHistoryLoading(false);
                onHistoryLoadingChange?.(false);
            }
        };
        loadSession();
    }, [currentSessionId, onHistoryLoadingChange]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const history = messages.map(m => ({ role: m.role, content: m.content }));

            const response = await apiFetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: input,
                    history: history,
                    session_id: currentSessionId // Pass active session UUID
                })
            });

            if (!response.ok) {
                throw new Error("Failed to get response");
            }

            const reader = response.body?.getReader();
            if (!reader) throw new Error("No reader available");

            const decoder = new TextDecoder();
            const assistantMessage: Message = { role: "assistant", content: "", traces: [] };

            setMessages((prev) => [...prev, assistantMessage]);

            isStreaming.current = true;
            let buffer = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const event = JSON.parse(line);

                            if (event.type === "session_id") {
                                lastLoadedSessionId.current = event.session_id;
                                onNewSession(event.session_id);
                            } else if (event.type === "trace") {
                                assistantMessage.traces = [...(assistantMessage.traces || []), event.message];
                                setMessages((prev) => {
                                    const newMessages = [...prev];
                                    newMessages[newMessages.length - 1] = { ...assistantMessage };
                                    return newMessages;
                                });
                            } else if (event.type === "result") {
                                const fullText = event.response;
                                for (let i = 0; i <= fullText.length; i++) {
                                    assistantMessage.content = fullText.slice(0, i);
                                    setMessages((prev) => {
                                        const newMessages = [...prev];
                                        newMessages[newMessages.length - 1] = { ...assistantMessage };
                                        return newMessages;
                                    });
                                    // 5ms delay per character = smooth, fast typewriter effect
                                    await new Promise(r => setTimeout(r, 5));
                                }
                            } else if (event.type === "error") {
                                assistantMessage.content = "Error: " + event.message;
                                setMessages((prev) => {
                                    const newMessages = [...prev];
                                    newMessages[newMessages.length - 1] = { ...assistantMessage };
                                    return newMessages;
                                });
                            }
                        } catch (e) {
                            console.error("Error parsing NDJSON line:", e);
                        }
                    }
                }
            }
        } catch (error: unknown) {
            console.error("Error sending message:", error);

            let errorText = "Sorry, I had trouble connecting to the server.";
            if (error instanceof Error && error.message === "Session expired") {
                errorText = "Your session has expired. Redirecting to login...";
            }

            // Only add error message if we haven't already started streaming
            setMessages((prev) => {
                const lastMsg = prev[prev.length - 1];
                if (lastMsg && lastMsg.role === "assistant" && !lastMsg.content) {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1] = { ...lastMsg, content: errorText };
                    return newMessages;
                } else if (!lastMsg || lastMsg.role === "user") {
                    return [...prev, { role: "assistant", content: errorText }];
                }
                return prev;
            });
        } finally {
            setIsLoading(false);
            isStreaming.current = false;
        }
    };

    return (
        <div className="flex flex-col w-full h-full bg-background text-foreground transition-shadow relative">
            <div className="absolute inset-0 bg-cyber-grid opacity-10 pointer-events-none" />
            <div 
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 scroll-smooth custom-scrollbar relative z-10"
            >
                {isHistoryLoading ? (
                    <div className="flex flex-col items-center justify-center h-full space-y-4">
                        <div className="relative w-12 h-12">
                            <div className="absolute inset-0 border-4 border-primary/20 rounded-full shadow-[0_0_15px_rgba(0,229,255,0.2)]"></div>
                            <div className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent animate-spin"></div>
                        </div>
                        <p className="text-sm font-medium text-primary animate-pulse neon-text-cyan">Retrieving encrypted logs...</p>
                    </div>
                ) : messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center space-y-6 max-w-md mx-auto">
                        <div className="relative w-24 h-24 rounded-3xl bg-primary/10 flex items-center justify-center text-primary shadow-[0_0_40px_rgba(0,229,255,0.2)] border border-primary/20 neon-glow-cyan">
                            <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                        </div>
                        <div className="space-y-2">
                            <h3 className="text-3xl font-bold text-transparent bg-clip-text bg-linear-to-r from-primary to-secondary neon-text-cyan">Campus Assistant</h3>
                            <p className="text-muted-foreground text-sm tracking-wide">Secure link established. Query campus policies, course schedules, or system databases.</p>
                        </div>
                    </div>
                )}
                {!isHistoryLoading && messages.map((msg, index) => (
                    <div key={index} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} items-start gap-4 mb-6`}>
                        {msg.role === "assistant" && (
                            <div className="shrink-0 w-8 h-8 rounded-xl bg-primary/20 flex items-center justify-center text-primary shadow-[0_0_10px_rgba(0,229,255,0.3)] border border-primary/30 mt-1">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                        )}
                        <div className={`relative max-w-[85%] sm:max-w-[75%] px-5 py-4 text-sm leading-relaxed ${msg.role === "user"
                            ? "bg-secondary/20 text-foreground border border-secondary/50 rounded-2xl rounded-tr-sm shadow-[0_0_15px_rgba(157,0,255,0.15)] backdrop-blur-md"
                            : "glass-panel text-foreground rounded-2xl rounded-tl-sm"
                            }`}>

                            {/* UNDER THE HOOD TERMINAL TRACES */}
                            {msg.role === "assistant" && msg.traces && msg.traces.length > 0 && (
                                <div className="mb-4">
                                    {!msg.content || expandedTerminals[index] ? (
                                        <div className="overflow-hidden rounded-xl bg-[#030308] border border-accent/20 shadow-[0_0_20px_rgba(0,255,65,0.05)] font-mono text-[10px] sm:text-[11px]">
                                            <div className="flex items-center justify-between px-4 py-2 bg-[#0A0A12] border-b border-accent/20">
                                                <div className="flex items-center gap-2">
                                                    <div className="flex gap-1.5">
                                                        <div className="w-2.5 h-2.5 rounded-full bg-red-500/80 shadow-[0_0_5px_rgba(239,68,68,0.5)]"></div>
                                                        <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80 shadow-[0_0_5px_rgba(234,179,8,0.5)]"></div>
                                                        <div className="w-2.5 h-2.5 rounded-full bg-accent/80 shadow-[0_0_5px_rgba(0,255,65,0.5)]"></div>
                                                    </div>
                                                    <span className="text-[10px] text-accent/80 font-bold tracking-widest uppercase ml-2 text-shadow-sm">System Process Logs</span>
                                                </div>
                                                {msg.content && (
                                                    <button
                                                        onClick={() => setExpandedTerminals(prev => ({ ...prev, [index]: false }))}
                                                        className="text-accent/60 hover:text-accent transition-colors"
                                                    >
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                                        </svg>
                                                    </button>
                                                )}
                                            </div>
                                            <div className="p-4 space-y-1.5 text-accent max-h-60 overflow-y-auto custom-scrollbar shadow-inner">
                                                {msg.traces.map((trace, i) => (
                                                    <div key={i} className="flex leading-relaxed">
                                                        <span className="opacity-50 mr-3 shrink-0">root@sys:~#</span>
                                                        <span className="wrap-break-word font-semibold" style={{ animation: "fadeIn 0.2s ease-in-out" }}>{trace}</span>
                                                    </div>
                                                ))}
                                                {!msg.content && (
                                                    <div className="flex mt-1">
                                                        <span className="opacity-50 mr-3 shrink-0">root@sys:~#</span>
                                                        <span className="inline-block w-2.5 h-3.5 bg-accent animate-pulse shadow-[0_0_5px_rgba(0,255,65,0.8)]"></span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <button
                                            onClick={() => setExpandedTerminals(prev => ({ ...prev, [index]: true }))}
                                            className="flex items-center gap-2 px-3 py-1.5 bg-black/40 hover:bg-black/60 border border-white/5 hover:border-accent/30 rounded-lg text-xs font-semibold text-muted-foreground hover:text-accent transition-all duration-300 shadow-sm"
                                        >
                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                                            </svg>
                                            <span className="tracking-wide">PROCESS LOGS ({msg.traces.length})</span>
                                            <svg className="w-3 h-3 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                            </svg>
                                        </button>
                                    )}
                                </div>
                            )}

                            {msg.role === "assistant" ? (
                                <div className="prose prose-slate dark:prose-invert prose-sm max-w-none wrap-break-word text-foreground">
                                    {msg.content ? (
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                            {msg.content}
                                        </ReactMarkdown>
                                    ) : (
                                        <div className="flex items-center gap-3 text-primary italic mt-2 neon-text-cyan">
                                            <svg className="animate-spin h-5 w-5 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            Synthesizing response...
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <p className="whitespace-pre-wrap">{msg.content}</p>
                            )}
                        </div>
                    </div>
                ))}
                {isLoading && messages[messages.length - 1]?.role === "user" && (
                    <div className="flex justify-start items-start gap-4 mb-6">
                        <div className="shrink-0 w-8 h-8 rounded-xl bg-primary/20 flex items-center justify-center text-primary shadow-[0_0_10px_rgba(0,229,255,0.3)] border border-primary/30 mt-1">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <div className="glass-panel text-primary rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_5px_rgba(0,229,255,0.8)]"></div>
                            <div className="w-2 h-2 rounded-full bg-primary animate-pulse delay-75 shadow-[0_0_5px_rgba(0,229,255,0.8)]"></div>
                            <div className="w-2 h-2 rounded-full bg-primary animate-pulse delay-150 shadow-[0_0_5px_rgba(0,229,255,0.8)]"></div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="relative z-20 pb-6 pt-2 px-4 sm:px-6 bg-transparent shrink-0">
                <form onSubmit={handleSubmit} className="relative flex items-end gap-2 max-w-4xl mx-auto">
                    <div className="relative w-full glass-panel-heavy rounded-full border border-white/10 group focus-within:border-primary transition-all duration-300 focus-within:shadow-[0_0_20px_rgba(0,229,255,0.2)]">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Initialize query..."
                            className="w-full pl-6 pr-14 py-4.5 bg-transparent text-foreground placeholder-muted-foreground focus:outline-none rounded-full"
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-primary text-black rounded-full hover:bg-primary-hover disabled:opacity-30 transition-all shadow-[0_0_15px_rgba(0,229,255,0.3)] hover:shadow-[0_0_25px_rgba(0,229,255,0.6)]"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                        </button>
                    </div>
                </form>
                <div className="mt-4 text-center">
                    <p className="text-xs text-muted-foreground tracking-wide">System processes are AI-driven. Verify outputs before execution.</p>
                </div>
            </div>
        </div>
    );
}
