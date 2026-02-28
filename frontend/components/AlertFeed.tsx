// frontend/components/AlertFeed.tsx
"use client";

import type { Alert } from "@/lib/types";

interface AlertFeedProps {
  alerts: Alert[];
}

export function AlertFeed({ alerts }: AlertFeedProps) {
  // Show most recent first
  const sortedAlerts = [...alerts].reverse();

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-semibold mb-3 text-gray-800">Alert Feed</h2>

      {sortedAlerts.length === 0 ? (
        <p className="text-gray-500 text-sm">No alerts</p>
      ) : (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {sortedAlerts.map((alert, index) => {
            const time = new Date(alert.timestamp).toLocaleTimeString();
            return (
              <div
                key={`${alert.timestamp}-${index}`}
                className={`
                  flex items-start gap-2 text-sm p-2 rounded
                  ${alert.level === "info" ? "bg-gray-50" : ""}
                  ${alert.level === "warning" ? "bg-yellow-50" : ""}
                  ${alert.level === "critical" ? "bg-red-50" : ""}
                `}
              >
                <span className="text-gray-400 text-xs whitespace-nowrap">
                  {time}
                </span>
                <span
                  className={`
                    ${alert.level === "info" ? "text-gray-600" : ""}
                    ${alert.level === "warning" ? "text-yellow-700" : ""}
                    ${alert.level === "critical" ? "text-red-700 font-medium" : ""}
                  `}
                >
                  {alert.level === "warning" && "⚠️ "}
                  {alert.level === "critical" && "🚨 "}
                  {alert.message}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
