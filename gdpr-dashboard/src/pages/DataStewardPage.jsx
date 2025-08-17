import React, { useState } from "react";
import RecommendationCard from "../components/RecommendationCard";

// Helper: group flat API array into { [column]: Recommendation[] }
function groupByColumn(items = []) {
  return items.reduce((acc, item) => {
    const col = item.column || "unknown";
    if (!acc[col]) acc[col] = [];
    acc[col].push(item);
    return acc;
  }, {});
}

export default function DataStewardPage() {
  const [file, setFile] = useState(null);
  const [grouped, setGrouped] = useState({}); // { column: Recommendation[] }
  const [feedback, setFeedback] = useState({}); // { column: { action: {status,value} } }
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [statusMsg, setStatusMsg] = useState("");

  // called by child cards
  const handleFeedbackChange = (column, action, status, value = null) => {
    setFeedback((prev) => ({
      ...prev,
      [column]: {
        ...(prev[column] || {}),
        [action]: { status, value },
      },
    }));
  };

  const onPickFile = (e) => {
    setFile(e.target.files?.[0] || null);
    setError("");
    setGrouped({});
    setFeedback({});
    setDownloadUrl(null);
    setStatusMsg("");
  };

  const getRecommendations = async () => {
    if (!file) {
      setError("Please choose a CSV file first.");
      return;
    }
    setBusy(true);
    setError("");
    setStatusMsg("");
    setDownloadUrl(null);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/recommend", {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();

      // backend returns a flat array of items with a "column" field
      const groupedData = Array.isArray(data)
        ? groupByColumn(data)
        : groupByColumn(data.recommendations || []);
      setGrouped(groupedData);
      setStatusMsg("✅ Recommendations loaded.");
    } catch (err) {
      console.error(err);
      setError("Failed to fetch recommendations.");
    } finally {
      setBusy(false);
    }
  };

  const submitFeedback = async () => {
    if (!file) {
      setError("Please choose a CSV file first.");
      return;
    }
    setBusy(true);
    setError("");
    setStatusMsg("");

    const form = new FormData();
    form.append("file", file); // send original file back
    form.append("feedback", JSON.stringify(feedback)); // send user choices

    try {
      const res = await fetch("http://localhost:8000/feedback", {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Server returned ${res.status}: ${txt}`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);
      setStatusMsg("✅ Changes applied. Download your processed CSV below.");
    } catch (err) {
      console.error(err);
      setError("Failed to apply feedback.");
    } finally {
      setBusy(false);
    }
  };

  const resetAll = () => {
    setFile(null);
    setGrouped({});
    setFeedback({});
    setError("");
    setStatusMsg("");
    setDownloadUrl(null);
  };

  const hasRecs = Object.keys(grouped).length > 0;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Data Steward Panel</h1>
          <p className="text-gray-600 mt-1">
            Upload a CSV, review per-column recommendations, accept/reject, and apply.
          </p>
        </header>

        {/* Upload + Buttons */}
        <div className="bg-white border rounded-lg p-4 shadow-sm mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <input
              type="file"
              accept=".csv"
              onChange={onPickFile}
              className="block text-sm text-gray-700"
            />
            {file && (
              <span className="text-xs text-gray-500 truncate max-w-[220px]">
                {file.name}
              </span>
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={getRecommendations}
              disabled={!file || busy}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {busy ? "Working..." : "Get Recommendations"}
            </button>
            <button
              onClick={submitFeedback}
              disabled={!file || !hasRecs || busy}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              {busy ? "Applying..." : "Submit Feedback"}
            </button>
            <button
              onClick={resetAll}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Alerts */}
        {!!error && (
          <div className="bg-red-50 text-red-700 border border-red-200 p-3 rounded mb-4">
            {error}
          </div>
        )}
        {!!statusMsg && (
          <div className="bg-emerald-50 text-emerald-700 border border-emerald-200 p-3 rounded mb-4">
            {statusMsg}
          </div>
        )}

        {/* Cards */}
        {hasRecs ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Object.entries(grouped).map(([column, actions]) => (
              <RecommendationCard
                key={column}
                columnName={column}
                recommendations={actions}
                onFeedbackChange={handleFeedbackChange}
              />
            ))}
          </div>
        ) : (
          <div className="text-gray-500 text-sm">
            No recommendations yet. Choose a CSV and click{" "}
            <span className="font-medium">Get Recommendations</span>.
          </div>
        )}

        {/* Download */}
        {downloadUrl && (
          <div className="mt-6">
            <a
              href={downloadUrl}
              download="processed.csv"
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
            >
              Download Processed CSV
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
