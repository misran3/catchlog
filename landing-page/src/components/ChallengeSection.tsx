import { Check, Sparkles } from 'lucide-react';

const requirements = [
  {
    requirement: 'Fine-tuned on-device model',
    implementation: 'Gemma 3n fine-tuned on FOID fish species dataset',
    met: true,
  },
  {
    requirement: 'Agentic behavior',
    implementation: 'Pydantic AI agent autonomously reviews catch logs against regulations',
    met: true,
  },
  {
    requirement: 'Visual input (camera/video)',
    implementation: 'Real-time camera feed for species detection',
    met: true,
  },
  {
    requirement: 'Genuine on-device reason',
    implementation: 'Fishing vessels operate offline at sea for days',
    met: true,
  },
  {
    requirement: 'Bonus: Audio output',
    implementation: 'Ship alarm sounds for violations detected at sea',
    met: true,
  },
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
            CatchLog was designed from the ground up to meet every hackathon requirement.
          </p>
        </div>

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
