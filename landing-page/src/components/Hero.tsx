import { Anchor, Shield, Wifi, WifiOff } from 'lucide-react';

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
            AI-Powered Fishing
            <span className="gradient-text block mt-2">Compliance at Sea</span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl text-text-muted leading-relaxed mb-10 max-w-2xl mx-auto">
            On-device species detection that works <strong className="text-navy-800">offline</strong>,
            with intelligent cloud compliance review when you're back online.
          </p>

          {/* Key Points */}
          <div className="flex flex-wrap justify-center gap-4 mb-10">
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl shadow-sm border border-ocean-100">
              <WifiOff className="w-5 h-5 text-ocean-500" />
              <span className="text-sm font-medium text-navy-800">Works Offline</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl shadow-sm border border-ocean-100">
              <Anchor className="w-5 h-5 text-seafoam-500" />
              <span className="text-sm font-medium text-navy-800">On-Device AI</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl shadow-sm border border-ocean-100">
              <Wifi className="w-5 h-5 text-ocean-500" />
              <span className="text-sm font-medium text-navy-800">Smart Sync</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl shadow-sm border border-ocean-100">
              <Shield className="w-5 h-5 text-coral-500" />
              <span className="text-sm font-medium text-navy-800">Compliance Agent</span>
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
