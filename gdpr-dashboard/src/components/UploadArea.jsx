import { useState } from "react";
import axios from "axios";

export default function UploadArea({ onResult }) {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    
    setIsUploading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:8000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onResult(res.data); // Backend returns recommendations directly
    } catch (err) {
      console.error("Upload error", err);
      setError(err.response?.data?.error || "Failed to upload file. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4">📤 Upload Your CSV File</h2>
      
      <div className="space-y-4">
        <div className="flex items-center space-x-4">
          <input 
            type="file" 
            accept=".csv" 
            onChange={(e) => setFile(e.target.files[0])} 
            className="flex-1 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          <button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
              !file || isUploading 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isUploading ? '🔄 Analyzing...' : '🚀 Analyze CSV'}
          </button>
        </div>
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-red-600 text-sm">❌ {error}</p>
          </div>
        )}
        
        {file && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-blue-600 text-sm">📁 Selected: {file.name}</p>
          </div>
        )}
      </div>
    </div>
  );
}
