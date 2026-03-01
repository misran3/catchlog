import { Ban, DollarSign, Fish, Video, Eye, AlertTriangle } from 'lucide-react';

const problems = [
  {
    icon: DollarSign,
    stat: '$10-50B',
    label: 'Annual IUU fishing losses',
  },
  {
    icon: Fish,
    stat: '9.1M',
    label: 'Tonnes bycatch discarded/year',
  },
  {
    icon: Eye,
    stat: '<2%',
    label: 'Of global fishing monitored',
  },
  {
    icon: Video,
    stat: '100+',
    label: 'EM programs require cameras',
  },
];

const painPoints = [
  {
    icon: AlertTriangle,
    title: 'The Problem Today',
    points: [
      'Nearly all vessel footage reviewed manually on shore',
      'NOAA: Video review is the single largest cost',
      'Data often arrives months late',
      'Most solutions need cloud or six-figure custom builds',
    ],
  },
  {
    icon: Ban,
    title: 'What\'s at Stake',
    points: [
      '14 EM programs in the U.S. alone',
      'Companies like Ai.Fish rely on post-trip cloud review',
      'Fishers can\'t get real-time compliance feedback',
      'Protected species caught without immediate alerts',
    ],
  },
];

const solutions = [
  {
    title: 'For Fishers',
    points: ['Real-time species ID at sea', 'Instant voice alerts for violations', 'Avoid fines before they happen'],
  },
  {
    title: 'For Regulators',
    points: ['Tamper-proof audit trails', 'Automated compliance reports', 'Eliminate manual video review'],
  },
  {
    title: 'For Our Oceans',
    points: ['Protect endangered species in real-time', 'Reduce bycatch mortality', 'Data-driven conservation'],
  },
];

export default function WhyCatchLog() {
  return (
    <section className="py-16">
      <div className="section-container">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl font-bold text-navy-800 mb-3">
            A Validated & Urgent Problem
          </h2>
          <p className="text-text-muted max-w-2xl mx-auto">
            Electronic monitoring is mandated worldwide, but nearly all footage is reviewed manually on shore.
            CatchLog brings AI directly onto the vessel.
          </p>
        </div>

        {/* Problem Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
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

        {/* Pain Points */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {painPoints.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.title} className="card bg-coral-400/5 border-coral-200">
                <div className="flex items-center gap-2 mb-3">
                  <Icon className="w-5 h-5 text-coral-500" />
                  <h3 className="font-display font-bold text-lg text-navy-800">{item.title}</h3>
                </div>
                <ul className="space-y-2">
                  {item.points.map((point) => (
                    <li key={point} className="flex items-start gap-2 text-text-muted text-sm">
                      <span className="w-1.5 h-1.5 bg-coral-500 rounded-full mt-1.5 flex-shrink-0" />
                      {point}
                    </li>
                  ))}
                </ul>
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
