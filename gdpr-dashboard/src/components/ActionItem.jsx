import { useState, useEffect } from "react";

export default function ActionItem({ action, column, onChange, feedback }) {
  const [decision, setDecision] = useState(feedback?.status || "");
  const [comment, setComment] = useState(feedback?.value || "");

  // Update local state when feedback prop changes
  useEffect(() => {
    setDecision(feedback?.status || "");
    setComment(feedback?.value || "");
  }, [feedback]);

  const handleUpdate = (d, c) => {
    setDecision(d);
    setComment(c);
    onChange(column, action.action, d, c);
  };

  return (
    <div className="bg-gray-50 p-2 rounded mb-2 border">
      <p><strong>Action:</strong> {action.action}</p>
      <p><strong>Reason:</strong> {action.reason}</p>
      {action.percentage && <p><strong>Percentage:</strong> {(action.percentage * 100).toFixed(2)}%</p>}

      <div className="mt-2 flex gap-2">
        <select
          className="border rounded p-1"
          value={decision}
          onChange={(e) => handleUpdate(e.target.value, comment)}
        >
          <option value="">Select...</option>
          <option value="accept">✅ Accept</option>
          <option value="reject">❌ Reject</option>
        </select>
        <input
          className="flex-1 p-1 border rounded"
          placeholder="Comment (optional)"
          value={comment}
          onChange={(e) => handleUpdate(decision, e.target.value)}
        />
      </div>
    </div>
  );
}
