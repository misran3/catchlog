// frontend/components/VideoFeed.tsx
"use client";

interface VideoFeedProps {
  frameBase64: string | null;
  species?: string;
  status?: string;
}

export function VideoFeed({ frameBase64, species, status }: VideoFeedProps) {
  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <div className="aspect-video relative flex items-center justify-center">
        {frameBase64 ? (
          <>
            <img
              src={frameBase64}
              alt="Detection frame"
              className="w-full h-full object-contain"
            />
            {species && (
              <div
                className={`
                  absolute bottom-4 left-4 px-3 py-1 rounded-full text-sm font-medium
                  ${status === "legal" ? "bg-green-500 text-white" : ""}
                  ${status === "bycatch" ? "bg-yellow-500 text-black" : ""}
                  ${status === "protected" ? "bg-red-500 text-white" : ""}
                  ${status === "unknown" ? "bg-gray-500 text-white" : ""}
                `}
              >
                {species}
              </div>
            )}
          </>
        ) : (
          <div className="text-gray-500 text-center">
            <div className="text-5xl mb-2">🐟</div>
            <p>No image uploaded yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
