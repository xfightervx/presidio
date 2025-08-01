import { useState } from "react";
import ActionLegend from "./components/ActionLegend";
import UploadArea from "./components/UploadArea";
import RecommendationsDisplay from "./components/RecommendationsDisplay";

export default function App() {
  const [recommendations, setRecommendations] = useState(null);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        <div className="text-center py-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🛡️ GDPR Data Analysis Dashboard
          </h1>
          <p className="text-gray-600 text-lg">
            Upload your CSV file to get intelligent recommendations for data privacy and processing
          </p>
        </div>
        
        <ActionLegend />
        <UploadArea onResult={setRecommendations} />
        {recommendations && <RecommendationsDisplay data={recommendations} />}
      </div>
    </div>
  );
}
