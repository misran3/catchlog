import { Camera, Cpu, Database, Volume2, Cloud, Mail } from 'lucide-react';

const steps = [
  {
    icon: Camera,
    title: 'Capture',
    description: 'Deck camera monitors catch in real-time.',
    color: 'ocean',
  },
  {
    icon: Cpu,
    title: 'Identify',
    description: 'PaliGemma 2 detects species with bounding boxes. No internet.',
    color: 'seafoam',
  },
  {
    icon: Database,
    title: 'Log',
    description: 'Species, confidence, GPS, timestamp — tamper-proof audit.',
    color: 'ocean',
  },
  {
    icon: Volume2,
    title: 'Voice Alert',
    description: 'Protected species? Instant audio alarm at sea.',
    color: 'coral',
    hasDemo: true,
  },
  {
    icon: Cloud,
    title: 'Sync',
    description: 'Back at port? Cloud agent reviews full trip log.',
    color: 'seafoam',
  },
  {
    icon: Mail,
    title: 'Report',
    description: 'Violations? Fines calculated, email sent automatically.',
    color: 'ocean',
  },
];

export default function HowItWorks() {
  const playAlertSound = () => {
    const audio = new Audio('/alert.mp3');
    audio.play();
  };

  return (
    <section className="py-16 bg-white/50">
      <div className="section-container">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl font-bold text-navy-800 mb-3">
            How It Works
          </h2>
          <p className="text-text-muted max-w-xl mx-auto">
            Real-time enforcement at sea, automated compliance review at port.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const bgColor = step.color === 'coral' ? 'bg-coral-500' :
                           step.color === 'seafoam' ? 'bg-seafoam-500' : 'bg-ocean-500';
            const lightBg = step.color === 'coral' ? 'bg-coral-400/10' :
                           step.color === 'seafoam' ? 'bg-seafoam-100' : 'bg-ocean-100';

            return (
              <div
                key={step.title}
                className={`relative p-4 rounded-2xl ${lightBg} border border-transparent hover:border-ocean-200 transition-all duration-300 group`}
              >
                {/* Step number */}
                <div className="absolute -top-2 -left-2 w-6 h-6 bg-navy-800 text-white text-xs font-bold rounded-full flex items-center justify-center">
                  {index + 1}
                </div>

                {/* Icon */}
                <div className={`w-12 h-12 ${bgColor} rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>

                {/* Content */}
                <h3 className="font-display font-bold text-navy-800 mb-1">
                  {step.title}
                </h3>
                <p className="text-sm text-text-muted leading-snug">
                  {step.description}
                </p>

                {/* Demo button for sound alert */}
                {step.hasDemo && (
                  <button
                    onClick={playAlertSound}
                    className="mt-2 px-3 py-1 bg-coral-500 text-white text-xs font-semibold rounded-lg hover:bg-coral-400 transition-colors"
                  >
                    Play Demo
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
