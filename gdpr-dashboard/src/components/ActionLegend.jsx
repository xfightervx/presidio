const explanations = {
  mask: {
    label: "Mask",
    icon: "🔒",
    description: "This column contains sensitive information (e.g. phone, ID). Masking is recommended before storage or sharing.",
    recommendation: "Use Presidio or similar tools to anonymize or redact this field.",
    color: "text-red-600"
  },
  generalize: {
    label: "Generalize", 
    icon: "📊",
    description: "Sensitive but not unique, like job title or birth year. Generalization helps preserve utility while reducing sensitivity.",
    recommendation: "Group into broader buckets like decades (for dates) or job sectors.",
    color: "text-orange-600"
  },
  fill: {
    label: "Fill",
    icon: "🔧",
    description: "This column has missing values that can be imputed with statistical measures.",
    recommendation: "Use statistical imputation such as mean/median/mode based on the data type.",
    color: "text-blue-600"
  },
  drop: {
    label: "Drop",
    icon: "🗑️",
    description: "Too many missing values to keep this column useful.",
    recommendation: "Remove the column unless there is a domain-specific reason to retain it.",
    color: "text-gray-600"
  },
  enrich: {
    label: "Enrich",
    icon: "✨",
    description: "Could be improved by linking with external data sources.",
    recommendation: "Use mapping or reference tables to add more context (e.g., ISO codes, locations).",
    color: "text-green-600"
  },
  categorize: {
    label: "Categorize",
    icon: "📝",
    description: "Low number of unique values detected. Could be useful as a category for ML or analysis.",
    recommendation: "Consider encoding it using one-hot or label encoding.",
    color: "text-purple-600"
  }
};

export default function ActionLegend() {
  return (
    <div className="bg-white shadow-lg rounded-lg p-6 mb-6">
      <div className="flex items-center mb-4">
        <h2 className="text-xl font-bold text-gray-800">🔍 Action Types Guide</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(explanations).map(([key, val]) => (
          <div key={key} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex items-center mb-2">
              <span className="text-lg mr-2">{val.icon}</span>
              <strong className={`text-sm uppercase tracking-wide ${val.color}`}>
                {val.label}
              </strong>
            </div>
            <p className="text-sm text-gray-700 mb-2">{val.description}</p>
            <p className="text-xs text-gray-500 italic">
              💡 {val.recommendation}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
