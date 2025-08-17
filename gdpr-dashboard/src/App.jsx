import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import DataStewardPage from "./pages/DataStewardPage";
import DataQualityPage from "./pages/DataQualityPage";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        {/* Navigation */}
        <nav className="bg-white shadow p-4 flex justify-center gap-6">
          <Link to="/" className="text-blue-600 hover:underline">
            Data Steward
          </Link>
          <Link to="/quality" className="text-blue-600 hover:underline">
            Data Quality
          </Link>
        </nav>

        {/* Routes */}
        <Routes>
          <Route path="/" element={<DataStewardPage />} />
          <Route path="/quality" element={<DataQualityPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
