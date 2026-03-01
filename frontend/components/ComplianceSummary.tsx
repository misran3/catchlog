"use client";

import type { Compliance } from "@/lib/types";

interface ComplianceSummaryProps {
  compliance: Compliance;
}

export function ComplianceSummary({ compliance }: ComplianceSummaryProps) {
  const isCompliant = compliance.status === "COMPLIANT";

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-semibold mb-3 text-gray-800">Compliance</h2>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Total Catch</span>
          <span className="font-medium text-gray-800">{compliance.total}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Legal</span>
          <span className="font-medium text-green-600">{compliance.legal}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Bycatch</span>
          <span className="font-medium text-yellow-600">{compliance.bycatch}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Protected</span>
          <span className="font-medium text-red-600">{compliance.protected}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Released</span>
          <span className="font-medium text-blue-600">{compliance.released}</span>
        </div>

        <div className="border-t pt-2 mt-2">
          <div
            className={`
              flex items-center justify-center gap-2 py-2 rounded-lg font-medium
              ${isCompliant ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}
            `}
          >
            {isCompliant ? "✓" : "⚠"} {compliance.status.replace("_", " ")}
          </div>
        </div>
      </div>
    </div>
  );
}
