"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/lib/supabase";

export default function SignupPage() {
    const router = useRouter();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState<"student" | "admin">("student");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setSuccess("");

        const { data, error } = await supabase.auth.signUp({
            email,        // ✅ explicit email
            password,
        });

        if (error) {
            setError(error.message);
            return;
        }

        // Wait for the user to be created in Supabase Auth, then inject the role into user_roles
        if (data?.user?.id) {
            try {
                const roleResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/assign-role`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_id: data.user.id, role }),
                });


                if (!roleResponse.ok) {
                    setError("Account created, but failed to assign role. Please contact support.");
                    return;
                }
            } catch {
                setError("Network error assigning role.");
                return;
            }
        }

        setSuccess("Account created! Redirecting to login...");
        setTimeout(() => {
            router.push("/login");
        }, 1500);
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-background relative overflow-hidden selection:bg-primary/30 selection:text-primary">
            {/* Cyber Grid Background */}
            <div className="absolute inset-0 bg-cyber-grid opacity-20 pointer-events-none" />

            {/* Ambient Background Glows */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/20 rounded-full blur-[120px] pointer-events-none" />

            <div className="w-full max-w-md p-8 sm:p-10 space-y-8 glass-panel-heavy sm:rounded-3xl shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/10 relative z-10 transition-all">
                <div className="text-center">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/20 text-primary mb-6 shadow-[0_0_20px_rgba(0,229,255,0.2)] border border-primary/20">
                        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                        </svg>
                    </div>
                    <h2 className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-linear-to-r from-primary to-secondary neon-text-cyan">Create Account</h2>
                    <p className="mt-2 text-sm text-muted-foreground tracking-wide">Join Campus Assistant to get started.</p>
                </div>

                {error && (
                    <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-500/10 dark:text-red-400 rounded-lg text-center border border-red-100 dark:border-red-500/20">
                        {error}
                    </div>
                )}
                {success && (
                    <div className="p-3 text-sm text-green-600 bg-green-50 dark:bg-green-500/10 dark:text-green-400 rounded-lg text-center border border-green-100 dark:border-green-500/20">
                        {success}
                    </div>
                )}

                <form onSubmit={handleSignup} className="space-y-5">
                    {/* Role Selection Toggle */}
                    <div className="flex p-1 bg-black/40 border border-white/5 rounded-2xl">
                        <button
                            type="button"
                            onClick={() => setRole("student")}
                            className={`flex-1 py-2.5 px-4 text-sm font-bold rounded-xl transition-all duration-300 ${role === "student"
                                ? "bg-primary/20 text-primary shadow-[0_0_10px_rgba(0,229,255,0.2)] border border-primary/30"
                                : "text-muted-foreground hover:text-foreground"
                                }`}
                        >
                            Student
                        </button>
                        <button
                            type="button"
                            onClick={() => setRole("admin")}
                            className={`flex-1 py-2.5 px-4 text-sm font-bold rounded-xl transition-all duration-300 ${role === "admin"
                                ? "bg-primary/20 text-primary shadow-[0_0_10px_rgba(0,229,255,0.2)] border border-primary/30"
                                : "text-muted-foreground hover:text-foreground"
                                }`}
                        >
                            Administrator
                        </button>
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-xs font-bold text-foreground uppercase tracking-widest pl-1">Email Address</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="block w-full px-4 py-3.5 bg-black/50 border border-white/10 rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all duration-300 focus:shadow-[0_0_15px_rgba(0,229,255,0.15)]"
                            placeholder="name@university.edu"
                            required
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-xs font-bold text-foreground uppercase tracking-widest pl-1">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="block w-full px-4 py-3.5 bg-black/50 border border-white/10 rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all duration-300 focus:shadow-[0_0_15px_rgba(0,229,255,0.15)]"
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        className="w-full py-3.5 px-4 flex justify-center text-sm font-bold text-black bg-primary hover:bg-primary-hover rounded-xl shadow-[0_0_20px_rgba(0,229,255,0.4)] hover:shadow-[0_0_30px_rgba(0,229,255,0.6)] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary dark:focus:ring-offset-background transition-all duration-300"
                    >
                        Create Account
                    </button>
                </form>

                <p className="text-center text-sm text-muted-foreground">
                    Already have an account?{" "}
                    <Link href="/login" className="font-bold text-primary hover:text-primary-hover hover:neon-text-cyan transition-colors">
                        Sign in here
                    </Link>
                </p>
            </div>
        </div>
    );
}
