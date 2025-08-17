import React, { useMemo, useState } from "react";

/**
 * Props:
 * - columnName: string
 * - recommendations: Array<{ action: string, reason: string, ... }>
 * - onFeedbackChange: (column, action, status, value) => void
 */
export default function RecommendationCard({
  columnName,
  recommendations = [],
  onFeedbackChange,
}) {
  // Sort actions to show "fill" first, then mask/generalize, then others
  const sorted = useMemo(() => {
    const order = { fill: 0, generalize: 1, mask: 2, drop: 3, categorize: 4, enrich: 5, keep: 6 };
    return [...recommendations].sort(
      (a, b) => (order[a.action] ?? 99) - (order[b.action] ?? 99)
    );
  }, [recommendations]);

  // Local UI state for "fill" custom inputs per action
  const [customFillValue, setCustomFillValue] = useState({}); // { action: stringValue }
  const [fillChoice, setFillChoice] = useState({}); // { action: selectedKey or 'custom' }

  const handleRadio = (action, status) => {
    onFeedbackChange?.(columnName, action, status, null);
  };

  const handleFillChoice = (action, optionKey, optionValue) => {
    setFillChoice((p) => ({ ...p, [action]: optionKey }));
    if (optionKey === "custom") {
      // keep last typed custom value, do not send yet
      onFeedbackChange?.(columnName, action, "accepted", null);
    } else {
      onFeedbackChange?.(columnName, action, "accepted", optionValue);
    }
  };

  const handleFillCustomInput = (action, val) => {
    setCustomFillValue((p) => ({ ...p, [action]: val }));
    onFeedbackChange?.(columnName, action, "accepted", val);
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-900">{columnName}</h3>
        <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
          {sorted.length} suggestion{sorted.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="space-y-4">
        {sorted
          .filter((r) => r.action !== "keep") // hide keep
          .map((rec, i) => {
            const isFill = rec.action === "fill";
            const isGeneralize = rec.action === "generalize";
            const isMask = rec.action === "mask";
            const isDrop = rec.action === "drop";
            const isCategorize = rec.action === "categorize";
            const isEnrich = rec.action === "enrich";

            // build fill options if present
            const fillOptions = isFill
              ? Object.entries(rec.filling || {}).map(([k, v]) => ({
                  key: k,
                  label: `${k} (${String(v)})`,
                  value: v,
                }))
              : [];

            return (
              <div key={`${rec.action}-${i}`} className="border rounded p-3">
                <div className="flex items-center justify-between">
                  <div className="font-medium capitalize">{rec.action}</div>
                  <div className="text-xs text-gray-500">{rec.reason}</div>
                </div>

                {/* Action-specific controls */}
                <div className="mt-3 space-y-3">
                  {isFill && (
                    <div className="space-y-2">
                      <div className="text-sm text-gray-700">Fill with:</div>
                      <select
                        className="w-full border rounded px-2 py-1 text-sm"
                        value={fillChoice[rec.action] || ""}
                        onChange={(e) => {
                          const opt = e.target.value;
                          if (opt === "custom") {
                            handleFillChoice(rec.action, "custom", null);
                          } else {
                            const chosen = fillOptions.find((o) => o.key === opt);
                            handleFillChoice(rec.action, opt, chosen ? chosen.value : null);
                          }
                        }}
                      >
                        <option value="" disabled>
                          Select an option…
                        </option>
                        {fillOptions.map((opt) => (
                          <option key={opt.key} value={opt.key}>
                            {opt.label}
                          </option>
                        ))}
                        <option value="custom">Custom…</option>
                      </select>

                      {fillChoice[rec.action] === "custom" && (
                        <input
                          type="text"
                          placeholder="Enter custom value"
                          className="w-full border rounded px-2 py-1 text-sm"
                          value={customFillValue[rec.action] || ""}
                          onChange={(e) =>
                            handleFillCustomInput(rec.action, e.target.value)
                          }
                        />
                      )}
                    </div>
                  )}

                  {isGeneralize && (
                    <div className="text-sm text-gray-700">
                      Suggest generalization (e.g., dates → decade, jobs → broader family).
                      <div className="mt-2 flex gap-3">
                        <button
                          className="px-3 py-1 text-xs rounded bg-blue-50 text-blue-700 border border-blue-200"
                          onClick={() =>
                            onFeedbackChange?.(columnName, rec.action, "accepted", "auto")
                          }
                        >
                          Accept (auto)
                        </button>
                        <button
                          className="px-3 py-1 text-xs rounded bg-gray-100 text-gray-700 border"
                          onClick={() =>
                            onFeedbackChange?.(columnName, rec.action, "rejected", null)
                          }
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  )}

                  {(isMask || isDrop || isCategorize || isEnrich) && (
                    <div className="flex gap-3">
                      <label className="inline-flex items-center gap-1 text-sm">
                        <input
                          type="radio"
                          name={`${columnName}-${rec.action}-status`}
                          onChange={() => handleRadio(rec.action, "accepted")}
                        />
                        Accept
                      </label>
                      <label className="inline-flex items-center gap-1 text-sm">
                        <input
                          type="radio"
                          name={`${columnName}-${rec.action}-status`}
                          defaultChecked
                          onChange={() => handleRadio(rec.action, "rejected")}
                        />
                        Reject
                      </label>
                    </div>
                  )}

                  {/* Tiny details */}
                  <div className="text-xs text-gray-500">
                    {isFill && typeof rec.percentage === "number" && (
                      <span>Missing ratio: {(rec.percentage * 100).toFixed(1)}%</span>
                    )}
                    {isMask && rec.gdpr_category && (
                      <span> GDPR: {rec.gdpr_category}</span>
                    )}
                    {isEnrich && rec.suggestions && (
                      <span> Suggestions: {rec.suggestions.join(", ")}</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
      </div>
    </div>
  );
}
