import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "../../lib/api-client";

interface ChatSession {
    id: string;
    title: string;
    updated_at: string;
}

export default function Sidebar({
    isAdmin,
    onSignOut,
    isCollapsed,
    onToggleCollapse,
    currentSessionId,
    isHistoryLoading = false,
    onSelectSession,
    onNewChat
}: {
    isAdmin: boolean;
    onSignOut: () => void;
    isCollapsed: boolean;
    onToggleCollapse: () => void;
    currentSessionId: string | null;
    isHistoryLoading?: boolean;
    onSelectSession: (id: string) => void;
    onNewChat: () => void;
}) {
    const router = useRouter();
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
    const [editTitle, setEditTitle] = useState("");

    const fetchSessions = async () => {
        try {
            const token = localStorage.getItem("token");
            if (!token) return;
            const res = await apiFetch("/chat/sessions");
            if (res.ok) {
                const data = await res.json();
                setSessions(data);
            }
        } catch (error) {
            console.error("Failed to fetch sessions", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleRename = async (id: string, newTitle: string) => {
        const previousSessions = [...sessions];
        setSessions(sessions.map(s => s.id === id ? { ...s, title: newTitle } : s));
        setEditingSessionId(null);
        setEditTitle("");

        try {
            const res = await apiFetch(`/chat/sessions/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: newTitle })
            });
            if (!res.ok) {
                setSessions(previousSessions);
                console.error("Failed to rename session");
            }
        } catch (error) {
            setSessions(previousSessions);
            console.error("Failed to rename session", error);
        }
    };

    const handleDelete = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();

        const previousSessions = [...sessions];
        setSessions(sessions.filter(s => s.id !== id));
        if (currentSessionId === id) {
            onNewChat();
        }

        try {
            const res = await apiFetch(`/chat/sessions/${id}`, {
                method: "DELETE"
            });
            if (!res.ok) {
                setSessions(previousSessions);
                console.error("Failed to delete session");
            }
        } catch (error) {
            setSessions(previousSessions);
            console.error("Failed to delete session", error);
        }
    };

    const startEditing = (id: string, title: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setEditingSessionId(id);
        setEditTitle(title);
    };

    useEffect(() => {
        // Fetch initially, and perhaps expose a ref/poll mechanism if needed, but we'll fetch on mount
        fetchSessions();
    }, [currentSessionId]); // Re-fetch whenever session ID changes (e.g. new chat created)

    return (
        <div className={`${isCollapsed ? 'w-16' : 'w-64'} shrink-0 bg-black/40 backdrop-blur-xl border-r border-white/5 flex flex-col h-full relative transition-all duration-300 ease-in-out z-20`}>

            <div className="p-3 flex items-center justify-between">
                {/* Brand */}
                {!isCollapsed && (
                    <div className="flex items-center gap-3 px-2">
                        <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary/20 text-primary border border-primary/30 shadow-[0_0_10px_rgba(0,229,255,0.2)] shrink-0">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                        </div>
                        <div className="overflow-hidden">
                            <h1 className="text-sm font-bold text-foreground tracking-wide leading-none truncate whitespace-nowrap">Campus Assistant</h1>
                        </div>
                    </div>
                )}

                {/* Collapse Toggle */}
                <button
                    onClick={onToggleCollapse}
                    className={`p-2 rounded-md hover:bg-white/10 text-muted-foreground hover:text-foreground transition-colors ${isCollapsed ? 'mx-auto' : ''}`}
                    title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        {isCollapsed ? (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                        ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                        )}
                    </svg>
                </button>
            </div>

            <div className="px-3 pb-3">
                {/* New Chat Button */}
                <button
                    onClick={onNewChat}
                    className={`flex items-center ${isCollapsed ? 'justify-center p-2' : 'gap-2 px-3 py-2 w-full'} bg-black/50 hover:bg-primary/10 text-foreground border border-white/5 hover:border-primary/30 rounded-lg text-sm font-medium transition-all duration-300 shadow-sm hover:shadow-[0_0_15px_rgba(0,229,255,0.15)] group`}
                    title="New Chat"
                >
                    <svg className="w-4 h-4 shrink-0 text-muted-foreground group-hover:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    {!isCollapsed && <span className="truncate whitespace-nowrap">New chat</span>}
                </button>
            </div>

            {/* History */}
            <div className="flex-1 overflow-y-auto px-3 py-2 custom-scrollbar">
                {!isCollapsed && (
                    <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 px-2">Recent</h3>
                )}
                <div className="flex flex-col gap-1">
                    {isLoading ? (
                        !isCollapsed && <div className="px-4 py-2 text-xs text-gray-400">Loading...</div>
                    ) : sessions.length === 0 ? (
                        !isCollapsed && <div className="px-3 py-3 text-xs text-gray-500 italic bg-gray-100/50 dark:bg-gray-800/30 rounded-md border border-dashed border-gray-300 dark:border-gray-700">No recent chats</div>
                    ) : (
                        sessions.map((chat) => (
                            <div key={chat.id} className="relative group flex items-center">
                                <button
                                    onClick={() => onSelectSession(chat.id)}
                                    title={chat.title}
                                    className={`w-full text-left text-sm rounded-md transition-all duration-200 border-l-2 ${isCollapsed ? 'p-2 flex justify-center border-l-0' : 'px-3 py-2 pr-16'} ${currentSessionId === chat.id ? 'bg-primary/10 text-primary border-primary shadow-[inset_2px_0_10px_rgba(0,229,255,0.05)] font-medium' : 'border-transparent text-muted-foreground hover:bg-white/5 hover:text-foreground hover:border-white/20'}`}
                                >
                                    {isCollapsed ? (
                                        <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                        </svg>
                                    ) : (
                                        editingSessionId === chat.id ? (
                                            <div className="flex items-center w-full" onClick={e => e.stopPropagation()}>
                                                <input
                                                    type="text"
                                                    className="w-full bg-transparent border-b border-blue-400 focus:outline-none text-sm text-gray-900 dark:text-gray-100 placeholder-transparent"
                                                    value={editTitle}
                                                    onChange={e => setEditTitle(e.target.value)}
                                                    onKeyDown={e => {
                                                        if (e.key === 'Enter') handleRename(chat.id, editTitle);
                                                        if (e.key === 'Escape') setEditingSessionId(null);
                                                    }}
                                                    autoFocus
                                                />
                                            </div>
                                        ) : (
                                            <div className="flex items-center justify-between w-full min-w-0">
                                                <span className="truncate block flex-1">{chat.title}</span>
                                                {isHistoryLoading && currentSessionId === chat.id && (
                                                    <svg className="animate-spin h-3 w-3 text-blue-500 shrink-0 ml-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                    </svg>
                                                )}
                                            </div>
                                        )
                                    )}
                                </button>

                                {!isCollapsed && editingSessionId === chat.id && (
                                    <div className="absolute right-2 flex items-center space-x-1">
                                        <button onClick={(e) => { e.stopPropagation(); handleRename(chat.id, editTitle); }} className="text-green-500 hover:text-green-600 p-1" title="Save">
                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                        </button>
                                        <button onClick={(e) => { e.stopPropagation(); setEditingSessionId(null); }} className="text-gray-400 hover:text-red-500 p-1" title="Cancel">
                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                        </button>
                                    </div>
                                )}

                                {!isCollapsed && editingSessionId !== chat.id && (
                                    <div className="absolute right-2 flex items-center space-x-1 sm:opacity-0 opacity-100 group-hover:opacity-100 transition-opacity bg-linear-to-l from-gray-100 dark:from-[#1e293b] via-gray-100 dark:via-[#1e293b] to-transparent pl-2">
                                        <button onClick={(e) => startEditing(chat.id, chat.title, e)} className="text-gray-400 hover:text-blue-500 p-1" title="Rename">
                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                                        </button>
                                        <button onClick={(e) => handleDelete(chat.id, e)} className="text-gray-400 hover:text-red-500 p-1" title="Delete">
                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Bottom controls */}
            <div className={`p-3 border-t border-white/5 flex flex-col gap-2 ${isCollapsed ? 'items-center' : ''}`}>
                {isAdmin && (
                    <button
                        onClick={() => router.push("/admin")}
                        title="Admin Dashboard"
                        className={`flex items-center text-sm text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-md transition-colors ${isCollapsed ? 'p-2 justify-center' : 'gap-2 px-3 py-2 w-full'}`}
                    >
                        <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {!isCollapsed && <span className="truncate whitespace-nowrap">Admin</span>}
                    </button>
                )}
                <button
                    onClick={onSignOut}
                    title="Sign out"
                    className={`flex items-center text-sm text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-md transition-colors group ${isCollapsed ? 'p-2 justify-center' : 'gap-2 px-3 py-2 w-full'}`}
                >
                    <svg className="w-4 h-4 shrink-0 text-gray-400 group-hover:text-red-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    {!isCollapsed && <span className="group-hover:text-red-500 transition-colors truncate whitespace-nowrap">Sign out</span>}
                </button>
            </div>
        </div>
    );
}
