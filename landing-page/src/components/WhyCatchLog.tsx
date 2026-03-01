import { Ban, DollarSign, Fish, ShieldAlert } from 'lucide-react';

const problems = [
  {
    icon: Ban,
    stat: '$23B',
    label: 'Annual illegal fishing losses',
  },
  {
    icon: Fish,
    stat: '30%',
    label: 'Of global catch is unreported',
  },
  {
    icon: ShieldAlert,
    stat: '85%',
    label: 'Of ocean is under-monitored',
  },
  {
    icon: DollarSign,
    stat: '$500K+',
    label: 'Fines for violations',
  },
];

const solutions = [
  {
    title: 'For Fishers',
    points: ['Know species instantly', 'Automatic compliance logging', 'Avoid accidental violations'],
  },
  {
    title: 'For Regulators',
    points: ['Tamper-proof audit trails', 'Real-time violation alerts', 'Reduced manual inspections'],
  },
  {
    title: 'For Our Oceans',
    points: ['Protect endangered species', 'Sustainable fishing practices', 'Data-driven conservation'],
  },
];

export default function WhyCatchLog() {
  return (
    <section className="py-16">
      <div className="section-container">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl font-bold text-navy-800 mb-3">
            Why CatchLog?
          </h2>
          <p className="text-text-muted max-w-xl mx-auto">
            The fishing industry has a compliance problem. We're solving it with AI.
          </p>
        </div>

        {/* Problem Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          {problems.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="card text-center">
                <Icon className="w-8 h-8 text-coral-500 mx-auto mb-2" />
                <div className="font-display text-2xl font-bold text-navy-800">{item.stat}</div>
                <div className="text-sm text-text-muted">{item.label}</div>
              </div>
            );
          })}
        </div>

        {/* Solutions */}
        <div className="grid md:grid-cols-3 gap-6">
          {solutions.map((solution) => (
            <div key={solution.title} className="card">
              <h3 className="font-display font-bold text-lg text-ocean-700 mb-4">
                {solution.title}
              </h3>
              <ul className="space-y-2">
                {solution.points.map((point) => (
                  <li key={point} className="flex items-start gap-2 text-text-muted">
                    <span className="w-1.5 h-1.5 bg-seafoam-500 rounded-full mt-2 flex-shrink-0" />
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
