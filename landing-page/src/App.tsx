import { useState } from 'react';
import { Waves, Cpu, ArrowRight, ArrowLeft } from 'lucide-react';
import Hero from './components/Hero';
import HowItWorks from './components/HowItWorks';
import WhyCatchLog from './components/WhyCatchLog';
import ChallengeSection from './components/ChallengeSection';
import UnderTheHood from './components/UnderTheHood';

type View = 'pitch' | 'architecture';

function App() {
  const [view, setView] = useState<View>('pitch');

  return (
    <div className="min-h-screen ocean-gradient">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-ocean-100">
        <div className="section-container py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-ocean-500 to-seafoam-500 flex items-center justify-center">
              <Waves className="w-5 h-5 text-white" />
            </div>
            <span className="font-display text-xl font-bold text-navy-800">CatchLog</span>
          </div>

          <div className="flex items-center gap-2 bg-ocean-50 p-1 rounded-xl">
            <button
              onClick={() => setView('pitch')}
              className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center gap-2 ${
                view === 'pitch'
                  ? 'bg-white text-ocean-700 shadow-sm'
                  : 'text-text-muted hover:text-ocean-600'
              }`}
            >
              <Waves className="w-4 h-4" />
              The Pitch
            </button>
            <button
              onClick={() => setView('architecture')}
              className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center gap-2 ${
                view === 'architecture'
                  ? 'bg-white text-ocean-700 shadow-sm'
                  : 'text-text-muted hover:text-ocean-600'
              }`}
            >
              <Cpu className="w-4 h-4" />
              Under the Hood
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="pt-20">
        {view === 'pitch' ? (
          <div className="animate-fade-in">
            <Hero onViewArchitecture={() => setView('architecture')} />
            <HowItWorks />
            <WhyCatchLog />
            <ChallengeSection />

            {/* View Architecture CTA */}
            <section className="py-12 bg-gradient-to-r from-ocean-500 to-seafoam-500">
              <div className="section-container text-center">
                <button
                  onClick={() => setView('architecture')}
                  className="inline-flex items-center gap-3 px-8 py-4 bg-white text-ocean-700 rounded-2xl font-display font-bold text-lg shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
                >
                  See How It's Built
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </section>
          </div>
        ) : (
          <div className="animate-fade-in">
            <UnderTheHood />

            {/* Back to Pitch CTA */}
            <section className="py-12 bg-gradient-to-r from-navy-800 to-navy-900">
              <div className="section-container text-center">
                <button
                  onClick={() => setView('pitch')}
                  className="inline-flex items-center gap-3 px-8 py-4 bg-ocean-500 text-white rounded-2xl font-display font-bold text-lg shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
                >
                  <ArrowLeft className="w-5 h-5" />
                  Back to The Pitch
                </button>
              </div>
            </section>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="py-6 bg-navy-900 text-center">
        <p className="text-ocean-300 text-sm">
          Built for Google DeepMind × InstaLILY On-Device AI Hackathon
        </p>
      </footer>
    </div>
  );
}

export default App;
