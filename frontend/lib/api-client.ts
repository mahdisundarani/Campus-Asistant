/**
 * api-client.ts — Centralized fetch wrapper for the Campus Assistant.
 * Handles automatic token injection and 401 Unauthorized (Expired) redirection.
 */

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
    const token = localStorage.getItem("token");
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const headers = {
        ...options.headers,
        "Authorization": `Bearer ${token}`
    };

    try {
        const response = await fetch(`${baseUrl}${endpoint}`, {
            ...options,
            headers,
        });

        // 401 Unauthorized = Session Expired or Invalid
        if (response.status === 401) {
            console.warn("Session expired or invalid. Redirecting to login...");
            localStorage.removeItem("token");

            // Redirect to login with an 'expired' flag
            if (typeof window !== "undefined") {
                window.location.href = "/login?expired=true";
            }
            throw new Error("Session expired");
        }

        return response;
    } catch (error) {
        console.error("API Fetch Error:", error);
        throw error;
    }
}
