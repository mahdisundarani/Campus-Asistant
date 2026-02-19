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
        <div className="min-h-screen bg-gray-100 p-8">
            <div className="max-w-2xl mx-auto bg-white p-6 rounded-lg shadow-md">
                <div className="flex items-center justify-between mb-6">
                    <h1 className="text-2xl font-bold text-gray-800">Admin Dashboard</h1>
                    <button
                        onClick={() => {
                            localStorage.removeItem("token");
                            router.push("/login");
                        }}
                        className="px-4 py-2 text-sm text-red-600 border border-red-600 rounded hover:bg-red-50 transition-colors"
                    >
                        Logout
                    </button>
                </div>

                <div className="mb-8">
                    <h2 className="text-lg font-semibold mb-4 text-gray-700">Upload Documents</h2>
                    <form onSubmit={handleUpload} className="space-y-4">
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:bg-gray-50 transition-colors">
                            <input
                                type="file"
                                onChange={handleFileChange}
                                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-full file:border-0
                  file:text-sm file:font-semibold
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100
                  cursor-pointer"
                            />
                            {file && <p className="mt-2 text-sm text-gray-600">Selected: {file.name}</p>}
                        </div>

                        <button
                            type="submit"
                            disabled={!file || isUploading}
                            className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isUploading ? "Uploading..." : "Upload File"}
                        </button>
                    </form>
                    {status && (
                        <div className={`mt-4 p-3 rounded-md text-sm ${status.includes("Success") ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                            {status}
                        </div>
                    )}
                </div>

                <div className="border-t pt-6">
                    <h2 className="text-lg font-semibold mb-4 text-gray-700">System Status</h2>
                    <div className="bg-gray-50 p-4 rounded-md">
                        <p className="text-sm text-gray-600">System is ready to ingest documents.</p>
                        {/* Extended status checks can go here */}
                    </div>
                </div>
            </div>
        </div>
    );
}
