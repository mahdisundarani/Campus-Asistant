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
    <main className="min-h-screen bg-gray-100 p-4">
      <header className="mb-6 flex flex-col items-center justify-center relative">
        <h1 className="text-3xl font-bold text-gray-800">Campus Assistant</h1>
        <p className="text-gray-600">Overview of campus policies, timetables, and documents</p>
        <button
          onClick={() => {
            localStorage.removeItem("token");
            router.push("/login");
          }}
          className="absolute right-0 top-0 px-4 py-2 text-sm text-red-600 border border-red-600 rounded hover:bg-red-50 transition-colors"
        >
          Logout
        </button>
      </header>
      <ChatInterface />
    </main>
  );
}
