import React from 'react';
import { 
  ShieldAlert, 
  Sliders, 
  DollarSign, 
  Key, 
  Headphones, 
  AlertOctagon,
  CheckCircle2,
  Lock
} from 'lucide-react';

/**
 * Enterprise Configurable Risk Threshold & Policy Selector
 * 
 * Directly fulfills client requirement:
 * "Threshold-based alerting logic configurable for different risk scenarios
 * (for example, high-value transaction calls, privileged access approvals)."
 */
export default function PolicyThresholdSelector({ 
  currentScenario, 
  onSelectScenario, 
  customThreshold, 
  onThresholdChange 
}) {
  const scenarios = [
    {
      id: 'high-value-wire',
      label: 'High-Value Wire / RTGS Transfer',
      threshold: 0.40,
      rule: 'RECOMMEND_CALLBACK_VERIFICATION',
      icon: DollarSign,
      badge: 'STRICT (40%)',
      desc: 'Fund transfers ≥ $50K or ₹10L. Dispatches out-of-band cryptographic push before execution.'
    },
    {
      id: 'privileged-access',
      label: 'Privileged CXO / IT Access',
      threshold: 0.45,
      rule: 'MANDATORY_HARDWARE_MFA',
      icon: Key,
      badge: 'STRICT (45%)',
      desc: 'Credential resets, API key generation, or executive overrides. Requires hardware key.'
    },
    {
      id: 'digital-arrest',
      label: 'Digital Arrest / Extortion Shield',
      threshold: 0.35,
      rule: 'IMMEDIATE_EXTORTION_INTERCEPT',
      icon: AlertOctagon,
      badge: 'SENSITIVE (35%)',
      desc: 'Indian law enforcement/CBI impersonation & Aadhaar coercion. Intercepts call immediately.'
    },
    {
      id: 'standard-support',
      label: 'Standard Inbound Support',
      threshold: 0.65,
      rule: 'STEP_UP_SECURITY_QUESTIONS',
      icon: Headphones,
      badge: 'STANDARD (65%)',
      desc: 'Routine banking balance queries. Prompts agent for step-up questions if risk is elevated.'
    }
  ];

  return (
    <div className="p-4 sm:p-5 rounded-2xl border border-forest/15 bg-white shadow-spade space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-forest/10 pb-3">
        <div className="flex items-center gap-2">
          <Sliders size={16} className="text-forest" />
          <h3 className="font-display text-xs font-extrabold text-forest uppercase tracking-wider">
            Configurable Scenario-Based Alerting Logic
          </h3>
        </div>
        <span className="text-[11px] font-mono text-forest/70 font-bold">
          Active Threshold: <strong className="text-forest font-black font-mono">{(customThreshold * 100).toFixed(0)}%</strong>
        </span>
      </div>

      {/* 4 Preset Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {scenarios.map((sc) => {
          const Icon = sc.icon;
          const isSelected = currentScenario === sc.id;
          return (
            <button
              key={sc.id}
              onClick={() => {
                onSelectScenario(sc.id);
                onThresholdChange(sc.threshold);
              }}
              className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between space-y-2 ${
                isSelected
                  ? 'bg-forest text-white border-forest shadow-md ring-2 ring-lemongrass/50'
                  : 'bg-sage-1/50 hover:bg-white text-forest border-forest/15'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                  isSelected ? 'bg-white/20 text-lemongrass' : 'bg-white text-forest border border-forest/10'
                }`}>
                  <Icon size={14} />
                </div>
                <span className={`text-[10px] font-mono font-extrabold px-2 py-0.5 rounded ${
                  isSelected ? 'bg-lemongrass text-forest' : 'bg-forest text-lemongrass'
                }`}>
                  {sc.badge}
                </span>
              </div>

              <div>
                <div className={`font-display text-xs font-extrabold ${isSelected ? 'text-white' : 'text-forest'}`}>
                  {sc.label}
                </div>
                <p className={`text-[10px] leading-tight mt-1 font-sans ${
                  isSelected ? 'text-white/80' : 'text-forest/70'
                }`}>
                  {sc.desc}
                </p>
              </div>

              <div className={`text-[9px] font-mono font-bold pt-1 border-t truncate ${
                isSelected ? 'border-white/15 text-lemongrass' : 'border-forest/10 text-forest/60'
              }`}>
                Policy: {sc.rule}
              </div>
            </button>
          );
        })}
      </div>

      {/* Manual Fine-Tune Slider */}
      <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-2 text-forest/70">
          <Lock size={13} />
          <span>Dynamic Gate: Scores above this threshold trigger automatic step-up verification</span>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-64">
          <span className="text-[10px] text-forest/60">Strict</span>
          <input
            type="range"
            min="0.20"
            max="0.80"
            step="0.05"
            value={customThreshold}
            onChange={(e) => onThresholdChange(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-sage-2 rounded-lg appearance-none cursor-pointer accent-forest"
          />
          <span className="text-[10px] text-forest/60">Permissive</span>
        </div>
      </div>

    </div>
  );
}
