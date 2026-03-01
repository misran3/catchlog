// frontend/components/ComplianceReportView.tsx
"use client";

import { ComplianceReport } from "@/lib/types";

interface ComplianceReportViewProps {
  report: ComplianceReport;
  onClose: () => void;
}

const severityColors = {
  compliant: "bg-green-100 text-green-800 border-green-300",
  minor: "bg-yellow-100 text-yellow-800 border-yellow-300",
  major: "bg-orange-100 text-orange-800 border-orange-300",
  critical: "bg-red-100 text-red-800 border-red-300",
};

export function ComplianceReportView({ report, onClose }: ComplianceReportViewProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className={`p-4 border-b ${severityColors[report.severity]}`}>
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">Compliance Report</h2>
            <span className="px-3 py-1 rounded-full text-sm font-medium uppercase">
              {report.severity}
            </span>
          </div>
          {report.email_sent && (
            <p className="text-sm mt-1">📧 Alert email sent</p>
          )}
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Trip Summary */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-2">Trip Summary</h3>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="bg-gray-50 p-2 rounded">
                <div className="text-gray-500">Total</div>
                <div className="font-medium text-gray-800">{report.trip_summary.total_catches}</div>
              </div>
              <div className="bg-green-50 p-2 rounded">
                <div className="text-gray-500">Legal</div>
                <div className="font-medium text-green-700">{report.trip_summary.legal}</div>
              </div>
              <div className="bg-yellow-50 p-2 rounded">
                <div className="text-gray-500">Bycatch</div>
                <div className="font-medium text-yellow-700">{report.trip_summary.bycatch}</div>
              </div>
              <div className="bg-red-50 p-2 rounded">
                <div className="text-gray-500">Protected</div>
                <div className="font-medium text-red-700">{report.trip_summary.protected}</div>
              </div>
              <div className="bg-blue-50 p-2 rounded">
                <div className="text-gray-500">Released</div>
                <div className="font-medium text-blue-700">{report.trip_summary.released}</div>
              </div>
              <div className="bg-red-50 p-2 rounded">
                <div className="text-gray-500">Violations</div>
                <div className="font-medium text-red-700">{report.trip_summary.unreleased_violations}</div>
              </div>
            </div>
          </div>

          {/* Violations */}
          {report.violations.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Violations</h3>
              <div className="space-y-2">
                {report.violations.map((v, i) => (
                  <div key={i} className="bg-red-50 p-3 rounded border border-red-200">
                    <div className="flex justify-between">
                      <span className="font-medium">{v.species}</span>
                      <span className="text-red-700 font-medium">${v.total_fine}</span>
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {v.count}x {v.status} @ ${v.fine_per_incident} each
                    </div>
                    <div className="text-sm text-gray-500 mt-1">{v.explanation}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Regional Context */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-2">Regional Context</h3>
            <p className="text-sm text-gray-600">{report.regional_context}</p>
          </div>

          {/* Penalties */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-2">Potential Penalties</h3>
            <p className="text-sm text-gray-600">{report.potential_penalties}</p>
          </div>

          {/* Recommendation */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-2">Recommendation</h3>
            <p className="text-sm text-gray-600">{report.recommendation}</p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="w-full py-2 bg-red-500 hover:bg-red-600 text-white rounded font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
