import React from "react";
import ReportTable from "./components/ReportTable";
import reportData from "./data/sampleReport.json";

function App() {
  return (
    <div className="p-6 font-sans">
      <h1 className="text-2xl font-bold mb-4">GDPR Report Summary</h1>
      <ReportTable report={reportData} />
    </div>
  );
}

export default App;
