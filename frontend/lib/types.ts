// frontend/lib/types.ts

export interface Detection {
  detection_id: number;
  timestamp: string;
  species: string;
  status: "legal" | "bycatch" | "protected" | "unknown";
  confidence: number;
  bbox: [number, number, number, number];
  alert_level: "none" | "info" | "warning" | "critical";
  audio_url: string | null;
}

export interface Alert {
  timestamp: string;
  message: string;
  level: "info" | "warning" | "critical";
}

export interface Compliance {
  total: number;
  legal: number;
  bycatch: number;
  protected: number;
  released: number;
  status: "COMPLIANT" | "ACTION_REQUIRED";
}

export interface AppState {
  last_detection: Detection | null;
  frame_base64: string | null;
  counts: Record<string, number>;
  alerts: Alert[];
  compliance: Compliance;
}

export interface ReleaseResponse {
  released_id: number;
  species: string;
  compliance_status: string;
}
