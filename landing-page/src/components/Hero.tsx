import { Anchor, Shield, Wifi, WifiOff, Volume2 } from 'lucide-react';

interface HeroProps {
  onViewArchitecture: () => void;
}

export default function Hero({ onViewArchitecture }: HeroProps) {
  return (
    <section className="relative py-20 overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute top-20 left-10 w-64 h-64 bg-ocean-200/30 rounded-full blur-3xl animate-wave-slow" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-seafoam-200/30 rounded-full blur-3xl animate-wave-delayed" />

      <div className="section-container relative">
        <div className="max-w-3xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-ocean-100 rounded-full text-ocean-700 text-sm font-medium mb-8 animate-float">
            <span className="w-2 h-2 bg-seafoam-500 rounded-full animate-pulse" />
            Google DeepMind × InstaLILY On-Device AI Hackathon
          </div>

          {/* Headline */}
          <h1 className="font-display text-5xl md:text-6xl font-bold text-navy-800 leading-tight mb-6">
            Your AI Compliance
            <span className="gradient-text block mt-2">Officer at Sea</span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl text-text-muted leading-relaxed mb-10 max-w-2xl mx-auto">
            On-device species detection, real-time regulation enforcement, and voice alerts —
            <strong className="text-navy-800"> 200 miles offshore, no signal, no cloud, no human reviewer</strong>.
          </p>

          {/* Key Points */}
          <div className="flex flex-wrap justify-center gap-3 mb-10">
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl shadow-sm border border-ocean-100">
              <WifiOff className="w-5 h-5 text-ocean-500" />
              <span className="text-sm font-medium text-navy-800">Fully Offline</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl shadow-sm border border-ocean-100">
              <Anchor className="w-5 h-5 text-seafoam-500" />
              <span className="text-sm font-medium text-navy-800">PaliGemma 2 3B</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl shadow-sm border border-ocean-100">
              <Volume2 className="w-5 h-5 text-coral-500" />
              <span className="text-sm font-medium text-navy-800">Voice Alerts</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl shadow-sm border border-ocean-100">
              <Shield className="w-5 h-5 text-ocean-500" />
              <span className="text-sm font-medium text-navy-800">Auto Compliance</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl shadow-sm border border-ocean-100">
              <Wifi className="w-5 h-5 text-seafoam-500" />
              <span className="text-sm font-medium text-navy-800">Cloud Sync</span>
            </div>
          </div>

          {/* CTA */}
          <button
            onClick={onViewArchitecture}
            className="btn btn-primary text-lg px-8 py-4"
          >
            See How It Works
          </button>
        </div>
      </div>
    </section>
  );
}
