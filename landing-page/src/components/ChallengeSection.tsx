import { Check, Sparkles, Database } from 'lucide-react';

const requirements = [
  {
    requirement: 'Fine-tuned on-device model',
    implementation: 'PaliGemma 2 3B fine-tuned with QLoRA on 140K real vessel images',
    met: true,
  },
  {
    requirement: 'Agentic behavior',
    implementation: 'On-device agent enforces regulations; cloud agent reviews full audit log',
    met: true,
  },
  {
    requirement: 'Visual input (camera/video)',
    implementation: 'Real-time deck camera feed with bounding box detection',
    met: true,
  },
  {
    requirement: 'Genuine on-device reason',
    implementation: 'Vessels operate 200+ miles offshore with no connectivity for days',
    met: true,
  },
  {
    requirement: 'Bonus: Voice alerts',
    implementation: 'Instant audio alerts when protected species detected at sea',
    met: true,
  },
];

const modelStats = [
  { label: 'Training Images', value: '140K', sub: 'Real vessel camera footage' },
  { label: 'Species Detected', value: '12', sub: 'With bounding boxes' },
  { label: 'LoRA Adapter', value: '45MB', sub: 'Runs on edge hardware' },
  { label: 'Base Model', value: 'PaliGemma 2', sub: '3B parameters' },
];

export default function ChallengeSection() {
  return (
    <section className="py-16 bg-navy-800">
      <div className="section-container">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-ocean-500/20 rounded-full text-ocean-300 text-sm font-medium mb-4">
            <Sparkles className="w-4 h-4" />
            Hackathon Challenge Fit
          </div>
          <h2 className="font-display text-3xl font-bold text-white mb-3">
            Built for the Challenge
          </h2>
          <p className="text-ocean-200 max-w-xl mx-auto">
            Every requirement met with real-world fishing compliance use case.
          </p>
        </div>

        {/* Model Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {modelStats.map((stat) => (
            <div key={stat.label} className="bg-white/5 rounded-xl p-4 text-center">
              <div className="font-display text-2xl font-bold text-seafoam-400">{stat.value}</div>
              <div className="text-white text-sm font-medium">{stat.label}</div>
              <div className="text-ocean-300 text-xs">{stat.sub}</div>
            </div>
          ))}
        </div>

        {/* Dataset Badge */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex items-center gap-3 px-5 py-3 bg-ocean-500/20 rounded-xl">
            <Database className="w-5 h-5 text-ocean-400" />
            <span className="text-ocean-200 text-sm">
              Trained on <strong className="text-white">The Nature Conservancy's Fishnet Dataset</strong>
            </span>
          </div>
        </div>

        {/* Requirements Checklist */}
        <div className="max-w-2xl mx-auto space-y-3">
          {requirements.map((item) => (
            <div
              key={item.requirement}
              className={`flex items-start gap-4 p-4 rounded-xl ${
                item.met ? 'bg-seafoam-500/10' : 'bg-white/5'
              }`}
            >
              <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                item.met ? 'bg-seafoam-500' : 'bg-text-muted'
              }`}>
                <Check className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1">
                <div className={`font-medium ${item.met ? 'text-white' : 'text-text-muted'}`}>
                  {item.requirement}
                </div>
                <div className="text-sm text-ocean-300 mt-0.5">
                  {item.implementation}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
