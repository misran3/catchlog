"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getState, getAudioUrl } from "@/lib/api";
import type { AppState, Detection } from "@/lib/types";

import { ImageUpload } from "@/components/ImageUpload";
import { VideoFeed } from "@/components/VideoFeed";
import { CatchCounter } from "@/components/CatchCounter";
import { AlertFeed } from "@/components/AlertFeed";
import { ComplianceSummary } from "@/components/ComplianceSummary";
import { ReleaseButton } from "@/components/ReleaseButton";

const INITIAL_STATE: AppState = {
  last_detection: null,
  frame_base64: null,
  counts: {},
  alerts: [],
  compliance: {
    total: 0,
    legal: 0,
    bycatch: 0,
    protected: 0,
    released: 0,
    status: "COMPLIANT",
  },
};

export default function Dashboard() {
  const [state, setState] = useState<AppState>(INITIAL_STATE);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Refresh state from backend
  const refreshState = useCallback(async () => {
    try {
      const newState = await getState();
      setState(newState);
    } catch (error) {
      console.error("Failed to refresh state:", error);
    }
  }, []);

  // Handle new detection
  const handleDetection = useCallback(
    (detection: Detection) => {
      // Play audio alert if present
      if (detection.audio_url && audioRef.current) {
        audioRef.current.src = getAudioUrl(detection.audio_url);
        audioRef.current.play().catch(console.error);
      }

      // Refresh full state
      refreshState();
    },
    [refreshState]
  );

  // Check if there are unreleased bycatch/protected
  const hasUnreleased =
    state.compliance.bycatch + state.compliance.protected > state.compliance.released;

  // Initial load
  useEffect(() => {
    refreshState();
  }, [refreshState]);

  return (
    <div className="max-w-6xl mx-auto p-4">
      {/* Header */}
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">
          CatchLog
        </h1>
        <div className="w-64">
          <ImageUpload onDetection={handleDetection} />
        </div>
      </header>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left column: Video feed */}
        <div className="lg:col-span-2 space-y-4">
          <VideoFeed
            frameBase64={state.frame_base64}
            species={state.last_detection?.species}
            status={state.last_detection?.status}
          />
          <ReleaseButton
            hasUnreleased={hasUnreleased}
            onRelease={refreshState}
          />
        </div>

        {/* Right column: Stats */}
        <div className="space-y-4">
          <CatchCounter counts={state.counts} />
          <ComplianceSummary compliance={state.compliance} />
        </div>
      </div>

      {/* Alert feed */}
      <div className="mt-4">
        <AlertFeed alerts={state.alerts} />
      </div>

      {/* Hidden audio element for alerts */}
      <audio ref={audioRef} className="hidden" />
    </div>
  );
}
