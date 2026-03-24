"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "../../lib/api-client";

type Tab = "docs" | "timetable" | "deadlines" | "notices" | "logs" | "index";

interface LogEntry {
    id: string;
    created_at: string;
    user_id: string | null;
    query: string;
    intent: string;
    latency_ms: number;
}

export default function AdminDashboard() {
    const router = useRouter();
    const [activeTab, setActiveTab] = useState<Tab>("docs");
    const [isAdmin, setIsAdmin] = useState<boolean | null>(null);

    // Docs Upload State
    const [docFile, setDocFile] = useState<File | null>(null);
    const [docStatus, setDocStatus] = useState("");
    const [isDocUploading, setIsDocUploading] = useState(false);
    const [docDepartment, setDocDepartment] = useState("");
    const [docYear, setDocYear] = useState("");
    const [docCourse, setDocCourse] = useState("");
    const [documents, setDocuments] = useState<{name: string, size: number, department: string, year: string, course: string}[]>([]);
    const [isDocsLoading, setIsDocsLoading] = useState(false);

    // Timetable Upload State
    const [timeFile, setTimeFile] = useState<File | null>(null);
    const [timeStatus, setTimeStatus] = useState("");
    const [isTimeUploading, setIsTimeUploading] = useState(false);
    const [timeGroup, setTimeGroup] = useState(""); // e.g. "CS-A", "CS-B", or blank for shared
    type TimetableFile = { filename: string; group: string; rows: Record<string, string>[]; headers: string[]; row_count: number; size: number; };
    const [timetableFiles, setTimetableFiles] = useState<TimetableFile[]>([]);
    const [isTimetableLoading, setIsTimetableLoading] = useState(false);
    const [deletingTimetable, setDeletingTimetable] = useState<string | null>(null);
    const [expandedGroup, setExpandedGroup] = useState<string | null>(null);

    // Deadlines State
    const [deadlineFile, setDeadlineFile] = useState<File | null>(null);
    const [deadlineStatus, setDeadlineStatus] = useState("");
    const [isDeadlineUploading, setIsDeadlineUploading] = useState(false);
    const [deadlineRows, setDeadlineRows] = useState<Record<string, string>[]>([]);
    const [deadlineHeaders, setDeadlineHeaders] = useState<string[]>([]);
    const [deadlineExists, setDeadlineExists] = useState(false);
    const [isDeadlineLoading, setIsDeadlineLoading] = useState(false);
    const [isDeletingDeadlines, setIsDeletingDeadlines] = useState(false);

    // Logs State
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isLogsLoading, setIsLogsLoading] = useState(false);
    
    // Notices State
    const [noticeFile, setNoticeFile] = useState<File | null>(null);
    const [noticeStatus, setNoticeStatus] = useState("");
    const [isNoticeUploading, setIsNoticeUploading] = useState(false);
    const [notices, setNotices] = useState<{ department: string, title: string, content: string }[]>([]);
    const [isNoticesLoading, setIsNoticesLoading] = useState(false);

    // Index State
    const [indexStatus, setIndexStatus] = useState("");
    const [isIndexing, setIsIndexing] = useState(false);

    useEffect(() => {
        const checkAdmin = async () => {
            const token = localStorage.getItem("token");
            if (!token) {
                router.push("/login");
                return;
            }
            try {
                const res = await apiFetch("/me");
                if (res.ok) {
                    const data = await res.json();
                    if (!data.is_admin) {
                        router.push("/");
                    } else {
                        setIsAdmin(true);
                    }
                } else {
                    router.push("/login"); // apiFetch already clears token on 401
                }
            } catch (err) {
                console.error("Auth check failed:", err);
            }
        };
        checkAdmin();
    }, [router]);

    const fetchNotices = async () => {
        setIsNoticesLoading(true);
        try {
            const res = await apiFetch("/admin/notices");
            if (res.ok) {
                setNotices(await res.json());
            }
        } catch (err) {
            console.error("Failed to fetch notices:", err);
        } finally {
            setIsNoticesLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === "logs" && isAdmin) fetchLogs();
        if (activeTab === "docs" && isAdmin) fetchDocs();
        if (activeTab === "notices" && isAdmin) fetchNotices();
        if (activeTab === "timetable" && isAdmin) fetchTimetable();
        if (activeTab === "deadlines" && isAdmin) fetchDeadlines();
    }, [activeTab, isAdmin]);

    const fetchDeadlines = async () => {
        setIsDeadlineLoading(true);
        try {
            const res = await apiFetch("/admin/deadlines");
            if (res.ok) {
                const data = await res.json();
                setDeadlineExists(data.exists);
                setDeadlineRows(data.rows ?? []);
                setDeadlineHeaders(data.headers ?? []);
            }
        } catch (err) {
            console.error("Failed to fetch deadlines:", err);
        } finally {
            setIsDeadlineLoading(false);
        }
    };

    const handleUploadDeadlines = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!deadlineFile) return;
        setIsDeadlineUploading(true);
        setDeadlineStatus("Uploading...");
        const formData = new FormData();
        formData.append("file", deadlineFile);
        try {
            const res = await apiFetch("/upload-deadlines", { method: "POST", body: formData });
            if (res.ok) {
                setDeadlineStatus(`Uploaded ${deadlineFile.name} successfully!`);
                setDeadlineFile(null);
                fetchDeadlines();
            } else {
                setDeadlineStatus("Upload failed.");
            }
        } catch (err) {
            console.error("Deadline upload error:", err);
            setDeadlineStatus("Error uploading.");
        } finally {
            setIsDeadlineUploading(false);
        }
    };

    const handleDeleteDeadlines = async () => {
        if (!confirm("Delete deadlines.csv? This cannot be undone.")) return;
        setIsDeletingDeadlines(true);
        try {
            const res = await apiFetch("/admin/deadlines", { method: "DELETE" });
            if (res.ok) {
                setDeadlineExists(false);
                setDeadlineRows([]);
                setDeadlineStatus("Deadlines deleted.");
            }
        } catch (err) {
            console.error("Error deleting deadlines:", err);
        } finally {
            setIsDeletingDeadlines(false);
        }
    };

    const fetchDocs = async () => {
        setIsDocsLoading(true);
        try {
            const res = await apiFetch("/admin/docs");
            if (res.ok) {
                setDocuments(await res.json());
            }
        } catch (err) {
            console.error("Failed to fetch docs:", err);
        } finally {
            setIsDocsLoading(false);
        }
    };

    const handleDeleteDoc = async (filename: string) => {
        if (!confirm(`Are you sure you want to delete ${filename}?`)) return;
        
        try {
            const res = await apiFetch(`/admin/docs/${filename}`, {
                method: "DELETE",
            });
            if (res.ok) {
                setDocuments(documents.filter(d => d.name !== filename));
            } else {
                alert("Failed to delete document");
            }
        } catch (err) {
            console.error("Error deleting document", err);
        }
    };

    const fetchTimetable = async () => {
        setIsTimetableLoading(true);
        try {
            const res = await apiFetch("/admin/timetable");
            if (res.ok) {
                const data = await res.json();
                setTimetableFiles(Array.isArray(data) ? data : []);
            }
        } catch (err) {
            console.error("Failed to fetch timetable:", err);
        } finally {
            setIsTimetableLoading(false);
        }
    };

    const handleDeleteTimetable = async (filename: string) => {
        if (!confirm(`Delete ${filename}? This cannot be undone.`)) return;
        setDeletingTimetable(filename);
        try {
            const res = await apiFetch(`/admin/timetable/${encodeURIComponent(filename)}`, { method: "DELETE" });
            if (res.ok) {
                setTimetableFiles(prev => prev.filter(f => f.filename !== filename));
                setTimeStatus(`Deleted ${filename}.`);
                if (expandedGroup === filename) setExpandedGroup(null);
            }
        } catch (err) {
            console.error("Error deleting timetable:", err);
        } finally {
            setDeletingTimetable(null);
        }
    };

    const handleUploadTimetable = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!timeFile) return;
        setIsTimeUploading(true);
        setTimeStatus("Uploading...");
        const formData = new FormData();
        formData.append("file", timeFile);
        if (timeGroup.trim()) formData.append("group", timeGroup.trim());
        try {
            const res = await apiFetch("/upload-timetable", { method: "POST", body: formData });
            if (res.ok) {
                const label = timeGroup.trim() ? timeGroup.trim().toUpperCase() : "Shared";
                setTimeStatus(`Uploaded timetable for ${label} successfully!`);
                setTimeFile(null);
                setTimeGroup("");
                fetchTimetable();
            } else {
                setTimeStatus("Upload failed.");
            }
        } catch (err) {
            console.error("Timetable upload error:", err);
            setTimeStatus("Error uploading.");
        } finally {
            setIsTimeUploading(false);
        }
    };

    const handleDeleteNotice = async (index: number) => {
        if (!confirm("Delete this announcement permanently?")) return;
        try {
            const res = await apiFetch(`/admin/notices/${index}`, { method: "DELETE" });
            if (res.ok) {
                setNotices(notices.filter((_, i) => i !== index));
            } else {
                alert("Failed to delete notice.");
            }
        } catch (err) {
            console.error("Error deleting notice:", err);
        }
    };

    const handleViewDoc = async (filename: string) => {
        try {
            const res = await apiFetch(`/admin/docs/${filename}/view`);
            if (res.ok) {
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                window.open(url, "_blank");
            } else {
                alert("Failed to load document preview");
            }
        } catch (err) {
            console.error("Error viewing document", err);
        }
    };

    const fetchLogs = async () => {
        setIsLogsLoading(true);
        try {
            const res = await apiFetch("/admin/logs");
            if (res.ok) {
                setLogs(await res.json());
            }
        } catch (err) {
            console.error("Failed to fetch logs:", err);
        } finally {
            setIsLogsLoading(false);
        }
    };

    const handleUpload = async (
        e: React.FormEvent,
        file: File | null,
        endpoint: string,
        setStatus: (s: string) => void,
        setUploading: (b: boolean) => void,
        clearFile: () => void,
        extraData?: Record<string, string>
    ) => {
        e.preventDefault();
        if (!file) return;

        setUploading(true);
        setStatus("Uploading...");

        const formData = new FormData();
        formData.append("file", file);
        if (extraData) {
            Object.entries(extraData).forEach(([k, v]) => formData.append(k, v));
        }

        try {
            const response = await apiFetch(endpoint, {
                method: "POST",
                body: formData,
            });

            if (response.ok) {
                setStatus(`Successfully uploaded ${file.name}`);
                clearFile();
                if (endpoint === "/upload") {
                    setDocDepartment("");
                    setDocYear("");
                    setDocCourse("");
                    fetchDocs();
                }
            } else {
                setStatus("Upload failed.");
            }
        } catch (err) {
            console.error("Upload error:", err);
            setStatus("Error uploading file.");
        } finally {
            setUploading(false);
        }
    };

    const handleRebuildIndex = async () => {
        setIsIndexing(true);
        setIndexStatus("Rebuilding index... This may take a minute.");
        try {
            const res = await apiFetch("/rebuild-index", {
                method: "POST",
            });
            if (res.ok) {
                setIndexStatus("Search index rebuilt successfully!");
            } else {
                setIndexStatus("Failed to rebuild index.");
            }
        } catch (err) {
            console.error("Rebuild error:", err);
            setIndexStatus("Error connecting to server.");
        } finally {
            setIsIndexing(false);
        }
    };

    if (isAdmin === null) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-background relative overflow-hidden selection:bg-primary/30 selection:text-primary">
                <div className="absolute inset-0 bg-cyber-grid opacity-10 pointer-events-none" />
                <div className="relative w-16 h-16">
                    <div className="absolute inset-0 border-4 border-primary/20 rounded-full shadow-[0_0_15px_rgba(0,229,255,0.2)]"></div>
                    <div className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent animate-spin"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col min-h-screen bg-background relative selection:bg-primary/30 selection:text-primary text-foreground">
            <div className="absolute inset-0 bg-cyber-grid opacity-10 pointer-events-none z-0" />
            
            <header className="flex items-center justify-between px-6 py-4 bg-[#0A0A12]/80 backdrop-blur-xl border-b border-white/10 shrink-0 relative z-10 shadow-lg">
                <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary/20 text-primary border border-primary/30 shadow-[0_0_15px_rgba(0,229,255,0.2)]">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                        </svg>
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-transparent bg-clip-text bg-linear-to-r from-primary to-secondary neon-text-cyan leading-none">
                            System Control Panel
                        </h1>
                        <p className="text-xs text-muted-foreground mt-1 uppercase tracking-widest font-semibold">
                            Admin Telemetry & Indexing
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={() => router.push("/")}
                        className="text-sm font-bold text-muted-foreground hover:text-primary hover:neon-text-cyan transition-colors"
                    >
                        Back to Core
                    </button>
                    <button
                        onClick={() => {
                            localStorage.removeItem("token");
                            router.push("/login");
                        }}
                        className="px-5 py-2 text-sm font-bold text-white bg-red-600/80 hover:bg-red-500 rounded-xl transition-all shadow-[0_0_15px_rgba(220,38,38,0.3)] hover:shadow-[0_0_25px_rgba(220,38,38,0.6)]"
                    >
                        Terminate Session
                    </button>
                </div>
            </header>

            <main className="flex-1 p-6 md:p-10 max-w-6xl mx-auto w-full relative z-10">
                {/* Navigation Tabs */}
                <div className="flex space-x-2 bg-black/50 border border-white/5 p-1.5 rounded-2xl mb-8 w-fit shadow-xl backdrop-blur-md">
                    <button
                        onClick={() => setActiveTab("docs")}
                        className={`px-5 py-2.5 text-sm font-bold rounded-xl transition-all duration-300 ${activeTab === "docs"
                            ? "bg-primary/20 text-primary shadow-[0_0_15px_rgba(0,229,255,0.2)] border border-primary/30"
                            : "text-muted-foreground hover:text-foreground"
                            }`}
                    >
                        Index Docs
                    </button>
                    <button
                        onClick={() => setActiveTab("timetable")}
                        className={`px-5 py-2.5 text-sm font-bold rounded-xl transition-all duration-300 ${activeTab === "timetable"
                            ? "bg-secondary/20 text-secondary shadow-[0_0_15px_rgba(157,0,255,0.2)] border border-secondary/30"
                            : "text-muted-foreground hover:text-foreground"
                            }`}
                    >
                        Timetables
                    </button>
                    <button
                        onClick={() => setActiveTab("notices")}
                        className={`px-5 py-2.5 text-sm font-bold rounded-xl transition-all duration-300 ${activeTab === "notices"
                            ? "bg-primary/20 text-primary shadow-[0_0_15px_rgba(0,229,255,0.2)] border border-primary/30"
                            : "text-muted-foreground hover:text-foreground"
                            }`}
                    >
                        Notices
                    </button>
                    <button
                        onClick={() => setActiveTab("deadlines")}
                        className={`px-5 py-2.5 text-sm font-bold rounded-xl transition-all duration-300 ${activeTab === "deadlines"
                            ? "bg-orange-500/20 text-orange-400 shadow-[0_0_15px_rgba(249,115,22,0.2)] border border-orange-500/30"
                            : "text-muted-foreground hover:text-foreground"
                            }`}
                    >
                        Deadlines
                    </button>
                    <button
                        onClick={() => setActiveTab("logs")}
                        className={`px-5 py-2.5 text-sm font-bold rounded-xl transition-all duration-300 ${activeTab === "logs"
                            ? "bg-accent/20 text-accent shadow-[0_0_15px_rgba(0,255,65,0.2)] border border-accent/30"
                            : "text-muted-foreground hover:text-foreground"
                            }`}
                    >
                        Telemetry
                    </button>
                    <button
                        onClick={() => setActiveTab("index")}
                        className={`px-5 py-2.5 text-sm font-bold rounded-xl transition-all duration-300 ${activeTab === "index"
                            ? "bg-red-500/20 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.2)] border border-red-500/30"
                            : "text-muted-foreground hover:text-foreground"
                            }`}
                    >
                        Rebuild Engine
                    </button>
                </div>

                {/* TAB 1: UPLOAD DOCUMENTS */}
                {activeTab === "docs" && (
                    <div className="glass-panel-heavy p-8 border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] relative z-10 transition-all">
                        <h2 className="text-2xl font-bold tracking-tight text-white mb-2">
                            Knowledge Base Documents
                        </h2>
                        <p className="text-muted-foreground mb-6">
                            Upload PDF and DOCX files to safely index them into the neural retrieval engine.
                        </p>
                        <form
                            onSubmit={(e) =>
                                handleUpload(e, docFile, "/upload", setDocStatus, setIsDocUploading, () => setDocFile(null), {
                                    department: docDepartment,
                                    year: docYear,
                                    course: docCourse
                                })
                            }
                            className="space-y-6"
                        >
                            <div className={`relative flex justify-center px-6 py-12 border-2 border-dashed rounded-xl transition-all duration-300 ${docFile ? "border-primary bg-primary/10 shadow-[inset_0_0_20px_rgba(0,229,255,0.2)]" : "border-white/10 bg-black/40 hover:bg-black/60 hover:border-primary/50"}`}>
                                <div className="text-center">
                                    <div className="mt-4 flex text-sm text-gray-600 dark:text-gray-400 justify-center">
                                        <label htmlFor="doc-upload" className="relative cursor-pointer rounded-md font-medium text-blue-600 hover:text-blue-500">
                                            <span>Upload a file</span>
                                            <input id="doc-upload" type="file" className="sr-only" onChange={(e) => e.target.files && setDocFile(e.target.files[0])} />
                                        </label>
                                    </div>
                                    {docFile && <div className="mt-4 text-sm font-medium text-gray-900 dark:text-gray-200">{docFile.name}</div>}
                                </div>
                            </div>
                            
                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Department (Optional)</label>
                                    <input type="text" value={docDepartment} onChange={e => setDocDepartment(e.target.value)} placeholder="e.g. CS" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-[#09090b] text-sm focus:ring-2 focus:ring-blue-500" />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Year (Optional)</label>
                                    <input type="text" value={docYear} onChange={e => setDocYear(e.target.value)} placeholder="e.g. 1" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-[#09090b] text-sm focus:ring-2 focus:ring-blue-500" />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Course (Optional)</label>
                                    <input type="text" value={docCourse} onChange={e => setDocCourse(e.target.value)} placeholder="e.g. CS101" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-[#09090b] text-sm focus:ring-2 focus:ring-blue-500" />
                                </div>
                            </div>

                            <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-800">
                                <div className="text-sm font-bold text-primary neon-text-cyan">{docStatus}</div>
                                <button
                                    type="submit"
                                    disabled={!docFile || isDocUploading}
                                    className="px-8 py-3 bg-primary text-black rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(0,229,255,0.4)] hover:shadow-[0_0_25px_rgba(0,229,255,0.6)] disabled:opacity-30"
                                >
                                    {isDocUploading ? "UPLOADING..." : "UPLOAD DOCUMENT"}
                                </button>
                            </div>
                        </form>
                        
                        {/* Manage Documents Section */}
                        <div className="mt-10 border-t border-white/10 pt-8">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center justify-between">
                                Verified Uploads Registry
                                <button onClick={fetchDocs} className="p-2 text-muted-foreground hover:text-primary transition-colors hover:shadow-[0_0_10px_rgba(0,229,255,0.3)] rounded-lg" title="Refresh list">
                                    <svg className={`w-5 h-5 ${isDocsLoading ? "animate-spin text-primary" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                    </svg>
                                </button>
                            </h3>
                            
                            <div className="bg-black/50 rounded-xl border border-white/10 overflow-hidden shadow-inner backdrop-blur-md">
                                {isDocsLoading && documents.length === 0 ? (
                                    <div className="p-6 text-center text-sm text-primary animate-pulse font-mono tracking-widest uppercase">Fetching Records...</div>
                                ) : documents.length === 0 ? (
                                    <div className="p-6 text-center text-sm text-muted-foreground italic font-mono uppercase tracking-widest">Registry Empty.</div>
                                ) : (
                                    <ul className="divide-y divide-white/5">
                                        {documents.map((doc, idx) => (
                                            <li key={idx} className="flex items-center justify-between p-4 hover:bg-gray-100 dark:hover:bg-[#1e293b] transition-colors">
                                                <div className="flex items-center gap-3 overflow-hidden">
                                                    <div className="shrink-0 w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                        </svg>
                                                    </div>
                                                    <div className="flex-1 min-w-0 pr-4">
                                                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate flex items-center gap-2">
                                                            {doc.name}
                                                            {(doc.department || doc.year || doc.course) && (
                                                                <span className="flex gap-1 items-center">
                                                                    {doc.department && <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">{doc.department}</span>}
                                                                    {doc.year && <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">Yr {doc.year}</span>}
                                                                    {doc.course && <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">{doc.course}</span>}
                                                                </span>
                                                            )}
                                                        </p>
                                                        <p className="text-xs text-gray-500 dark:text-gray-400">{(doc.size / 1024).toFixed(1)} KB</p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <button onClick={() => handleViewDoc(doc.name)} className="shrink-0 p-2 text-gray-400 hover:text-blue-500 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors" title="View/Preview document">
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                                        </svg>
                                                    </button>
                                                    <button onClick={() => handleDeleteDoc(doc.name)} className="shrink-0 p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors" title="Delete document">
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                        </svg>
                                                    </button>
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* TAB 2: TIMETABLES */}
                {activeTab === "timetable" && (
                    <div className="glass-panel-heavy p-8 border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] relative z-10 transition-all">
                        <h2 className="text-2xl font-bold tracking-tight text-white mb-2">
                            Timetable &amp; Schedule Sync
                        </h2>
                        <p className="text-muted-foreground mb-6">
                            Upload a <code>timetable.csv</code> for each student group. Each upload is stored separately — existing groups are not overwritten.
                        </p>

                        <form onSubmit={handleUploadTimetable} className="space-y-5">
                            {/* Group name input */}
                            <div>
                                <label className="block text-xs font-bold text-muted-foreground uppercase tracking-widest mb-2">
                                    Student Group <span className="text-muted-foreground/50 font-normal normal-case">(e.g. CS-A, CS-B — leave blank for shared)</span>
                                </label>
                                <input
                                    type="text"
                                    value={timeGroup}
                                    onChange={e => setTimeGroup(e.target.value)}
                                    placeholder="CS-A"
                                    className="w-full px-4 py-2.5 bg-black/50 border border-white/10 rounded-xl text-white placeholder-muted-foreground text-sm focus:outline-none focus:ring-2 focus:ring-secondary/50 focus:border-secondary/50 transition-all"
                                />
                            </div>

                            {/* File drop zone */}
                            <div className={`relative flex justify-center px-6 py-10 border-2 border-dashed rounded-xl transition-all duration-300 ${timeFile ? "border-secondary bg-secondary/10 shadow-[inset_0_0_20px_rgba(157,0,255,0.2)]" : "border-white/10 bg-black/40 hover:bg-black/60 hover:border-secondary/50"}`}>
                                <div className="text-center">
                                    <div className="mt-4 flex text-sm justify-center">
                                        <label htmlFor="time-upload" className="relative cursor-pointer rounded-md font-bold text-secondary hover:text-secondary/80">
                                            <span className="neon-text-purple">Select CSV payload</span>
                                            <input id="time-upload" type="file" accept=".csv" className="sr-only" onChange={(e) => e.target.files && setTimeFile(e.target.files[0])} />
                                        </label>
                                    </div>
                                    {timeFile && <div className="mt-4 text-sm font-bold text-white">{timeFile.name}</div>}
                                </div>
                            </div>
                            <div className="flex items-center justify-between pt-4 border-t border-white/10">
                                <div className="text-sm font-bold text-secondary neon-text-purple">{timeStatus}</div>
                                <button
                                    type="submit"
                                    disabled={!timeFile || isTimeUploading}
                                    className="px-8 py-3 bg-secondary text-white rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(157,0,255,0.4)] hover:shadow-[0_0_25px_rgba(157,0,255,0.6)] hover:bg-[#b033ff] disabled:opacity-30 uppercase tracking-widest text-xs"
                                >
                                    {isTimeUploading ? "UPLOADING..." : "UPLOAD TIMETABLE"}
                                </button>
                            </div>
                        </form>

                        {/* Per-Group Timetable Registry */}
                        <div className="mt-10 border-t border-white/10 pt-8">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center justify-between">
                                Timetable Registry (by Group)
                                <button onClick={fetchTimetable} className="p-2 text-muted-foreground hover:text-secondary transition-colors hover:shadow-[0_0_10px_rgba(157,0,255,0.3)] rounded-lg" title="Refresh">
                                    <svg className={`w-5 h-5 ${isTimetableLoading ? "animate-spin text-secondary" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                    </svg>
                                </button>
                            </h3>

                            {isTimetableLoading ? (
                                <div className="p-6 text-center text-sm text-secondary animate-pulse font-mono tracking-widest uppercase">Loading Timetable Data...</div>
                            ) : timetableFiles.length === 0 ? (
                                <div className="p-6 text-center text-sm text-muted-foreground italic font-mono uppercase tracking-widest">No timetables uploaded yet.</div>
                            ) : (
                                <div className="space-y-4">
                                    {timetableFiles.map(tf => (
                                        <div key={tf.filename} className="glass-panel border border-white/10 rounded-xl overflow-hidden">
                                            {/* Card header */}
                                            <div className="flex items-center justify-between px-5 py-4">
                                                <button
                                                    className="flex items-center gap-3 text-left flex-1 min-w-0"
                                                    onClick={() => setExpandedGroup(expandedGroup === tf.filename ? null : tf.filename)}
                                                >
                                                    <span className="px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-widest bg-secondary/20 text-secondary border border-secondary/30 shadow-[0_0_10px_rgba(157,0,255,0.2)] shrink-0">
                                                        {tf.group}
                                                    </span>
                                                    <span className="text-sm text-muted-foreground font-mono truncate">{tf.filename}</span>
                                                    <span className="text-xs text-muted-foreground/60 shrink-0">{tf.row_count} rows · {(tf.size / 1024).toFixed(1)} KB</span>
                                                    <svg className={`w-4 h-4 text-muted-foreground shrink-0 transition-transform ${expandedGroup === tf.filename ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                    </svg>
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteTimetable(tf.filename)}
                                                    disabled={deletingTimetable === tf.filename}
                                                    className="ml-4 shrink-0 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-red-400 border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 hover:shadow-[0_0_10px_rgba(239,68,68,0.3)] rounded-lg transition-all disabled:opacity-40"
                                                >
                                                    {deletingTimetable === tf.filename ? "..." : "DELETE"}
                                                </button>
                                            </div>

                                            {/* Expandable CSV table */}
                                            {expandedGroup === tf.filename && tf.rows.length > 0 && (
                                                <div className="overflow-x-auto border-t border-white/10 bg-black/50">
                                                    <table className="w-full text-sm text-left text-muted-foreground">
                                                        <thead className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest bg-black/80 border-b border-white/10">
                                                            <tr>
                                                                {tf.headers.map(col => (
                                                                    <th key={col} className="px-4 py-3 whitespace-nowrap">{col}</th>
                                                                ))}
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {tf.rows.map((row, i) => (
                                                                <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                                                    {Object.values(row).map((val: unknown, j) => (
                                                                        <td key={j} className="px-4 py-3 whitespace-nowrap font-mono text-[11px] text-gray-200">{String(val)}</td>
                                                                    ))}
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* TAB: DEADLINES */}
                {activeTab === "deadlines" && (
                    <div className="glass-panel-heavy p-8 border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] relative z-10 transition-all">
                        <h2 className="text-2xl font-bold tracking-tight text-white mb-2">
                            Deadlines &amp; Academic Calendar
                        </h2>
                        <p className="text-muted-foreground mb-6">
                            Upload <code>deadlines.csv</code> with columns: <code>course_id, course_name, title, type, due_date, description</code>.
                        </p>

                        <form onSubmit={handleUploadDeadlines} className="space-y-5">
                            <div className={`relative flex justify-center px-6 py-10 border-2 border-dashed rounded-xl transition-all duration-300 ${deadlineFile ? "border-orange-500 bg-orange-500/10 shadow-[inset_0_0_20px_rgba(249,115,22,0.2)]" : "border-white/10 bg-black/40 hover:bg-black/60 hover:border-orange-500/50"}`}>
                                <div className="text-center">
                                    <div className="mt-4 flex text-sm justify-center">
                                        <label htmlFor="deadline-upload" className="relative cursor-pointer rounded-md font-bold text-orange-400 hover:text-orange-300">
                                            <span>Select CSV payload</span>
                                            <input id="deadline-upload" type="file" accept=".csv" className="sr-only" onChange={e => e.target.files && setDeadlineFile(e.target.files[0])} />
                                        </label>
                                    </div>
                                    {deadlineFile && <div className="mt-4 text-sm font-bold text-white">{deadlineFile.name}</div>}
                                </div>
                            </div>
                            <div className="flex items-center justify-between pt-4 border-t border-white/10">
                                <div className="text-sm font-bold text-orange-400">{deadlineStatus}</div>
                                <button
                                    type="submit"
                                    disabled={!deadlineFile || isDeadlineUploading}
                                    className="px-8 py-3 bg-orange-500 text-white rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(249,115,22,0.4)] hover:shadow-[0_0_25px_rgba(249,115,22,0.6)] hover:bg-orange-400 disabled:opacity-30 uppercase tracking-widest text-xs"
                                >
                                    {isDeadlineUploading ? "UPLOADING..." : "UPLOAD DEADLINES"}
                                </button>
                            </div>
                        </form>

                        {/* Deadlines Registry */}
                        <div className="mt-10 border-t border-white/10 pt-8">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center justify-between">
                                Active Deadline Registry
                                <div className="flex items-center gap-2">
                                    {deadlineExists && (
                                        <button
                                            onClick={handleDeleteDeadlines}
                                            disabled={isDeletingDeadlines}
                                            className="px-4 py-2 text-xs font-bold uppercase tracking-widest text-red-400 border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 hover:shadow-[0_0_15px_rgba(239,68,68,0.3)] rounded-lg transition-all disabled:opacity-40"
                                        >
                                            {isDeletingDeadlines ? "DELETING..." : "DELETE ALL"}
                                        </button>
                                    )}
                                    <button onClick={fetchDeadlines} className="p-2 text-muted-foreground hover:text-orange-400 transition-colors rounded-lg" title="Refresh">
                                        <svg className={`w-5 h-5 ${isDeadlineLoading ? "animate-spin text-orange-400" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                        </svg>
                                    </button>
                                </div>
                            </h3>

                            {isDeadlineLoading ? (
                                <div className="p-6 text-center text-sm text-orange-400 animate-pulse font-mono tracking-widest uppercase">Loading Deadlines...</div>
                            ) : !deadlineExists ? (
                                <div className="p-6 text-center text-sm text-muted-foreground italic font-mono uppercase tracking-widest">No deadlines uploaded yet.</div>
                            ) : deadlineRows.length === 0 ? (
                                <div className="p-6 text-center text-sm text-muted-foreground italic font-mono uppercase tracking-widest">Deadlines file is empty.</div>
                            ) : (
                                <div className="space-y-3">
                                    {deadlineRows.map((row, i) => {
                                        const typeColors: Record<string, string> = {
                                            exam: "bg-red-500/20 text-red-400 border-red-500/30",
                                            assignment: "bg-orange-500/20 text-orange-400 border-orange-500/30",
                                            lab: "bg-purple-500/20 text-purple-400 border-purple-500/30",
                                            project: "bg-blue-500/20 text-blue-400 border-blue-500/30",
                                            quiz: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                                        };
                                        const typeKey = (row.type || "").toLowerCase();
                                        const badgeClass = typeColors[typeKey] || "bg-white/10 text-gray-400 border-white/20";
                                        return (
                                            <div key={i} className="glass-panel border border-white/10 rounded-xl p-4 hover:bg-white/5 transition-all">
                                                <div className="flex items-start justify-between gap-3 mb-1">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <span className="font-bold text-white text-sm">{row.title || row.course_name}</span>
                                                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest border ${badgeClass}`}>{row.type}</span>
                                                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-secondary/20 text-secondary border border-secondary/30">{row.course_id}</span>
                                                    </div>
                                                    <span className="text-xs font-mono text-orange-400 shrink-0 font-bold">{row.due_date}</span>
                                                </div>
                                                {row.description && <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2 mt-1">{row.description}</p>}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* TAB 3: CAMPUS NOTICES */}
                {activeTab === "notices" && (
                    <div className="glass-panel-heavy p-8 border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] relative z-10 transition-all">
                        <h2 className="text-2xl font-bold tracking-tight text-white mb-2">
                            Campus Notices (JSON)
                        </h2>
                        <p className="text-muted-foreground mb-6">
                            Upload <code>notices.json</code> to update the digital announcement board.
                        </p>
                        <form
                            onSubmit={(e) =>
                                handleUpload(e, noticeFile, "/upload-notices", setNoticeStatus, setIsNoticeUploading, () => setNoticeFile(null))
                            }
                            className="space-y-6"
                        >
                            <div className={`relative flex justify-center px-6 py-12 border-2 border-dashed rounded-xl transition-all duration-300 ${noticeFile ? "border-primary bg-primary/10 shadow-[inset_0_0_20px_rgba(0,229,255,0.2)]" : "border-white/10 bg-black/40 hover:bg-black/60 hover:border-primary/50"}`}>
                                <div className="text-center">
                                    <div className="mt-4 flex text-sm justify-center">
                                        <label htmlFor="notice-upload" className="relative cursor-pointer rounded-md font-bold text-primary hover:text-primary/80">
                                            <span className="neon-text-cyan">Upload JSON payload</span>
                                            <input id="notice-upload" type="file" className="sr-only" onChange={(e) => e.target.files && setNoticeFile(e.target.files[0])} />
                                        </label>
                                    </div>
                                    {noticeFile && <div className="mt-4 text-sm font-bold text-white">{noticeFile.name}</div>}
                                </div>
                            </div>
                            <div className="flex items-center justify-between pt-4 border-t border-white/10">
                                <div className="text-sm font-bold text-primary neon-text-cyan">{noticeStatus}</div>
                                <button
                                    type="submit"
                                    disabled={!noticeFile || isNoticeUploading}
                                    className="px-8 py-3 bg-primary text-black rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(0,229,255,0.4)] hover:shadow-[0_0_25px_rgba(0,229,255,0.6)] hover:bg-primary-hover disabled:opacity-30 disabled:shadow-none flex items-center gap-2 uppercase tracking-widest text-xs"
                                >
                                    {isNoticeUploading ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                                            UPLOADING...
                                        </>
                                    ) : (
                                        "UPDATE NOTICES"
                                    )}
                                </button>
                            </div>
                        </form>

                        {/* Notices Preview List */}
                        <div className="mt-10 border-t border-white/10 pt-8">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center justify-between">
                                Active Announcements
                                <button onClick={fetchNotices} className="p-2 text-muted-foreground hover:text-primary transition-colors hover:shadow-[0_0_10px_rgba(0,229,255,0.3)] rounded-lg" title="Refresh list">
                                    <svg className={`w-5 h-5 ${isNoticesLoading ? "animate-spin text-primary" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                    </svg>
                                </button>
                            </h3>
                            <div className="space-y-4">
                                {isNoticesLoading && notices.length === 0 ? (
                                    <div className="space-y-4">
                                        {[1, 2, 3].map(i => (
                                            <div key={i} className="p-4 bg-black/40 border border-dashed border-white/10 rounded-xl animate-pulse">
                                                <div className="h-4 bg-white/10 rounded w-1/3 mb-4"></div>
                                                <div className="h-2 bg-white/5 rounded w-full mb-2"></div>
                                                <div className="h-2 bg-white/5 rounded w-2/3"></div>
                                            </div>
                                        ))}
                                    </div>
                                ) : notices.length === 0 ? (
                                    <p className="text-sm text-muted-foreground italic font-mono uppercase tracking-widest text-center mt-8">No active announcements.</p>
                                ) : (
                                    notices.map((n, i) => (
                                        <div key={i} className="p-5 glass-panel border border-white/10 rounded-xl hover:bg-white/5 transition-all group">
                                            <div className="flex justify-between items-start mb-2">
                                                <h4 className="font-bold text-white text-md tracking-wide">{n.title}</h4>
                                                <div className="flex items-center gap-2 shrink-0 ml-2">
                                                    <span className="px-2.5 py-1 rounded text-[10px] bg-primary/20 text-primary border border-primary/30 font-bold uppercase tracking-widest shadow-[0_0_10px_rgba(0,229,255,0.15)]">{n.department}</span>
                                                    <button
                                                        onClick={() => handleDeleteNotice(i)}
                                                        className="p-1.5 text-muted-foreground hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                                        title="Delete notice"
                                                    >
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                        </svg>
                                                    </button>
                                                </div>
                                            </div>
                                            <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">{n.content}</p>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* TAB 4: LOGS */}
                {activeTab === "logs" && (
                    <div className="glass-panel-heavy overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/10 relative z-10 transition-all sm:rounded-3xl">
                        <div className="p-6 md:p-8 border-b border-white/10 flex justify-between items-center bg-black/40">
                            <div>
                                <h2 className="text-2xl font-bold tracking-tight text-white mb-1">
                                    System Chat Logs
                                </h2>
                                <p className="text-muted-foreground text-sm tracking-wide">
                                    Live telemetry from the Supabase database.
                                </p>
                            </div>
                            <button onClick={fetchLogs} className="px-5 py-2.5 bg-black/50 border border-white/10 text-muted-foreground hover:text-accent hover:border-accent/50 rounded-lg text-xs font-bold uppercase tracking-widest transition-all shadow-sm flex items-center gap-2">
                                <svg className={`w-4 h-4 ${isLogsLoading ? "animate-spin text-accent" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                {isLogsLoading ? "SYNCING..." : "SYNC LOGS"}
                            </button>
                        </div>

                        <div className="overflow-x-auto bg-black/20">
                            <table className="w-full text-sm text-left text-muted-foreground">
                                <thead className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest bg-black/80 border-b border-white/10">
                                    <tr>
                                        <th scope="col" className="px-6 py-4">Timestamp</th>
                                        <th scope="col" className="px-6 py-4">Query</th>
                                        <th scope="col" className="px-6 py-4">Intent Engine</th>
                                        <th scope="col" className="px-6 py-4">Latency (ms)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.length === 0 && !isLogsLoading ? (
                                        <tr>
                                            <td colSpan={4} className="px-6 py-12 text-center text-muted-foreground italic font-mono uppercase tracking-widest">No Telemetry Found.</td>
                                        </tr>
                                    ) : (
                                        logs.map((log) => (
                                            <tr key={log.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                                <td className="px-6 py-4 whitespace-nowrap font-mono text-[11px] opacity-80">{new Date(log.created_at).toLocaleString()}</td>
                                                <td className="px-6 py-4 font-medium text-gray-200 max-w-md truncate" title={log.query}>{log.query}</td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-3 py-1 rounded-md text-[10px] font-bold tracking-widest uppercase border ${
                                                        log.intent === 'timetable' ? 'bg-secondary/20 text-secondary border-secondary/30 shadow-[0_0_10px_rgba(157,0,255,0.1)]' :
                                                        log.intent === 'rag' ? 'bg-primary/20 text-primary border-primary/30 shadow-[0_0_10px_rgba(0,229,255,0.1)]' :
                                                        'bg-gray-800 text-gray-300 border-gray-700'
                                                        }`}>
                                                        {log.intent}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 font-mono text-[11px] text-accent/80">{log.latency_ms} ms</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* TAB 5: INDEX MANAGEMENT */}
                {activeTab === "index" && (
                    <div className="glass-panel-heavy p-8 border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] relative z-10 transition-all sm:rounded-3xl">
                        <h2 className="text-2xl font-bold tracking-tight text-white mb-2">
                            Engine Vector Index
                        </h2>
                        <p className="text-muted-foreground mb-6">
                            When uploading new documents, you must rebuild the FAISS vector index to sync the core AI.
                        </p>

                        <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6 mb-8 shadow-[0_0_20px_rgba(239,68,68,0.05)]">
                            <h3 className="text-sm font-bold text-red-500 uppercase tracking-widest flex items-center gap-2">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                                System Warning
                            </h3>
                            <p className="text-sm text-red-400/80 mt-2 leading-relaxed tracking-wide">
                                Rebuilding the FAISS index blocks background threads. The retrieval features will be temporarily disabled until the reconstruction succeeds.
                            </p>
                        </div>

                        <div className="flex items-center gap-6">
                            <button
                                onClick={handleRebuildIndex}
                                disabled={isIndexing}
                                className="px-8 py-3 bg-red-600/80 text-white rounded-xl font-bold uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(239,68,68,0.3)] hover:shadow-[0_0_25px_rgba(239,68,68,0.6)] hover:bg-red-500 disabled:opacity-30 flex items-center gap-3 text-xs"
                            >
                                {isIndexing ? (
                                    <>
                                        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        REBUILDING ENGINE...
                                    </>
                                ) : (
                                    <>
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                        </svg>
                                        COMMENCE REBUILD
                                    </>
                                )}
                            </button>
                            <span className={`text-xs font-bold uppercase tracking-widest ${indexStatus.includes("success") || indexStatus.includes("successfully") ? "text-accent neon-text-green" : "text-primary neon-text-cyan"}`}>
                                {indexStatus}
                            </span>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
