"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminDashboard() {
    const router = useRouter();
    const [file, setFile] = useState<File | null>(null);
    const [status, setStatus] = useState("");
    const [isUploading, setIsUploading] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) {
            router.push("/login");
        }
    }, [router]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setIsUploading(true);
        setStatus("Uploading...");

        const formData = new FormData();
        formData.append("file", file);

        try {
            const token = localStorage.getItem("token");
            const response = await fetch("http://localhost:8000/upload", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                },
                body: formData,
            });

            if (response.ok) {
                setStatus(`Successfully uploaded ${file.name}`);
                setFile(null);
            } else {
                setStatus("Upload failed.");
            }
        } catch (error) {
            console.error("Upload error:", error);
            setStatus("Error uploading file.");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-[#09090b]">
            <header className="flex items-center justify-between px-6 py-4 bg-white dark:bg-[#0f172a] border-b border-gray-200 dark:border-gray-800 shrink-0">
                <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gray-800 dark:bg-gray-100 text-white dark:text-gray-900 shadow-sm">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                    </div>
                    <div>
                        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100 leading-none">Administration</h1>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Manage knowledge and settings</p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={() => router.push("/")}
                        className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                    >
                        Back to App
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

            <main className="flex-1 p-6 md:p-10">
                <div className="max-w-4xl mx-auto space-y-8">
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white mb-2">Knowledge Base Documents</h2>
                        <p className="text-gray-500 dark:text-gray-400">Upload PDF and DOCX files to be indexed into the retrieval system for AI assistant answers.</p>
                    </div>

                    <div className="bg-white dark:bg-[#0f172a] rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
                        <div className="p-6 md:p-8">
                            <form onSubmit={handleUpload} className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">File Upload</label>
                                    <div className={`relative flex justify-center px-6 py-12 border-2 border-dashed rounded-xl transition-colors ${file ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/10' : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 bg-gray-50 dark:bg-[#09090b]/50'
                                        }`}>
                                        <div className="text-center">
                                            <svg className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                                                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                                            </svg>
                                            <div className="mt-4 flex text-sm text-gray-600 dark:text-gray-400 justify-center">
                                                <label htmlFor="file-upload" className="relative cursor-pointer bg-white dark:bg-[#0f172a] rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500 dark:focus-within:ring-offset-[#09090b]">
                                                    <span>Upload a file</span>
                                                    <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} />
                                                </label>
                                                <p className="pl-1">or drag and drop</p>
                                            </div>
                                            <p className="text-xs text-gray-500 mt-2">PDF, DOCX up to 10MB</p>
                                            {file && (
                                                <div className="mt-4 inline-flex items-center px-3 py-1.5 rounded-md bg-white dark:bg-[#0f172a] border border-gray-200 dark:border-gray-700 shadow-sm">
                                                    <svg className="w-4 h-4 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                    </svg>
                                                    <span className="text-sm font-medium text-gray-900 dark:text-gray-200">{file.name}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center justify-between border-t border-gray-100 dark:border-gray-800 pt-6">
                                    <div className="w-full sm:w-auto">
                                        {status && (
                                            <div className={`px-4 py-2 rounded-lg text-sm font-medium ${status.includes("Success") || status.includes("Successfully")
                                                ? "bg-green-50 text-green-700 border border-green-200 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20"
                                                : "bg-red-50 text-red-700 border border-red-200 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20"
                                                }`}>
                                                {status}
                                            </div>
                                        )}
                                    </div>
                                    <button
                                        type="submit"
                                        disabled={!file || isUploading}
                                        className="inline-flex justify-center items-center py-2.5 px-6 border border-transparent rounded-xl shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-[#09090b] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                    >
                                        {isUploading ? (
                                            <>
                                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                </svg>
                                                Uploading...
                                            </>
                                        ) : "Upload File"}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-[#0f172a] rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden p-6 md:p-8">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">System Status</h3>
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-400">
                                <span className="w-2 h-2 mr-1.5 bg-green-500 rounded-full"></span>
                                Online
                            </span>
                        </div>
                        <div className="bg-gray-50 dark:bg-[#09090b] p-4 rounded-xl border border-gray-200 dark:border-gray-800">
                            <p className="text-sm text-gray-600 dark:text-gray-400">System is ready to ingest documents into the Knowledge Base.</p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
