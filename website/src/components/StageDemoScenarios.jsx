import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  ShieldAlert, 
  DollarSign, 
  AlertOctagon, 
  CheckCircle2, 
  Play, 
  Loader2, 
  Radio, 
  ArrowRight,
  ShieldCheck
} from 'lucide-react';

/**
 * 1-Click Stage Demo Scenarios Bar
 * 
 * Enables the stage presenter to trigger pre-configured fraud attacks
 * and genuine verification flows with a single click — zero file searching required.
 */
export default function StageDemoScenarios({ onRunScenario, isProcessing }) {
  const [activeScenarioId, setActiveScenarioId] = useState(null);

  const scenarios = [
    {
      id: 'cxo-wire-fraud',
      title: 'High-Value CXO Wire Transfer Impersonation',
      tag: 'CRITICAL ATTACK',
      tagColor: 'bg-rose-600 text-white',
      amount: '$500,000 USD (₹4.15 Cr)',
      sampleFile: '/samples/cxo_wire_transfer_clone.mp3',
      fileName: 'cxo_wire_transfer_clone.mp3',
      threshold: 0.40,
      thresholdId: 'high-value-wire',
      description: 'Cloned voice of CFO David Vance requesting immediate wire transfer to unverified offshore account.',
      context: {
        title: 'High-Value CXO Wire Transfer Intercept',
        amount: '$500,000 USD (₹4,15,00,000)',
        beneficiary: 'Alpha Global Logistics Ltd (IBAN: DE89 3704 ... 9102)',
        callerClaimed: 'David Vance (Chief Financial Officer)',
        callerNumber: '+1 (415) 890-4412 (VoIP / SIP Gateway)',
        tenant: 'Apex Global Financial Corp',
        languageCluster: 'en-IN (Indian Executive English)',
        vishingIntent: 'High Urgency Wire Coercion'
      },
      icon: DollarSign,
      accent: 'border-rose-300 bg-rose-50/50'
    },
    {
      id: 'digital-arrest',
      title: 'CBI / Police "Digital Arrest" Extortion Scam',
      tag: 'INDIAN SCAM DEFENSE',
      tagColor: 'bg-amber-600 text-white',
      amount: '₹2,50,000 Clearance Bond',
      sampleFile: '/samples/digital_arrest_scam_hindi.mp3',
      fileName: 'digital_arrest_scam_hindi.mp3',
      threshold: 0.35,
      thresholdId: 'digital-arrest',
      description: 'Authority impersonation claiming victim\'s Aadhaar is linked to narcotic parcel, demanding extortion bond.',
      context: {
        title: 'Digital Arrest Authority Impersonation',
        amount: '₹2,50,000 INR (Extortion Demand)',
        beneficiary: 'Fake Court Escrow UPI (cbi-clearance@okhdfc)',
        callerClaimed: 'Inspector Rajesh Kumar (CBI Cyber Crime Cell)',
        callerNumber: '+91 98210 44912 (Spoofed Police Telephony)',
        tenant: 'National Telephony Integrity Shield',
        languageCluster: 'hi-IN (Hindi Regional Dialect)',
        vishingIntent: 'Extortion & Arrest Coercion'
      },
      icon: AlertOctagon,
      accent: 'border-amber-300 bg-amber-50/50'
    },
    {
      id: 'bonafide-human',
      title: 'Bonafide Corporate Executive Call',
      tag: 'AUTHENTIC PASS',
      tagColor: 'bg-emerald-600 text-white',
      amount: 'Routine Inquiry',
      sampleFile: '/samples/bonafide_human_sample.mp3',
      fileName: 'bonafide_human_sample.mp3',
      threshold: 0.65,
      thresholdId: 'standard-support',
      description: 'Genuine executive voice with natural human vocal cord micro-jitter, dynamic pitch, and harmonic phase alignment.',
      context: {
        title: 'Corporate Employee Support Inquiry',
        amount: 'N/A (Routine Payroll Verification)',
        beneficiary: 'Verified Internal Account',
        callerClaimed: 'Ananya Sharma (VP Human Resources)',
        callerNumber: '+91 80 4120 9000 (Internal PBX / SIP)',
        tenant: 'Apex Global Financial Corp',
        languageCluster: 'en-IN (Indian English - Standard)',
        vishingIntent: 'Zero Risk (Benign Query)'
      },
      icon: ShieldCheck,
      accent: 'border-emerald-300 bg-emerald-50/50'
    }
  ];

  const handleTriggerScenario = async (sc) => {
    setActiveScenarioId(sc.id);
    try {
      const resp = await fetch(sc.sampleFile);
      if (!resp.ok) {
        throw new Error(`Failed to load scenario audio file: ${sc.sampleFile}`);
      }
      const blob = await resp.blob();
      const file = new File([blob], sc.fileName, { type: 'audio/mp3' });
      
      onRunScenario({
        file,
        scenarioId: sc.id,
        context: sc.context,
        threshold: sc.threshold,
        thresholdId: sc.thresholdId
      });
    } catch (err) {
      console.error('Error triggering stage scenario:', err);
    }
  };

  return (
    <div className="rounded-2xl border border-forest/20 bg-forest text-white p-5 sm:p-6 shadow-spade space-y-4">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-lemongrass animate-pulse" />
          <h2 className="font-display text-sm font-extrabold text-white tracking-wide uppercase">
            Stage Demo Scenarios · 1-Click Attack & Verification Simulator
          </h2>
        </div>
        <span className="text-[11px] font-mono text-lemongrass font-bold bg-white/10 px-2.5 py-0.5 rounded">
          LIVE DEMO MODE
        </span>
      </div>

      <p className="text-xs text-white/80 font-medium">
        Select a real-world enterprise attack scenario below to automatically load the recorded voice stream, apply scenario-specific policy thresholds, and demonstrate multi-layer defense in under 50ms:
      </p>

      {/* 3 Scenario Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 pt-1">
        {scenarios.map((sc) => {
          const Icon = sc.icon;
          const isCurrent = activeScenarioId === sc.id && isProcessing;

          return (
            <div
              key={sc.id}
              className={`p-4 rounded-xl border bg-white text-forest flex flex-col justify-between space-y-3 transition-all hover:shadow-lg ${sc.accent}`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] font-mono font-extrabold px-2 py-0.5 rounded shadow-xs ${sc.tagColor}`}>
                    {sc.tag}
                  </span>
                  <span className="text-[11px] font-mono font-bold text-forest/70">
                    {sc.amount}
                  </span>
                </div>

                <div className="flex items-start gap-2 pt-1">
                  <div className="w-7 h-7 rounded-lg bg-forest/10 flex items-center justify-center text-forest shrink-0 mt-0.5">
                    <Icon size={15} />
                  </div>
                  <h3 className="font-display text-xs font-black text-forest leading-snug">
                    {sc.title}
                  </h3>
                </div>

                <p className="text-[11px] text-forest/80 leading-relaxed font-sans">
                  {sc.description}
                </p>
              </div>

              <div className="pt-2 border-t border-forest/10 flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-forest/60 truncate">
                  Policy: {(sc.threshold * 100).toFixed(0)}% Trigger
                </span>

                <button
                  onClick={() => handleTriggerScenario(sc)}
                  disabled={isProcessing}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-forest text-lemongrass hover:bg-forest-hover font-mono font-extrabold text-xs shadow-xs transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
                >
                  {isCurrent ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <Play size={12} />
                      <span>Run Demo</span>
                    </>
                  )}
                </button>
              </div>

            </div>
          );
        })}
      </div>

    </div>
  );
}
