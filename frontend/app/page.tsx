"use client";

import ChatInterface from "./components/ChatInterface";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  return (
    <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-[#09090b]">
      <header className="flex items-center justify-between px-6 py-4 bg-white dark:bg-[#0f172a] border-b border-gray-200 dark:border-gray-800 shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600 text-white shadow-sm">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100 leading-none">Campus Assistant</h1>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Enterprise Knowledge Base</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/admin")}
            className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
          >
            Admin
          </button>
          <button
            onClick={() => {
              localStorage.removeItem("token");
              router.push("/login");
            }}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-200 dark:bg-[#09090b] dark:border-gray-800 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white transition-all shadow-sm"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-hidden flex flex-col items-center p-4 sm:p-6 lg:p-8">
        <ChatInterface />
      </main>
    </div>
  );
}
