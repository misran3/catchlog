// frontend/components/CatchCounter.tsx
"use client";

interface CatchCounterProps {
  counts: Record<string, number>;
}

// Map species to their status for styling
const SPECIES_STATUS: Record<string, "legal" | "bycatch" | "protected" | "unknown"> = {
  "Albacore Tuna": "legal",
  "Bigeye Tuna": "legal",
  "Mahi-Mahi": "legal",
  "Yellowfin Tuna": "legal",
  "Shark": "bycatch",
  "Opah": "bycatch",
  "Pelagic Stingray": "protected",
  "Unknown": "unknown",
};

export function CatchCounter({ counts }: CatchCounterProps) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-semibold mb-3 text-gray-800">Catch Counter</h2>

      {entries.length === 0 ? (
        <p className="text-gray-500 text-sm">No catches recorded</p>
      ) : (
        <div className="space-y-2">
          {entries.map(([species, count]) => {
            const status = SPECIES_STATUS[species] || "unknown";
            return (
              <div
                key={species}
                className="flex items-center justify-between py-1"
              >
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full
                      ${status === "legal" ? "bg-green-500" : ""}
                      ${status === "bycatch" ? "bg-yellow-500" : ""}
                      ${status === "protected" ? "bg-red-500" : ""}
                      ${status === "unknown" ? "bg-gray-400" : ""}
                    `}
                  />
                  <span className="text-sm text-gray-700">{species}</span>
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {count}
                  {status === "bycatch" && " ⚠️"}
                  {status === "protected" && " 🚨"}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
