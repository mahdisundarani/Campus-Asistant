"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ChatInterface from "./components/ChatInterface";
import Sidebar from "./components/Sidebar";
import { apiFetch } from "../lib/api-client";
import { supabase } from "../lib/supabase";

export default function Home() {
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [isVerified, setIsVerified] = useState(false);

  // Mobile sidebar states
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Desktop Sidebar collapse state
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Chat Session tracking
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);

  useEffect(() => {
    const checkUser = async () => {
      // Always get a fresh token from Supabase (it auto-refreshes internally).
      // This prevents the stale-token bug where the stored token is expired but
      // Supabase has already issued a new one that was never written to localStorage.
      const { data: sessionData } = await supabase.auth.getSession();

      if (!sessionData?.session) {
        localStorage.removeItem("token");
        router.push("/login");
        return;
      }

      // Always keep localStorage in sync with the latest Supabase token
      const freshToken = sessionData.session.access_token;
      localStorage.setItem("token", freshToken);

      try {
        const res = await apiFetch("/me");
        if (res.ok) {
          const data = await res.json();
          setIsAdmin(data.is_admin);
        }
      } catch (err) {
        console.error("Failed to fetch user roles", err);
      } finally {
        setIsVerified(true);
      }
    };
    checkUser();
  }, [router]);

  // Keep localStorage token in sync whenever Supabase auto-refreshes it mid-session
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.access_token) {
        localStorage.setItem("token", session.access_token);
      } else if (!session) {
        localStorage.removeItem("token");
      }
    });
    return () => subscription.unsubscribe();
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  const handleNewSession = (newId: string | null) => {
    setCurrentSessionId(newId);
  };

  const onHistoryLoadingChange = (loading: boolean) => {
    setIsHistoryLoading(loading);
  };

  if (!isVerified) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background transition-colors selection:bg-primary/30 selection:text-primary">
        <div className="relative w-16 h-16 mb-6">
          <div className="absolute inset-0 border-4 border-primary/20 rounded-full shadow-[0_0_15px_rgba(0,229,255,0.2)]"></div>
          <div className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent animate-spin"></div>
        </div>
        <div className="space-y-2 text-center">
          <h2 className="text-xl font-bold text-transparent bg-clip-text bg-linear-to-r from-primary to-secondary neon-text-cyan">Campus Assistant</h2>
          <p className="text-sm text-primary animate-pulse tracking-wide neon-text-cyan">Securing session link...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background text-foreground selection:bg-primary/30 selection:text-primary">
      {/* Mobile Sidebar Overlay */}
      {isMobileSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 md:hidden"
          onClick={() => setIsMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar - Mobile fixed, Desktop static shrink-0 */}
      <div className={`fixed inset-y-0 left-0 z-30 transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${isMobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <Sidebar
          isAdmin={isAdmin}
          onSignOut={handleSignOut}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          currentSessionId={currentSessionId}
          isHistoryLoading={isHistoryLoading}
          onSelectSession={(id) => setCurrentSessionId(id)}
          onNewChat={() => setCurrentSessionId(null)}
        />
      </div>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header to toggle sidebar */}
        <div className="md:hidden flex items-center p-4 border-b border-white/5 shrink-0 bg-black/40 backdrop-blur-md relative z-20">
          <button
            onClick={() => setIsMobileSidebarOpen(true)}
            className="p-2 -ml-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <span className="ml-2 font-bold text-transparent bg-clip-text bg-linear-to-r from-primary to-secondary neon-text-cyan">Campus Assistant</span>
        </div>

        <div className="flex-1 overflow-hidden relative">
          <ChatInterface
            currentSessionId={currentSessionId}
            onNewSession={handleNewSession}
            onHistoryLoadingChange={onHistoryLoadingChange}
          />
        </div>
      </main>
    </div>
  );
}
