import React, { useState } from "react";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  RadialBarChart,
  RadialBar,
  AreaChart,
  Area
} from "recharts";

function DataQualityPage() {
  const [file, setFile] = useState(null);
  const [indicators, setIndicators] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Color schemes for charts
  const COLORS = {
    primary: ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444'],
    gradient: ['#6366F1', '#8B5CF6', '#EC4899', '#F97316', '#10B981'],
    quality: {
      excellent: '#10B981',
      good: '#3B82F6', 
      fair: '#F59E0B',
      poor: '#F97316',
      critical: '#EF4444'
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setIndicators(null);
    setError("");
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a CSV file first.");
      return;
    }

    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/quality", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to fetch indicators");

      const data = await response.json();
      setIndicators(data.indicators);
    } catch (err) {
      console.error(err);
      setError("Error fetching quality indicators.");
    } finally {
      setLoading(false);
    }
  };

  const getQualityColor = (score) => {
    if (score >= 90) return COLORS.quality.excellent;
    if (score >= 75) return COLORS.quality.good;
    if (score >= 60) return COLORS.quality.fair;
    if (score >= 40) return COLORS.quality.poor;
    return COLORS.quality.critical;
  };

  const formatCompletenessData = () => {
    if (!indicators?.completeness) return [];
    return Object.entries(indicators.completeness).map(([col, data]) => ({
      column: col.length > 15 ? col.substring(0, 12) + '...' : col,
      fullColumn: col,
      percentage: data.percentage || data, // Handle both old and new format
      nonNull: data.non_null_count || 0,
      null: data.null_count || 0,
      empty: data.empty_string_count || 0
    }));
  };

  const formatConsistencyData = () => {
    if (!indicators?.consistency) return [];
    return Object.entries(indicators.consistency).map(([col, data]) => ({
      column: col.length > 15 ? col.substring(0, 12) + '...' : col,
      fullColumn: col,
      valid: 100 - (data.invalid_percentage || data.pct || 0),
      invalid: data.invalid_percentage || data.pct || 0,
      invalidCount: data.invalid_count || data.invalid || 0,
      dataType: data.data_type || 'unknown'
    }));
  };

  const formatDataProfilingChart = () => {
    if (!indicators?.data_profiling) return [];
    return Object.entries(indicators.data_profiling).map(([col, profile]) => ({
      column: col.length > 12 ? col.substring(0, 10) + '..' : col,
      fullColumn: col,
      uniqueCount: profile.unique_count || 0,
      duplicateCount: profile.duplicate_count || 0,
      nullCount: profile.null_count || 0
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Data Quality Analytics
          </h1>
          <p className="text-gray-600 mt-2">
            Comprehensive analysis and visualization of your data quality metrics
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Upload Section */}
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-8 shadow-xl border border-gray-200 mb-8">
          <div className="flex flex-col md:flex-row gap-6 items-center">
            <div className="flex-1">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Select CSV File for Analysis
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-xl hover:border-blue-400 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              {file && (
                <p className="text-sm text-green-600 mt-2 font-medium">
                  Selected: {file.name}
                </p>
              )}
            </div>
            <button
              onClick={handleUpload}
              className={`px-8 py-3 rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl ${
                loading
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              }`}
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Analyzing...
                </span>
              ) : (
                "Analyze Quality"
              )}
            </button>
          </div>
          
          {error && (
            <div className="mt-4 bg-red-50 border-l-4 border-red-500 p-4 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 bg-red-500 rounded-full flex-shrink-0"></div>
                <p className="text-red-700 font-medium">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Results Section */}
        {indicators && (
          <div className="space-y-8">
            {/* Quality Score Overview */}
            {indicators.quality_score && (
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-8 shadow-xl border border-gray-200">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                  </div>
                  Overall Quality Score
                </h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div className="flex items-center justify-center">
                    <div className="relative w-56 h-56">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadialBarChart cx="50%" cy="50%" innerRadius="65%" outerRadius="95%" data={[{
                          name: 'Quality Score',
                          value: indicators.quality_score.overall_score,
                          fill: getQualityColor(indicators.quality_score.overall_score)
                        }]}>
                          <RadialBar 
                            dataKey="value" 
                            cornerRadius={15} 
                            fill={getQualityColor(indicators.quality_score.overall_score)}
                            stroke={getQualityColor(indicators.quality_score.overall_score)}
                            strokeWidth={2}
                          />
                        </RadialBarChart>
                      </ResponsiveContainer>
                      <div className="absolute inset-0 flex items-center justify-center flex-col">
                        <span className="text-4xl font-bold text-gray-800 mb-1">
                          {indicators.quality_score.overall_score}%
                        </span>
                        <span className={`text-lg font-semibold px-3 py-1 rounded-full ${
                          indicators.quality_score.category === 'Excellent' ? 'bg-green-100 text-green-800' :
                          indicators.quality_score.category === 'Good' ? 'bg-blue-100 text-blue-800' :
                          indicators.quality_score.category === 'Fair' ? 'bg-yellow-100 text-yellow-800' :
                          indicators.quality_score.category === 'Poor' ? 'bg-orange-100 text-orange-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {indicators.quality_score.category}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 gap-4">
                      <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-xl border border-blue-200 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm text-blue-800 font-medium">Completeness</div>
                          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                            <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                          </div>
                        </div>
                        <div className="text-3xl font-bold text-blue-600 mb-2">
                          {indicators.quality_score.factors.completeness_score}%
                        </div>
                        <div className="w-full bg-blue-200 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${indicators.quality_score.factors.completeness_score}%` }}
                          ></div>
                        </div>
                      </div>
                      <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-6 rounded-xl border border-purple-200 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm text-purple-800 font-medium">Duplicates Quality</div>
                          <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                            <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                          </div>
                        </div>
                        <div className="text-3xl font-bold text-purple-600 mb-2">
                          {indicators.quality_score.factors.duplicates_score}%
                        </div>
                        <div className="w-full bg-purple-200 rounded-full h-2">
                          <div 
                            className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${indicators.quality_score.factors.duplicates_score}%` }}
                          ></div>
                        </div>
                      </div>
                      <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-xl border border-green-200 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm text-green-800 font-medium">Consistency</div>
                          <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                            <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                          </div>
                        </div>
                        <div className="text-3xl font-bold text-green-600 mb-2">
                          {indicators.quality_score.factors.consistency_score}%
                        </div>
                        <div className="w-full bg-green-200 rounded-full h-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${indicators.quality_score.factors.consistency_score}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                    {indicators.quality_score.recommendations && (
                      <div className="bg-gray-50 p-6 rounded-xl border border-gray-200">
                        <h4 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                          <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center">
                            <div className="w-3 h-3 bg-white rounded opacity-90"></div>
                          </div>
                          Recommendations
                        </h4>
                        <ul className="space-y-3">
                          {indicators.quality_score.recommendations.map((rec, idx) => (
                            <li key={idx} className="flex items-start gap-3 text-sm text-gray-700 bg-white p-3 rounded-lg shadow-sm">
                              <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-blue-600 font-bold text-xs">{idx + 1}</span>
                              </div>
                              <span className="leading-relaxed">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Summary Stats */}
            {indicators.summary && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="group bg-gradient-to-r from-blue-500 to-blue-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <div className="w-6 h-6 bg-white rounded opacity-90"></div>
                    </div>
                    <div className="text-blue-100 text-sm font-medium">Rows</div>
                  </div>
                  <div className="text-3xl font-bold mb-1">{indicators.summary.total_rows?.toLocaleString() || 0}</div>
                  <div className="text-blue-100 text-sm">Total Records</div>
                </div>
                <div className="group bg-gradient-to-r from-purple-500 to-purple-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <div className="w-6 h-6 bg-white rounded opacity-90"></div>
                    </div>
                    <div className="text-purple-100 text-sm font-medium">Fields</div>
                  </div>
                  <div className="text-3xl font-bold mb-1">{indicators.summary.total_columns || 0}</div>
                  <div className="text-purple-100 text-sm">Data Columns</div>
                </div>
                <div className="group bg-gradient-to-r from-emerald-500 to-green-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <div className="w-6 h-6 bg-white rounded opacity-90"></div>
                    </div>
                    <div className="text-green-100 text-sm font-medium">Quality</div>
                  </div>
                  <div className="text-3xl font-bold mb-1">
                    {indicators.duplicates ? 
                      `${(100 - indicators.duplicates.duplicate_percentage).toFixed(1)}%` : 
                      '0%'
                    }
                  </div>
                  <div className="text-green-100 text-sm">Unique Data</div>
                </div>
                <div className="group bg-gradient-to-r from-orange-500 to-red-500 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <div className="w-6 h-6 bg-white rounded opacity-90"></div>
                    </div>
                    <div className="text-orange-100 text-sm font-medium">Size</div>
                  </div>
                  <div className="text-3xl font-bold mb-1">
                    {indicators.summary.memory_usage ? 
                      `${(indicators.summary.memory_usage / 1024).toFixed(0)}KB` : 
                      '0KB'
                    }
                  </div>
                  <div className="text-orange-100 text-sm">Memory Usage</div>
                </div>
              </div>
            )}

            {/* Completeness Analysis */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-8 shadow-xl border border-gray-200">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                  <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                </div>
                Data Completeness Analysis
              </h2>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                <div className="bg-gray-50 p-6 rounded-xl">
                  <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
                    <div className="w-6 h-6 bg-blue-500 rounded-lg flex items-center justify-center">
                      <div className="w-3 h-3 bg-white rounded opacity-90"></div>
                    </div>
                    Completeness by Column
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={formatCompletenessData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        dataKey="column" 
                        angle={-45} 
                        textAnchor="end" 
                        height={80}
                        fontSize={12}
                        stroke="#6b7280"
                      />
                      <YAxis stroke="#6b7280" />
                      <Tooltip 
                        formatter={(value, name) => [`${value}%`, 'Completeness']}
                        labelFormatter={(label) => {
                          const item = formatCompletenessData().find(d => d.column === label);
                          return item ? item.fullColumn : label;
                        }}
                        contentStyle={{
                          backgroundColor: '#f8fafc',
                          border: '1px solid #e2e8f0',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Bar 
                        dataKey="percentage" 
                        fill="url(#completenessGradient)" 
                        radius={[6, 6, 0, 0]}
                        stroke="#3B82F6"
                        strokeWidth={1}
                      />
                      <defs>
                        <linearGradient id="completenessGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3B82F6" />
                          <stop offset="100%" stopColor="#60A5FA" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
                    <div className="w-6 h-6 bg-green-500 rounded-lg flex items-center justify-center">
                      <div className="w-3 h-3 bg-white rounded opacity-90"></div>
                    </div>
                    Detailed Breakdown
                  </h3>
                  <div className="max-h-80 overflow-y-auto space-y-3 pr-2">
                    {formatCompletenessData().map((item, idx) => (
                      <div key={idx} className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200">
                        <div className="font-medium text-gray-800 mb-3 flex items-center justify-between">
                          <span className="truncate">{item.fullColumn}</span>
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            item.percentage >= 95 ? 'bg-green-100 text-green-800' :
                            item.percentage >= 80 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {item.percentage}%
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-sm mb-3">
                          <div className="text-center bg-green-50 p-2 rounded-lg">
                            <div className="font-bold text-green-600">{item.nonNull}</div>
                            <div className="text-green-700 text-xs">Valid</div>
                          </div>
                          <div className="text-center bg-red-50 p-2 rounded-lg">
                            <div className="font-bold text-red-600">{item.null}</div>
                            <div className="text-red-700 text-xs">Null</div>
                          </div>
                          <div className="text-center bg-orange-50 p-2 rounded-lg">
                            <div className="font-bold text-orange-600">{item.empty}</div>
                            <div className="text-orange-700 text-xs">Empty</div>
                          </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3 shadow-inner">
                          <div 
                            className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 shadow-sm"
                            style={{ width: `${item.percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Duplicates Analysis */}
            {indicators.duplicates && (
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-8 shadow-xl border border-gray-200">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                    <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                  </div>
                  Duplicate Data Analysis
                </h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div className="bg-gray-50 p-6 rounded-xl">
                    <h3 className="text-lg font-semibold text-gray-700 mb-4 text-center">Data Distribution</h3>
                    <ResponsiveContainer width="100%" height={280}>
                      <PieChart>
                        <Pie
                          data={[
                            { 
                              name: 'Unique Rows', 
                              value: indicators.duplicates.unique_rows, 
                              fill: '#10B981',
                              percentage: ((indicators.duplicates.unique_rows / indicators.duplicates.total_rows) * 100).toFixed(1)
                            },
                            { 
                              name: 'Duplicate Rows', 
                              value: indicators.duplicates.duplicate_rows, 
                              fill: '#EF4444',
                              percentage: indicators.duplicates.duplicate_percentage.toFixed(1)
                            }
                          ]}
                          cx="50%"
                          cy="50%"
                          outerRadius={90}
                          innerRadius={40}
                          dataKey="value"
                          label={({name, percentage}) => `${name}: ${percentage}%`}
                          labelLine={false}
                          stroke="#ffffff"
                          strokeWidth={2}
                        >
                          <Cell fill="#10B981" />
                          <Cell fill="#EF4444" />
                        </Pie>
                        <Tooltip 
                          formatter={(value, name) => [value.toLocaleString(), name]}
                          contentStyle={{
                            backgroundColor: '#f8fafc',
                            border: '1px solid #e2e8f0',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
                      <div className="w-6 h-6 bg-purple-500 rounded-lg flex items-center justify-center">
                        <div className="w-3 h-3 bg-white rounded opacity-90"></div>
                      </div>
                      Summary Statistics
                    </h3>
                    <div className="grid grid-cols-1 gap-4">
                      <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm text-green-800 font-medium">Unique Records</div>
                          <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                            <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                          </div>
                        </div>
                        <div className="text-3xl font-bold text-green-600 mb-1">
                          {indicators.duplicates.unique_rows?.toLocaleString()}
                        </div>
                        <div className="text-sm text-green-700">Out of {indicators.duplicates.total_rows?.toLocaleString()} total</div>
                      </div>
                      <div className="bg-gradient-to-r from-red-50 to-pink-50 p-6 rounded-xl border border-red-200 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm text-red-800 font-medium">Duplicate Records</div>
                          <div className="w-8 h-8 bg-red-500 rounded-lg flex items-center justify-center">
                            <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                          </div>
                        </div>
                        <div className="text-3xl font-bold text-red-600 mb-1">
                          {indicators.duplicates.duplicate_rows?.toLocaleString()}
                        </div>
                        <div className="text-sm text-red-700">
                          {indicators.duplicates.duplicate_percentage}% of total data
                        </div>
                      </div>
                    </div>
                    <div className={`p-6 rounded-xl border shadow-sm ${
                      indicators.duplicates.duplicate_percentage < 5 ? 
                        'bg-gradient-to-r from-green-50 to-emerald-50 border-green-200' :
                        indicators.duplicates.duplicate_percentage < 15 ?
                        'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200' :
                        'bg-gradient-to-r from-red-50 to-pink-50 border-red-200'
                    }`}>
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          indicators.duplicates.duplicate_percentage < 5 ? 'bg-green-500' :
                          indicators.duplicates.duplicate_percentage < 15 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}>
                          <div className="w-5 h-5 bg-white rounded opacity-90"></div>
                        </div>
                        <div>
                          <div className={`text-lg font-bold ${
                            indicators.duplicates.duplicate_percentage < 5 ? 'text-green-800' :
                            indicators.duplicates.duplicate_percentage < 15 ? 'text-yellow-800' :
                            'text-red-800'
                          }`}>
                            {indicators.duplicates.duplicate_percentage}% Duplication Rate
                          </div>
                          <div className={`text-sm ${
                            indicators.duplicates.duplicate_percentage < 5 ? 'text-green-600' :
                            indicators.duplicates.duplicate_percentage < 15 ? 'text-yellow-600' :
                            'text-red-600'
                          }`}>
                            {indicators.duplicates.duplicate_percentage < 5 ? 
                              '✓ Excellent - Low duplication detected' :
                              indicators.duplicates.duplicate_percentage < 15 ?
                              '⚠ Fair - Moderate duplication level' :
                              '✗ Poor - High duplication needs attention'
                            }
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Data Consistency Analysis */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-8 shadow-xl border border-gray-200">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-lg flex items-center justify-center">
                  <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                </div>
                Data Consistency & Validation
              </h2>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                <div className="bg-gray-50 p-6 rounded-xl">
                  <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
                    <div className="w-6 h-6 bg-emerald-500 rounded-lg flex items-center justify-center">
                      <div className="w-3 h-3 bg-white rounded opacity-90"></div>
                    </div>
                    Validation Results
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={formatConsistencyData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        dataKey="column" 
                        angle={-45} 
                        textAnchor="end" 
                        height={80}
                        fontSize={12}
                        stroke="#6b7280"
                      />
                      <YAxis stroke="#6b7280" />
                      <Tooltip 
                        formatter={(value, name) => [
                          `${value.toFixed(1)}%`, 
                          name === 'valid' ? 'Valid Data' : 'Invalid Data'
                        ]}
                        contentStyle={{
                          backgroundColor: '#f8fafc',
                          border: '1px solid #e2e8f0',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="valid" 
                        stackId="1" 
                        stroke="#10B981" 
                        fill="url(#validGradient)" 
                        fillOpacity={0.8}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="invalid" 
                        stackId="1" 
                        stroke="#EF4444" 
                        fill="url(#invalidGradient)" 
                        fillOpacity={0.8}
                      />
                      <defs>
                        <linearGradient id="validGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#10B981" stopOpacity={0.8} />
                          <stop offset="100%" stopColor="#34D399" stopOpacity={0.3} />
                        </linearGradient>
                        <linearGradient id="invalidGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#EF4444" stopOpacity={0.8} />
                          <stop offset="100%" stopColor="#F87171" stopOpacity={0.3} />
                        </linearGradient>
                      </defs>
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
                    <div className="w-6 h-6 bg-teal-500 rounded-lg flex items-center justify-center">
                      <div className="w-3 h-3 bg-white rounded opacity-90"></div>
                    </div>
                    Column Details
                  </h3>
                  <div className="max-h-80 overflow-y-auto space-y-3 pr-2">
                    {formatConsistencyData().map((item, idx) => (
                      <div key={idx} className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm hover:shadow-md transition-all duration-200">
                        <div className="flex justify-between items-start mb-3">
                          <div className="font-medium text-gray-800 truncate flex-1 mr-3">{item.fullColumn}</div>
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold flex-shrink-0 ${
                            item.dataType === 'email' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                            item.dataType === 'phone' ? 'bg-green-100 text-green-800 border border-green-200' :
                            item.dataType === 'date' ? 'bg-purple-100 text-purple-800 border border-purple-200' :
                            item.dataType === 'numeric' ? 'bg-orange-100 text-orange-800 border border-orange-200' :
                            item.dataType === 'url' ? 'bg-cyan-100 text-cyan-800 border border-cyan-200' :
                            'bg-gray-100 text-gray-800 border border-gray-200'
                          }`}>
                            {item.dataType}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                          <div className="bg-green-50 p-3 rounded-lg text-center border border-green-200">
                            <div className="font-bold text-green-600 text-lg">
                              {item.valid.toFixed(1)}%
                            </div>
                            <div className="text-green-700 text-xs">Valid Data</div>
                          </div>
                          <div className="bg-red-50 p-3 rounded-lg text-center border border-red-200">
                            <div className="font-bold text-red-600 text-lg">
                              {item.invalidCount}
                            </div>
                            <div className="text-red-700 text-xs">Invalid Count</div>
                          </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3 shadow-inner overflow-hidden">
                          <div className="h-full flex">
                            <div 
                              className="bg-gradient-to-r from-green-500 to-emerald-500 transition-all duration-500"
                              style={{ width: `${item.valid}%` }}
                            ></div>
                            <div 
                              className="bg-gradient-to-r from-red-500 to-pink-500 transition-all duration-500"
                              style={{ width: `${item.invalid}%` }}
                            ></div>
                          </div>
                        </div>
                        {item.invalid > 0 && (
                          <div className="mt-3 p-2 bg-yellow-50 rounded-lg border border-yellow-200">
                            <div className="text-xs text-yellow-800 font-medium">
                              ⚠ Validation issues detected - review data format consistency
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Data Profiling */}
            {indicators.data_profiling && (
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-8 shadow-xl border border-gray-200">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-lg flex items-center justify-center">
                    <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                  </div>
                  Data Profiling Overview
                </h2>
                <div className="bg-gray-50 p-6 rounded-xl">
                  <ResponsiveContainer width="100%" height={380}>
                    <BarChart data={formatDataProfilingChart()} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        dataKey="column" 
                        angle={-45} 
                        textAnchor="end" 
                        height={80}
                        fontSize={12}
                        stroke="#6b7280"
                      />
                      <YAxis stroke="#6b7280" />
                      <Tooltip 
                        labelFormatter={(label) => {
                          const item = formatDataProfilingChart().find(d => d.column === label);
                          return item ? item.fullColumn : label;
                        }}
                        contentStyle={{
                          backgroundColor: '#f8fafc',
                          border: '1px solid #e2e8f0',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Legend 
                        wrapperStyle={{
                          paddingTop: '20px'
                        }}
                      />
                      <Bar 
                        dataKey="uniqueCount" 
                        fill="url(#uniqueGradient)" 
                        name="Unique Values" 
                        radius={[2, 2, 0, 0]}
                        stroke="#3B82F6"
                        strokeWidth={1}
                      />
                      <Bar 
                        dataKey="duplicateCount" 
                        fill="url(#duplicateGradient)" 
                        name="Duplicates" 
                        radius={[2, 2, 0, 0]}
                        stroke="#EF4444"
                        strokeWidth={1}
                      />
                      <Bar 
                        dataKey="nullCount" 
                        fill="url(#nullGradient)" 
                        name="Null Values" 
                        radius={[2, 2, 0, 0]}
                        stroke="#F59E0B"
                        strokeWidth={1}
                      />
                      <defs>
                        <linearGradient id="uniqueGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3B82F6" />
                          <stop offset="100%" stopColor="#60A5FA" />
                        </linearGradient>
                        <linearGradient id="duplicateGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#EF4444" />
                          <stop offset="100%" stopColor="#F87171" />
                        </linearGradient>
                        <linearGradient id="nullGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#F59E0B" />
                          <stop offset="100%" stopColor="#FBBF24" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Data Profile Summary Cards */}
                <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-blue-800">Data Variety</h4>
                      <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                        <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-blue-600 mb-2">
                      {Object.values(indicators.data_profiling).reduce((acc, col) => acc + (col.unique_count || 0), 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-blue-700">Total Unique Values</div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-red-50 to-pink-50 p-6 rounded-xl border border-red-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-red-800">Data Redundancy</h4>
                      <div className="w-8 h-8 bg-red-500 rounded-lg flex items-center justify-center">
                        <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-red-600 mb-2">
                      {Object.values(indicators.data_profiling).reduce((acc, col) => acc + (col.duplicate_count || 0), 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-red-700">Total Duplicates</div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-6 rounded-xl border border-yellow-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-yellow-800">Data Gaps</h4>
                      <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center">
                        <div className="w-4 h-4 bg-white rounded opacity-90"></div>
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-yellow-600 mb-2">
                      {Object.values(indicators.data_profiling).reduce((acc, col) => acc + (col.null_count || 0), 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-yellow-700">Total Missing Values</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default DataQualityPage;
