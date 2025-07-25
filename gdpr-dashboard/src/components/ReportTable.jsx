import React from "react";

export default function ReportTable({ report }) {
  return (
    <div className="overflow-x-auto mt-6">
      <table className="min-w-full border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="px-4 py-2 text-left">Column</th>
            <th className="px-4 py-2 text-left">Category</th>
            <th className="px-4 py-2 text-left">Count</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(report).map(([col, cats]) =>
            Object.entries(cats).map(([cat, count], i) => (
              <tr key={`${col}-${cat}-${i}`}>
                <td className="border px-4 py-2">{col}</td>
                <td className="border px-4 py-2">{cat}</td>
                <td className="border px-4 py-2">{count}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
