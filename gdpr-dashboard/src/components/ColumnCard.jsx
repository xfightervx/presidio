
import { useState } from "react";
import ActionItem from "./ActionItem";

export default function ColumnCard({ column, actions, llmSuggestion, llmAccepted, onLLMFeedback, onManualFeedback, manualFeedback }) {
  // 'mode' can be 'llm' or 'manual'
  const [mode, setMode] = useState("llm");
  // Accept/reject for LLM suggestion
  const [llmDecision, setLLMDecision] = useState(llmAccepted ?? "");

  // Handle LLM accept/reject
  const handleLLMDecision = (decision) => {
    setLLMDecision(decision);
    onLLMFeedback(column, decision);
  };

  // Handle mode switch
  const handleModeChange = (e) => {
    setMode(e.target.value);
  };

  return (
    <div className="border rounded-xl shadow p-4 bg-white mb-4">
      <h2 className="text-lg font-bold mb-2">{column}</h2>

      {/* Mode selector */}
      <div className="flex items-center gap-6 mb-4">
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name={`mode-${column}`}
            value="llm"
            checked={mode === "llm"}
            onChange={handleModeChange}
            className="accent-blue-600"
          />
          <span className="font-medium text-blue-700">LLM Recommendation</span>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name={`mode-${column}`}
            value="manual"
            checked={mode === "manual"}
            onChange={handleModeChange}
            className="accent-purple-600"
          />
          <span className="font-medium text-purple-700">Manual Feedback</span>
        </label>
      </div>

      {/* LLM Recommendation Mode */}
      {mode === "llm" && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-2">
          <div className="mb-3">
            <div className="font-semibold text-blue-800 mb-1">Steward Suggestion</div>
            <div className="text-gray-700 whitespace-pre-line text-sm">{llmSuggestion || "No suggestion from LLM."}</div>
          </div>
          <div className="flex items-center gap-6 mt-2">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name={`llm-decision-${column}`}
                value="accept"
                checked={llmDecision === "accept"}
                onChange={() => handleLLMDecision("accept")}
                className="accent-green-600"
              />
              <span className="text-green-700 font-medium">Accept</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name={`llm-decision-${column}`}
                value="reject"
                checked={llmDecision === "reject"}
                onChange={() => handleLLMDecision("reject")}
                className="accent-red-600"
              />
              <span className="text-red-700 font-medium">Reject</span>
            </label>
          </div>
        </div>
      )}

      {/* Manual Feedback Mode */}
      {mode === "manual" && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
          <div className="font-semibold text-purple-800 mb-2">Manual Actions</div>
          <div className="flex flex-wrap gap-4">
            {actions.map((action, idx) => (
              <div key={idx} className="flex-1 min-w-[260px] max-w-[400px]">
                <ActionItem
                  action={action}
                  column={column}
                  onChange={onManualFeedback}
                  feedback={manualFeedback?.[action.action]}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Separator line for columns */}
      <div className="border-t border-gray-200 mt-6"></div>
    </div>
  );
}
