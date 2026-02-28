// frontend/lib/api.ts

import type { Detection, AppState, ReleaseResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadImage(file: File): Promise<Detection> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getState(): Promise<AppState> {
  const response = await fetch(`${API_BASE}/api/state`);

  if (!response.ok) {
    throw new Error(`Failed to get state: ${response.statusText}`);
  }

  return response.json();
}

export async function releaseLastCatch(): Promise<ReleaseResponse> {
  const response = await fetch(`${API_BASE}/api/release`, {
    method: "POST",
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("No unreleased catch to release");
    }
    throw new Error(`Release failed: ${response.statusText}`);
  }

  return response.json();
}

export function getAudioUrl(path: string): string {
  return `${API_BASE}${path}`;
}
