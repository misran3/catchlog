// frontend/components/SyncButton.tsx
"use client";

import { useState } from "react";
import { ComplianceReport } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SyncButtonProps {
  onReport: (report: ComplianceReport) => void;
}

export function SyncButton({ onReport }: SyncButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSync = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/sync`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.statusText}`);
      }

      const report: ComplianceReport = await response.json();
      onReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={handleSync}
        disabled={loading}
        className={`
          px-4 py-2 rounded-lg font-medium text-white
          ${loading
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-700"
          }
        `}
      >
        {loading ? "Syncing..." : "☁️ Sync to Cloud"}
      </button>
      {error && (
        <p className="text-red-500 text-sm">{error}</p>
      )}
    </div>
  );
}
