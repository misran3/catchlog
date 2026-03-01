import { Camera, Cpu, Database, Cloud, Mail, FileText, Smartphone, Server, Bot, Volume2 } from 'lucide-react';

export default function UnderTheHood() {
  return (
    <section className="py-20">
      <div className="section-container">
        <div className="text-center mb-12">
          <h2 className="font-display text-4xl font-bold text-navy-800 mb-4">
            Under the Hood
          </h2>
          <p className="text-text-muted max-w-2xl mx-auto">
            Real-time enforcement at sea with on-device AI, automated compliance review on shore with cloud agents.
          </p>
        </div>

        {/* Architecture Diagram */}
        <div className="grid lg:grid-cols-2 gap-8 mb-12">
          {/* On-Device Phase */}
          <div className="card p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-ocean-500 rounded-xl flex items-center justify-center">
                <Smartphone className="w-5 h-5 text-white" />
              </div>
              <h3 className="font-display text-xl font-bold text-navy-800">
                Phase 1: At Sea (Offline)
              </h3>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-4 p-3 bg-ocean-50 rounded-xl">
                <Camera className="w-6 h-6 text-ocean-500 mt-0.5" />
                <div>
                  <div className="font-medium text-navy-800">Deck Camera</div>
                  <div className="text-sm text-text-muted">Real-time video stream from vessel camera</div>
                </div>
              </div>

              <div className="flex items-start gap-4 p-3 bg-ocean-50 rounded-xl">
                <Cpu className="w-6 h-6 text-seafoam-500 mt-0.5" />
                <div>
                  <div className="font-medium text-navy-800">PaliGemma 2 3B + QLoRA</div>
                  <div className="text-sm text-text-muted">45MB adapter detects 12 species with bounding boxes</div>
                </div>
              </div>

              <div className="flex items-start gap-4 p-3 bg-ocean-50 rounded-xl">
                <Database className="w-6 h-6 text-ocean-500 mt-0.5" />
                <div>
                  <div className="font-medium text-navy-800">Local Audit Log</div>
                  <div className="text-sm text-text-muted">Species, confidence, timestamp, GPS — tamper-proof</div>
                </div>
              </div>

              <div className="flex items-start gap-4 p-3 bg-coral-400/10 rounded-xl">
                <Volume2 className="w-6 h-6 text-coral-500 mt-0.5" />
                <div>
                  <div className="font-medium text-navy-800">Voice Alerts</div>
                  <div className="text-sm text-text-muted">Instant audio alarm when protected species detected</div>
                </div>
              </div>
            </div>
          </div>

          {/* Cloud Phase */}
          <div className="card p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-seafoam-500 rounded-xl flex items-center justify-center">
                <Cloud className="w-5 h-5 text-white" />
              </div>
              <h3 className="font-display text-xl font-bold text-navy-800">
                Phase 2: At Port (Online)
              </h3>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-4 p-3 bg-seafoam-50 rounded-xl">
                <Server className="w-6 h-6 text-seafoam-500 mt-0.5" />
                <div>
                  <div className="font-medium text-navy-800">FastAPI Backend</div>
                  <div className="text-sm text-text-muted">Receives full trip audit log on sync</div>
                </div>
              </div>

              <div className="flex items-start gap-4 p-3 bg-seafoam-50 rounded-xl">
                <Bot className="w-6 h-6 text-ocean-500 mt-0.5" />
                <div>
                  <div className="font-medium text-navy-800">Claude on AWS Bedrock</div>
                  <div className="text-sm text-text-muted">Reviews catches against regulations, calculates fines</div>
                </div>
              </div>

              <div className="flex items-start gap-4 p-3 bg-seafoam-50 rounded-xl">
                <Mail className="w-6 h-6 text-ocean-500 mt-0.5" />
                <div>
                  <div className="font-medium text-navy-800">AWS SES Alerts</div>
                  <div className="text-sm text-text-muted">Email notifications for unresolved violations</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tech Stack */}
        <div className="card p-8">
          <h3 className="font-display text-xl font-bold text-navy-800 mb-6 text-center">
            Tech Stack
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            <div className="text-center">
              <div className="w-14 h-14 bg-gradient-to-br from-ocean-500 to-ocean-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🔮</span>
              </div>
              <div className="font-medium text-navy-800">PaliGemma 2</div>
              <div className="text-xs text-text-muted">3B Vision Model</div>
            </div>

            <div className="text-center">
              <div className="w-14 h-14 bg-gradient-to-br from-seafoam-500 to-seafoam-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🎯</span>
              </div>
              <div className="font-medium text-navy-800">QLoRA</div>
              <div className="text-xs text-text-muted">45MB Adapter</div>
            </div>

            <div className="text-center">
              <div className="w-14 h-14 bg-gradient-to-br from-ocean-400 to-ocean-500 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">⚡</span>
              </div>
              <div className="font-medium text-navy-800">FastAPI</div>
              <div className="text-xs text-text-muted">Python Backend</div>
            </div>

            <div className="text-center">
              <div className="w-14 h-14 bg-gradient-to-br from-ocean-400 to-seafoam-500 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🧠</span>
              </div>
              <div className="font-medium text-navy-800">Pydantic AI</div>
              <div className="text-xs text-text-muted">Agent Framework</div>
            </div>

            <div className="text-center">
              <div className="w-14 h-14 bg-gradient-to-br from-coral-400 to-coral-500 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">☁️</span>
              </div>
              <div className="font-medium text-navy-800">AWS Bedrock</div>
              <div className="text-xs text-text-muted">Claude LLM</div>
            </div>
          </div>
        </div>

        {/* Data Flow */}
        <div className="mt-8 p-6 bg-navy-900 rounded-2xl">
          <h4 className="font-display font-bold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-ocean-400" />
            Data Flow
          </h4>
          <div className="font-mono text-sm text-ocean-200 space-y-2">
            <div className="flex items-start gap-3">
              <span className="text-ocean-400 flex-shrink-0">1.</span>
              <span>Deck camera → PaliGemma 2 → Species + bbox detection (on-device)</span>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-ocean-400 flex-shrink-0">2.</span>
              <span>Detection → Local audit log (species, confidence, GPS, timestamp)</span>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-coral-400 flex-shrink-0">3.</span>
              <span className="text-coral-300">Protected species? → Voice alert sounds immediately</span>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-ocean-400 flex-shrink-0">4.</span>
              <span>Vessel returns to port → Sync full trip audit log</span>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-ocean-400 flex-shrink-0">5.</span>
              <span>Cloud agent → Reviews against regulations → Calculates fines</span>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-ocean-400 flex-shrink-0">6.</span>
              <span>Unresolved violations → Email alert via AWS SES</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
