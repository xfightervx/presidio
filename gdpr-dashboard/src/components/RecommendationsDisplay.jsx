export default function RecommendationsDisplay({ data }) {
  if (!data) return null;

  // Function to get action color and icon
  const getActionStyle = (action) => {
    const styles = {
      mask: { color: 'text-red-600', bg: 'bg-red-50', icon: '🔒' },
      generalize: { color: 'text-orange-600', bg: 'bg-orange-50', icon: '📊' },
      fill: { color: 'text-blue-600', bg: 'bg-blue-50', icon: '🔧' },
      drop: { color: 'text-gray-600', bg: 'bg-gray-50', icon: '🗑️' },
      enrich: { color: 'text-green-600', bg: 'bg-green-50', icon: '✨' },
      categorize: { color: 'text-purple-600', bg: 'bg-purple-50', icon: '📝' },
      keep: { color: 'text-gray-400', bg: 'bg-gray-50', icon: '✓' }
    };
    return styles[action] || { color: 'text-gray-600', bg: 'bg-gray-50', icon: '❓' };
  };

  // Function to format percentage
  const formatPercentage = (value) => {
    if (typeof value === 'number') {
      return `${(value * 100).toFixed(1)}%`;
    }
    return value;
  };

  // Function to render additional details based on action type
  const renderDetails = (rec) => {
    const details = [];
    
    if (rec.percentage) {
      details.push(
        <span key="percentage" className="text-xs text-gray-500">
          Missing: {formatPercentage(rec.percentage)}
        </span>
      );
    }
    
    if (rec.filling) {
      details.push(
        <div key="filling" className="text-xs text-gray-600 mt-1">
          <strong>Suggested values:</strong>
          <ul className="ml-2 mt-1">
            {Object.entries(rec.filling).map(([key, value]) => (
              <li key={key}>
                {key}: {typeof value === 'number' ? value.toFixed(2) : value}
              </li>
            ))}
          </ul>
        </div>
      );
    }
    
    if (rec.gdpr_category) {
      details.push(
        <span key="gdpr" className="inline-block px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded-full mt-1">
          GDPR: {rec.gdpr_category}
        </span>
      );
    }
    
    if (rec.top_detected_entities && rec.top_detected_entities.length > 0) {
      details.push(
        <div key="entities" className="text-xs text-gray-600 mt-1">
          <strong>Detected entities:</strong>
          <ul className="ml-2 mt-1">
            {rec.top_detected_entities.slice(0, 3).map(([entity, count], idx) => (
              <li key={idx}>
                {entity}: {count} occurrences
              </li>
            ))}
          </ul>
        </div>
      );
    }
    
    if (rec.example_categories) {
      details.push(
        <div key="categories" className="text-xs text-gray-600 mt-1">
          <strong>Top categories:</strong>
          <ul className="ml-2 mt-1">
            {Object.entries(rec.example_categories).slice(0, 3).map(([category, count]) => (
              <li key={category}>
                {category}: {count} occurrences
              </li>
            ))}
          </ul>
        </div>
      );
    }
    
    if (rec.uniqueness_ratio) {
      details.push(
        <span key="uniqueness" className="text-xs text-gray-500">
          Uniqueness: {formatPercentage(rec.uniqueness_ratio)}
        </span>
      );
    }
    
    if (rec.suggestions && rec.suggestions.length > 0) {
      details.push(
        <div key="suggestions" className="text-xs text-gray-600 mt-1">
          <strong>Suggestions:</strong>
          <ul className="ml-2 mt-1">
            {rec.suggestions.map((suggestion, idx) => (
              <li key={idx}>• {suggestion}</li>
            ))}
          </ul>
        </div>
      );
    }
    
    return details;
  };

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <div className="flex items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">📊 Data Analysis Recommendations</h2>
      </div>
      
      {Object.keys(data).length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">✅</div>
          <p className="text-lg">No issues detected!</p>
          <p className="text-sm">Your data looks good to go.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(data).map(([column, actions]) => (
            <div key={column} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center mb-3">
                <h3 className="text-lg font-semibold text-gray-800 mr-2">📋 {column}</h3>
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                  {actions.length} recommendation{actions.length > 1 ? 's' : ''}
                </span>
              </div>
              
              <div className="space-y-3">
                {actions.map((rec, idx) => {
                  const style = getActionStyle(rec.action);
                  return (
                    <div key={idx} className={`${style.bg} border-l-4 border-${style.color.split('-')[1]}-400 p-3 rounded-r-lg`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center mb-1">
                            <span className="text-lg mr-2">{style.icon}</span>
                            <span className={`font-semibold text-sm uppercase tracking-wide ${style.color}`}>
                              {rec.action}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 mb-2">{rec.reason}</p>
                          <div className="space-y-1">
                            {renderDetails(rec)}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
