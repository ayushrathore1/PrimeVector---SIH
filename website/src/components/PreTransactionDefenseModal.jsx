import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldAlert,
  PhoneCall,
  Smartphone,
  Users,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Lock,
  ArrowRight,
  RefreshCw,
  Send,
  X
} from 'lucide-react';

/**
 * Pre-Transaction Banking Defense HUD & Out-of-Band Escalation Modal
 * 
 * Directly fulfills client requirements:
 * "Pre-transaction warning prompts recommending secondary verification such as
 * call-back, multifactor authentication, or escalation to supervisors.
 * Configurable workflows for banks, enterprises, and government agencies."
 */
export default function PreTransactionDefenseModal({ 
  isOpen, 
  onClose, 
  riskScore = 0.97, 
  transactionContext = null 
}) {
  const [activeStep, setActiveStep] = useState(1);
  const [challengeStatus, setChallengeStatus] = useState('pending'); // 'pending' | 'dispatched' | 'fraud_confirmed' | 'approved'
  const [actionLog, setActionLog] = useState([
    { time: '12:04:18', msg: 'Dhwani 2 Neural Classifier flagged voice stream as AI clone (97.4% risk).' },
    { time: '12:04:19', msg: 'Core Banking API rule triggered: AUTOMATIC_PRE_TRANSACTION_HOLD.' }
  ]);

  if (!isOpen) return null;

  const context = transactionContext || {
    title: 'High-Value CXO Wire Transfer Intercept',
    amount: '$500,000 USD (₹4,15,00,000)',
    beneficiary: 'Alpha Global Logistics Ltd (IBAN: DE89 3704 ... 9102)',
    callerClaimed: 'David Vance (Chief Financial Officer)',
    callerNumber: '+1 (415) 890-4412 (VoIP / SIP Gateway)',
    tenant: 'Apex Global Financial Corp'
  };

  const handleDispatchPush = () => {
    setChallengeStatus('dispatched');
    setActionLog(prev => [
      ...prev,
      { time: new Date().toLocaleTimeString(), msg: 'Out-of-band cryptographic push sent to registered CXO device (iPhone 16 Pro).' }
    ]);
  };

  const handleSimulateResponse = (fraud) => {
    if (fraud) {
      setChallengeStatus('fraud_confirmed');
      setActionLog(prev => [
        ...prev,
        { time: new Date().toLocaleTimeString(), msg: 'CXO responded via Push: "FRAUD DETECTED - I am not on this call!" Transaction permanently BLOCKED.' },
        { time: new Date().toLocaleTimeString(), msg: 'Incident report PV-SEC-9921 generated and synced to Bank SIEM/SOC.' }
      ]);
    } else {
      setChallengeStatus('approved');
      setActionLog(prev => [
        ...prev,
        { time: new Date().toLocaleTimeString(), msg: 'CXO authenticated via biometric FaceID. Hold lifted by Supervisor.' }
      ]);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-forest/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 15 }}
        className="w-full max-w-3xl bg-white rounded-2xl border border-forest/20 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
      >
        {/* Modal Header */}
        <div className="bg-rose-600 text-white p-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
              <ShieldAlert className="w-6 h-6 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono font-bold bg-white/20 px-2 py-0.5 rounded tracking-wide uppercase">
                  BANKING CRITICAL INTERVENTION
                </span>
                <span className="text-xs font-mono font-extrabold text-lemongrass">
                  RULE: PRE_TRANSACTION_INTERCEPT
                </span>
              </div>
              <h3 className="text-lg font-display font-extrabold tracking-tight mt-0.5">
                Impersonation Alert: Wire Transfer Frozen
              </h3>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 overflow-y-auto">
          
          {/* Active Transaction Intercept Card */}
          <div className="p-4 rounded-xl bg-rose-50/80 border border-rose-200 text-forest space-y-3 font-mono text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-rose-200/80 pb-2.5">
              <span className="font-bold text-rose-900 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle size={14} className="text-rose-600" />
                Interception Context: {context.title}
              </span>
              <span className="bg-rose-600 text-white font-extrabold px-2.5 py-0.5 rounded text-[11px]">
                STATUS: FUNDS HELD (0% LEAKAGE)
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div>
                <span className="text-[10px] text-forest/60 block uppercase font-bold">Transfer Amount:</span>
                <span className="text-base font-black text-rose-950">{context.amount}</span>
              </div>
              <div>
                <span className="text-[10px] text-forest/60 block uppercase font-bold">Beneficiary:</span>
                <span className="text-xs font-bold text-forest truncate block">{context.beneficiary}</span>
              </div>
              <div>
                <span className="text-[10px] text-forest/60 block uppercase font-bold">Claimed Caller:</span>
                <span className="text-xs font-bold text-forest">{context.callerClaimed}</span>
              </div>
              <div>
                <span className="text-[10px] text-forest/60 block uppercase font-bold">Origin Telephony:</span>
                <span className="text-xs font-bold text-forest">{context.callerNumber}</span>
              </div>
            </div>
          </div>

          {/* Out-of-Band Secondary Verification Workflow */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-display text-sm font-extrabold text-forest uppercase tracking-wider flex items-center gap-2">
                <Lock size={15} className="text-forest" />
                <span>Multi-Channel Frontline Intervention Workflow</span>
              </h4>
              <span className="text-xs font-mono text-forest/60">Zero-Trust Call Protocol</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              
              {/* Action 1: Out-of-Band Hardware MFA */}
              <div className={`p-4 rounded-xl border transition-all ${
                activeStep === 1 ? 'border-forest bg-sage-1/70 shadow-sm' : 'border-forest/15 bg-white'
              }`}>
                <div className="flex items-center gap-2 text-forest mb-2">
                  <Smartphone size={16} className="text-forest shrink-0" />
                  <span className="text-xs font-mono font-bold">Step 1: OOB Push</span>
                </div>
                <p className="text-[11px] text-forest/70 mb-3 leading-relaxed">
                  Cryptographic push challenge sent directly to CXO device outside the telephony channel.
                </p>
                {challengeStatus === 'pending' && (
                  <button
                    onClick={handleDispatchPush}
                    className="w-full py-2 px-3 rounded-lg bg-forest text-lemongrass font-mono font-bold text-xs hover:bg-forest-hover transition-all cursor-pointer"
                  >
                    Dispatch OOB Push
                  </button>
                )}
                {challengeStatus === 'dispatched' && (
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded block text-center animate-pulse">
                      Awaiting CXO Biometric Tap...
                    </span>
                    <div className="flex gap-1.5">
                      <button
                        onClick={() => handleSimulateResponse(true)}
                        className="flex-1 py-1.5 rounded bg-rose-600 hover:bg-rose-700 text-white font-mono font-bold text-[10px] cursor-pointer"
                      >
                        Fraud Confirmed
                      </button>
                      <button
                        onClick={() => handleSimulateResponse(false)}
                        className="flex-1 py-1.5 rounded bg-emerald-600 hover:bg-emerald-700 text-white font-mono font-bold text-[10px] cursor-pointer"
                      >
                        Approve
                      </button>
                    </div>
                  </div>
                )}
                {challengeStatus === 'fraud_confirmed' && (
                  <span className="text-[10px] font-mono font-extrabold text-rose-800 bg-rose-100 px-2 py-1 rounded block text-center">
                    ❌ CONFIRMED FRAUD (BLOCKED)
                  </span>
                )}
                {challengeStatus === 'approved' && (
                  <span className="text-[10px] font-mono font-extrabold text-emerald-800 bg-emerald-100 px-2 py-1 rounded block text-center">
                    ✔ AUTHENTICATED
                  </span>
                )}
              </div>

              {/* Action 2: Automated Telecom Call-Back */}
              <div className="p-4 rounded-xl border border-forest/15 bg-white space-y-2">
                <div className="flex items-center gap-2 text-forest mb-2">
                  <PhoneCall size={16} className="text-forest shrink-0" />
                  <span className="text-xs font-mono font-bold">Step 2: Telecom Call-Back</span>
                </div>
                <p className="text-[11px] text-forest/70 mb-3 leading-relaxed">
                  Initiate cryptographic out-of-band call to verified SIM registered with telecom operator.
                </p>
                <button
                  onClick={() => {
                    setActionLog(prev => [
                      ...prev,
                      { time: new Date().toLocaleTimeString(), msg: 'Automated PSTN call-back initiated to carrier verified SIM IMSI.' }
                    ]);
                  }}
                  className="w-full py-2 px-3 rounded-lg bg-white border border-forest/20 text-forest font-mono font-bold text-xs hover:bg-sage-1 transition-all cursor-pointer"
                >
                  Trigger Call-Back
                </button>
              </div>

              {/* Action 3: Supervisor Workstation Escalation */}
              <div className="p-4 rounded-xl border border-forest/15 bg-white space-y-2">
                <div className="flex items-center gap-2 text-forest mb-2">
                  <Users size={16} className="text-forest shrink-0" />
                  <span className="text-xs font-mono font-bold">Step 3: Fraud SOC</span>
                </div>
                <p className="text-[11px] text-forest/70 mb-3 leading-relaxed">
                  Escalate packet to Bank Fraud Desk for real-time dual-key approval or police notification.
                </p>
                <button
                  onClick={() => {
                    setActionLog(prev => [
                      ...prev,
                      { time: new Date().toLocaleTimeString(), msg: 'Escalated to Fraud Operations Workstation #4. Audio spectrogram attached.' }
                    ]);
                  }}
                  className="w-full py-2 px-3 rounded-lg bg-white border border-forest/20 text-forest font-mono font-bold text-xs hover:bg-sage-1 transition-all cursor-pointer"
                >
                  Escalate to SOC
                </button>
              </div>

            </div>
          </div>

          {/* Real-time Tamper-Evident Action Audit Trail */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-mono text-forest font-bold">
              <span>Append-Only Forensic Action Log (§4.8 Audit Trail)</span>
              <span className="text-[10px] text-forest/60">SHA-256 Tamper-Proof</span>
            </div>

            <div className="p-3.5 bg-forest text-lemongrass font-mono text-[11px] rounded-xl space-y-1.5 max-h-32 overflow-y-auto">
              {actionLog.map((item, idx) => (
                <div key={idx} className="flex gap-2">
                  <span className="text-white/50 shrink-0">[{item.time}]</span>
                  <span className="text-white/90">{item.msg}</span>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="bg-sage-1 p-4 border-t border-forest/10 flex items-center justify-between">
          <span className="text-xs font-mono text-forest/70">
            Zero Customer Audio Retained during verification (§7 DPDP Compliant)
          </span>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-lg bg-forest text-lemongrass font-mono font-bold text-xs hover:bg-forest-hover transition-all cursor-pointer"
          >
            Dismiss HUD
          </button>
        </div>

      </motion.div>
    </div>
  );
}
