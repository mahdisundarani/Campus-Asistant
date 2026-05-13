"use client";

import { useState, useEffect, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/lib/supabase";

function LoginContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState<"student" | "admin">("student");
    const [error, setError] = useState("");
    const [info, setInfo] = useState("");
    const infoInitialized = useRef(false);

    useEffect(() => {
        if (!infoInitialized.current) {
            const expired = searchParams.get("expired");
            if (expired === "true") {
                // Use a microtask to avoid cascading render warning in some strict linters
                Promise.resolve().then(() => {
                    setInfo("Your session has expired. Please log in again to continue.");
                });
            }
            infoInitialized.current = true;
        }
    }, [searchParams]);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        const { data, error: authError } = await supabase.auth.signInWithPassword({
            email,
            password,
        });

        if (authError) {
            setError(authError.message);
            return;
        }

        const token = data.session.access_token;

        if (role === "admin") {
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/me`, {
                    headers: { Authorization: `Bearer ${token}` }
                });


                if (res.ok) {
                    const userData = await res.json();
                    if (!userData.is_admin) {
                        await supabase.auth.signOut();
                        setError("You do not have Administrator privileges.");
                        return;
                    }
                } else {
                    setError("Failed to verify admin status.");
                    return;
                }
            } catch (authVerifyErr) {
                console.error("Auth verification failed:", authVerifyErr);
                setError("Network error verifying admin status.");
                return;
            }
        }

        localStorage.setItem("token", token);
        router.push(role === "admin" ? "/admin" : "/");
    };

    return (
        <div className="relative flex min-h-screen items-center justify-center bg-background overflow-hidden selection:bg-primary/30 selection:text-primary">
            {/* Ambient Background Glows & Grid */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/20 rounded-full blur-[120px] opacity-60 pointer-events-none" />
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-secondary/10 rounded-full blur-[100px] opacity-40 pointer-events-none translate-x-1/3 -translate-y-1/3" />
            <div className="absolute inset-0 bg-cyber-grid opacity-30 pointer-events-none" />

            <div className="relative z-10 w-full max-w-md p-8 sm:p-10 space-y-8 glass-panel-heavy sm:rounded-2xl transition-all duration-500 hover:neon-glow-cyan">
                <div className="text-center">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/10 text-primary mb-6 shadow-[0_0_20px_rgba(0,229,255,0.25)] border border-primary/30">
                        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                    </div>
                    <h2 className="text-3xl font-bold tracking-tight text-foreground">Welcome back</h2>
                    <p className="mt-2 text-sm text-muted-foreground">Sign in to your Campus Assistant account</p>
                </div>

                {error && (
                    <div className="p-3 text-sm text-red-400 bg-red-500/10 rounded-xl text-center border border-red-500/20 backdrop-blur-md">
                        {error}
                    </div>
                )}

                {info && (
                    <div className="p-3 text-sm text-primary bg-primary/10 rounded-xl text-center border border-primary/20 backdrop-blur-md">
                        {info}
                    </div>
                )}

                <form onSubmit={handleLogin} className="space-y-6">
                    <div className="flex p-1 bg-black/40 rounded-xl border border-white/5 backdrop-blur-md">
                        <button
                            type="button"
                            onClick={() => setRole("student")}
                            className={`flex-1 py-2.5 px-4 text-sm font-medium rounded-lg transition-all duration-300 ${role === "student"
                                ? "bg-primary/20 text-primary border border-primary/50 shadow-[0_0_15px_rgba(0,229,255,0.2)]"
                                : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                                }`}
                        >
                            Student
                        </button>
                        <button
                            type="button"
                            onClick={() => setRole("admin")}
                            className={`flex-1 py-2.5 px-4 text-sm font-medium rounded-lg transition-all duration-300 ${role === "admin"
                                ? "bg-secondary/20 text-secondary border border-secondary/50 shadow-[0_0_15px_rgba(157,0,255,0.2)]"
                                : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                                }`}
                        >
                            Administrator
                        </button>
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-foreground tracking-wide">Email address</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="block w-full px-4 py-3 bg-black/50 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all shadow-inner"
                            placeholder="name@university.edu"
                            required
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-foreground tracking-wide">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="block w-full px-4 py-3 bg-black/50 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all shadow-inner"
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        className="w-full py-3.5 px-4 flex justify-center text-sm font-bold text-black bg-primary hover:bg-primary-hover rounded-xl shadow-[0_0_20px_rgba(0,229,255,0.4)] hover:shadow-[0_0_30px_rgba(0,229,255,0.6)] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary focus:ring-offset-background transition-all duration-300 transform hover:-translate-y-0.5"
                    >
                        Sign In
                    </button>
                </form>

                <p className="text-center text-sm text-muted-foreground">
                    Don&apos;t have an account?{" "}
                    <Link href="/signup" className="font-semibold text-primary hover:text-primary-hover transition-colors neon-text-cyan hover:shadow-primary">
                        Create an account
                    </Link>
                </p>
            </div>
        </div>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center dark:bg-[#09090b] text-gray-500">Loading...</div>}>
            <LoginContent />
        </Suspense>
    );
}
