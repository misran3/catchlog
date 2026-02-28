// frontend/components/ImageUpload.tsx
"use client";

import { useCallback, useState } from "react";
import { uploadImage } from "@/lib/api";
import type { Detection } from "@/lib/types";

interface ImageUploadProps {
  onDetection: (detection: Detection) => void;
}

export function ImageUpload({ onDetection }: ImageUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.type.startsWith("image/")) {
        alert("Please upload an image file");
        return;
      }

      setIsUploading(true);
      try {
        const detection = await uploadImage(file);
        onDetection(detection);
      } catch (error) {
        console.error("Upload failed:", error);
        alert("Failed to upload image");
      } finally {
        setIsUploading(false);
      }
    },
    [onDetection]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);

      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      className={`
        border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
        transition-colors duration-200
        ${dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"}
        ${isUploading ? "opacity-50 pointer-events-none" : ""}
      `}
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      onClick={() => document.getElementById("file-input")?.click()}
    >
      <input
        id="file-input"
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleChange}
        disabled={isUploading}
      />

      {isUploading ? (
        <div className="flex items-center justify-center gap-2">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-600">Processing...</span>
        </div>
      ) : (
        <div>
          <div className="text-3xl mb-2">📷</div>
          <p className="text-gray-600">
            Drop image here or <span className="text-blue-500">browse</span>
          </p>
        </div>
      )}
    </div>
  );
}
