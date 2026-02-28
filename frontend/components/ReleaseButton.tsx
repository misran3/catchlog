"use client";

import { useState } from "react";
import { releaseLastCatch } from "@/lib/api";

interface ReleaseButtonProps {
  hasUnreleased: boolean;
  onRelease: () => void;
}

export function ReleaseButton({ hasUnreleased, onRelease }: ReleaseButtonProps) {
  const [isReleasing, setIsReleasing] = useState(false);

  const handleRelease = async () => {
    setIsReleasing(true);
    try {
      await releaseLastCatch();
      onRelease();
    } catch (error) {
      console.error("Release failed:", error);
      alert("Failed to release catch");
    } finally {
      setIsReleasing(false);
    }
  };

  if (!hasUnreleased) {
    return null;
  }

  return (
    <button
      onClick={handleRelease}
      disabled={isReleasing}
      className={`
        w-full py-3 px-4 rounded-lg font-medium text-white
        transition-colors duration-200
        ${isReleasing
          ? "bg-gray-400 cursor-not-allowed"
          : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
        }
      `}
    >
      {isReleasing ? (
        <span className="flex items-center justify-center gap-2">
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          Releasing...
        </span>
      ) : (
        "🔓 Mark as Released"
      )}
    </button>
  );
}
