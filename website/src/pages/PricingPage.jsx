import React from 'react';
import { motion } from 'framer-motion';
import { Check, Zap, Building2, Sparkles, ArrowRight, ShieldCheck, CreditCard } from 'lucide-react';

const tiers = [
  {
    name: 'Developer / Free',
    price: '₹0',
    period: 'forever',
    description: 'Get started testing SatyaDhVani 2 voice deepfake detection',
    icon: Sparkles,
    features: [
      '100 detections per day',
      '5MB max file size',
      'REST API access',
      'Real / Fake verdict output',
      'Confidence score metrics',
      'Community documentation',
    ],
    cta: 'Get Free API Key',
    highlight: false,
  },
  {
    name: 'Pro Metered',
    price: '₹0.50',
    period: 'per detection',
    description: 'For production web applications and IVR systems',
    icon: Zap,
    features: [
      '100,000 detections per day',
      '25MB max file size',
      'Batch API endpoint access',
      'Sub-50ms P99 latency SLA',
      'API usage dashboard & metrics',
      'Email support (24h SLA)',
      'Webhook callback alerts',
    ],
    cta: 'Start Pro Metered',
    highlight: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: 'volume contract',
    description: 'For large financial institutions and telecom backbones',
    icon: Building2,
    features: [
      'Unlimited detection throughput',
      '100MB max file size',
      'Dedicated C++ ONNX cluster',
      'On-premise air-gapped deploy',
      '99.99% uptime guarantee',
      'Dedicated security engineer',
      'Custom acoustic model tuning',
      'RAM-only zero data retention SLA',
    ],
    cta: 'Contact Enterprise Sales',
    highlight: false,
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-white text-forest selection:bg-lemongrass py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-sage-1 border border-forest/15 text-forest font-mono text-xs font-semibold">
            <CreditCard size={14} /> PAY-AS-YOU-GO METERED BILLING
          </div>

          <h1 className="font-display text-4xl sm:text-5xl font-extrabold text-forest tracking-tight">
            Simple, transparent pricing
          </h1>

          <p className="text-forest/70 font-normal text-base sm:text-lg">
            Start free with zero commitment. Scale seamlessly as your voice stream throughput grows.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {tiers.map((tier, i) => {
            const Icon = tier.icon;
            return (
              <div
                key={tier.name}
                className={`relative rounded-2xl p-8 flex flex-col spade-cut-md transition-all ${
                  tier.highlight
                    ? 'bg-forest text-white shadow-spade-lg border-2 border-forest'
                    : 'bg-sage-1 text-forest border border-forest/10 hover:border-forest/30'
                }`}
              >
                {tier.highlight && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="px-3.5 py-1 rounded-full bg-lemongrass text-forest text-[11px] font-mono font-bold uppercase tracking-wider shadow-sm">
                      Most Popular Tier
                    </span>
                  </div>
                )}

                {/* Header */}
                <div className="mb-6 space-y-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold ${
                      tier.highlight ? 'bg-lemongrass text-forest' : 'bg-forest text-lemongrass'
                    }`}>
                      <Icon size={18} />
                    </div>
                    <h3 className="font-display text-xl font-bold">{tier.name}</h3>
                  </div>

                  <div className="flex items-baseline gap-1 pt-1">
                    <span className="text-4xl font-extrabold font-display">{tier.price}</span>
                    <span className={`text-xs font-mono ${tier.highlight ? 'text-white/70' : 'text-forest/70'}`}>
                      / {tier.period}
                    </span>
                  </div>
                  <p className={`text-xs font-normal leading-relaxed ${tier.highlight ? 'text-white/80' : 'text-forest/70'}`}>
                    {tier.description}
                  </p>
                </div>

                {/* Features list */}
                <ul className="space-y-3 flex-1 mb-8 pt-2">
                  {tier.features.map((feat) => (
                    <li key={feat} className="flex items-start gap-2.5 text-xs font-medium">
                      <Check className={`w-4 h-4 mt-0.5 shrink-0 ${tier.highlight ? 'text-lemongrass' : 'text-forest'}`} />
                      <span className={tier.highlight ? 'text-white/90' : 'text-forest/80'}>{feat}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA Button */}
                <button
                  className={`w-full py-3.5 rounded-md font-semibold text-sm transition-all flex items-center justify-center gap-2 cursor-pointer shadow-sm ${
                    tier.highlight
                      ? 'bg-lemongrass text-forest hover:bg-lemongrass-hover font-bold'
                      : 'bg-forest text-lemongrass hover:bg-forest-hover font-semibold'
                  }`}
                >
                  <span>{tier.cta}</span>
                  <ArrowRight size={15} />
                </button>
              </div>
            );
          })}
        </div>

        {/* Feature Comparison Table */}
        <section className="bg-sage-1 border border-forest/10 rounded-2xl overflow-hidden spade-cut-md shadow-spade">
          <div className="px-8 py-5 bg-white border-b border-forest/10">
            <h3 className="font-display text-xl font-bold text-forest">Detailed Tier Comparison Matrix</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-sage-2 text-forest border-b border-forest/10 font-bold">
                <tr>
                  <th className="py-3.5 px-6">Specification</th>
                  <th className="py-3.5 px-6 text-center">Free</th>
                  <th className="py-3.5 px-6 text-center text-forest font-extrabold">Pro Metered</th>
                  <th className="py-3.5 px-6 text-center">Enterprise</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-forest/5 text-forest/80">
                {[
                  ['Daily Detection Capacity', '100 requests', '100,000 requests', 'Unlimited'],
                  ['Max File Size', '5MB', '25MB', '100MB'],
                  ['Batch Processing API', '—', '✓ (10 items/req)', '✓ (50 items/req)'],
                  ['Latency Guarantee SLA', 'Best effort', '<100ms P95', '<50ms P99'],
                  ['Usage & Metering Dashboard', '✓', '✓', '✓'],
                  ['API Key Provisioning', '1 key', '5 keys', 'Unlimited keys'],
                  ['Webhook Callback System', '—', '✓', '✓'],
                  ['Air-Gapped Deployment', '—', '—', '✓'],
                  ['Custom Acoustic Fine-Tuning', '—', '—', '✓'],
                  ['Support SLA', 'Community', 'Email (24h SLA)', 'Dedicated Engineer'],
                ].map(([feature, free, pro, enterprise], i) => (
                  <tr key={i} className="hover:bg-white/60 transition-colors">
                    <td className="py-3.5 px-6 font-bold text-forest font-sans">{feature}</td>
                    <td className="py-3.5 px-6 text-center">{free}</td>
                    <td className="py-3.5 px-6 text-center text-forest font-bold">{pro}</td>
                    <td className="py-3.5 px-6 text-center">{enterprise}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

      </div>
    </div>
  );
}
