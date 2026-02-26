"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
    role: "user" | "assistant";
    content: string;
}

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const token = localStorage.getItem("token");
            const response = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ message: input })
            });

            if (!response.ok) {
                throw new Error("Failed to get response");
            }

            const data = await response.json();
            const assistantMessage: Message = {
                role: "assistant",
                content: data.response,
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            console.error("Error sending message:", error);
            const errorMessage: Message = {
                role: "assistant",
                content: "Sorry, I had trouble connecting to the server.",
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col w-full max-w-4xl h-full max-h-[calc(100vh-8rem)] bg-white dark:bg-[#0f172a] sm:rounded-2xl sm:shadow-xl sm:border border-gray-200 dark:border-gray-800 overflow-hidden text-gray-900 dark:text-gray-100 transition-shadow">
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 scroll-smooth bg-gray-50/50 dark:bg-transparent custom-scrollbar">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center space-y-4 max-w-md mx-auto">
                        <div className="w-16 h-16 rounded-2xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 mb-2">
                            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                        </div>
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">How can I help you today?</h3>
                        <p className="text-gray-500 dark:text-gray-400 text-sm">Ask me about campus policies, course schedules, deadlines, or relevant university documents.</p>
                    </div>
                )}
                {messages.map((msg, index) => (
                    <div key={index} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} items-start gap-4 mb-6`}>
                        {msg.role === "assistant" && (
                            <div className="shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white shadow-sm mt-1">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                        )}
                        <div className={`relative max-w-[85%] sm:max-w-[75%] px-5 py-4 text-sm leading-relaxed ${msg.role === "user"
                            ? "bg-blue-600 text-white rounded-2xl rounded-tr-sm shadow-sm"
                            : "bg-white dark:bg-[#09090b] text-gray-800 dark:text-gray-200 rounded-2xl rounded-tl-sm shadow-sm border border-gray-100 dark:border-gray-800"
                            }`}>
                            {msg.role === "assistant" ? (
                                <div className="prose prose-slate dark:prose-invert prose-sm max-w-none wrap-break-word">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>
                            ) : (
                                <p className="whitespace-pre-wrap">{msg.content}</p>
                            )}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start items-start gap-4 mb-6">
                        <div className="shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white shadow-sm mt-1">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <div className="bg-white dark:bg-[#09090b] text-gray-500 dark:text-gray-400 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm border border-gray-100 dark:border-gray-800 flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse"></div>
                            <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse delay-75"></div>
                            <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse delay-150"></div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="p-4 sm:p-6 bg-white dark:bg-[#0f172a] border-t border-gray-100 dark:border-gray-800">
                <form onSubmit={handleSubmit} className="relative flex items-end gap-2 max-w-3xl mx-auto">
                    <div className="relative w-full shadow-sm rounded-2xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#09090b] focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent transition-all">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type a message..."
                            className="w-full pl-5 pr-12 py-4 bg-transparent text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none rounded-2xl"
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                        </button>
                    </div>
                </form>
                <div className="mt-3 text-center">
                    <p className="text-xs text-gray-400 dark:text-gray-500">AI can make mistakes. Consider verifying important information.</p>
                </div>
            </div>
        </div>
    );
}
