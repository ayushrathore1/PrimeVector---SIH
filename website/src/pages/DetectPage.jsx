import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mic, 
  Upload, 
  Radio, 
  Loader2, 
  RotateCcw, 
  Sparkles, 
  Key, 
  ShieldCheck,
  Lock,
  FileCheck2,
  Activity,
  Cpu,
  Waves
} from 'lucide-react';
import AudioUploader from '../components/AudioUploader';
import DetectionResult from '../components/DetectionResult';
import { detectAudio } from '../utils/api';
import LiveDetectionPanel from '../components/LiveDetectionPanel';
import DirectSatyaDhVaniMicPanel, { DirectDhwaniMicPanel } from '../components/DirectDhwaniMicPanel';
import PrivacyComplianceModal from '../components/PrivacyComplianceModal';

const DEFAULT_API_KEY = 'pv_live_demo_000000000000000000000000';

export default function DetectPage() {
  const [mode, setMode] = useState('satyadhvani-mic'); // 'satyadhvani-mic' | 'upload' | 'live'
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [apiKey, setApiKey] = useState(DEFAULT_API_KEY);
  const [isComplianceOpen, setIsComplianceOpen] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState(null);

  const handleDetect = async (file) => {
    setIsProcessing(true);
    setResult(null);
    setError(null);
    setUploadedFileName(file.name || 'Audio Stream');

    const resp = await detectAudio(file, apiKey);

    if (resp.success && resp.data) {
      setResult(resp.data);
    } else {
      const errObj = resp.error;
      let errMsg = 'Unable to reach the detection service. Ensure the API Gateway is running and the API key is valid.';
      if (typeof errObj === 'string') {
        errMsg = errObj;
      } else if (errObj && typeof errObj === 'object') {
        errMsg = errObj.message || errObj.detail?.message || errObj.detail || errObj.error || JSON.stringify(errObj);
        if (typeof errMsg === 'object') {
          errMsg = errMsg.message || JSON.stringify(errMsg);
        }
      }
      setError(errMsg);
    }

    setIsProcessing(false);
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setUploadedFileName(null);
  };

  return (
    <div className="relative w-full min-h-[calc(100vh-4rem)] bg-[#F3F6EE] text-[#0B150A] p-4 sm:p-6 lg:px-8 space-y-4 flex flex-col justify-start">
      
      {/* ── Top Header Row (SatyaDhVani Brand + Pill Mode Switcher) ── */}
      <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 shrink-0">
        
        {/* Left: Brand Icon & Title */}
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-full bg-[#0F1C0B] text-[#C5FF34] flex items-center justify-center shadow-xs shrink-0">
            <Activity size={22} className="text-[#C5FF34]" />
          </div>
          <div>
            <h1 className="font-display text-xl sm:text-2xl font-black text-[#0B150A] tracking-tight">
              SatyaDhVani
            </h1>
            <p className="text-xs font-mono text-[#5A6556] tracking-wide mt-0.5">
              Voice Integrity Firewall
            </p>
          </div>
        </div>

        {/* Right: Ingestion Mode Pill Switchers */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={() => setMode('satyadhvani-mic')}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-mono font-bold transition-all cursor-pointer shadow-xs ${
              (mode === 'satyadhvani-mic' || mode === 'dhwani-mic')
                ? 'bg-[#0F1C0B] text-[#C5FF34] border border-[#0F1C0B]'
                : 'bg-white text-[#0B150A] border border-[#D5DDCF] hover:bg-[#FAFBF8]'
            }`}
          >
            <Mic size={14} className={(mode === 'satyadhvani-mic' || mode === 'dhwani-mic') ? 'text-[#C5FF34]' : 'text-[#0B150A]'} />
            <span>Direct SatyaDhVani Mic</span>
          </button>
          
          <button
            onClick={() => setMode('upload')}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-mono font-bold transition-all cursor-pointer shadow-xs ${
              mode === 'upload'
                ? 'bg-[#0F1C0B] text-[#C5FF34] border border-[#0F1C0B]'
                : 'bg-white text-[#0B150A] border border-[#D5DDCF] hover:bg-[#FAFBF8]'
            }`}
          >
            <Upload size={14} className={mode === 'upload' ? 'text-[#C5FF34]' : 'text-[#0B150A]'} />
            <span>Upload Audio File</span>
          </button>

          <button
            onClick={() => setMode('live')}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-mono font-bold transition-all cursor-pointer shadow-xs ${
              mode === 'live'
                ? 'bg-[#0F1C0B] text-[#C5FF34] border border-[#0F1C0B]'
                : 'bg-white text-[#0B150A] border border-[#D5DDCF] hover:bg-[#FAFBF8]'
            }`}
          >
            <Radio size={14} className={mode === 'live' ? 'text-[#C5FF34]' : 'text-[#0B150A]'} />
            <span>Multi-Vector Pipeline</span>
          </button>
        </div>

      </header>

      {/* ── Main Cockpit Frame ── */}
      <main className="flex-1 w-full flex flex-col justify-start">
        <AnimatePresence mode="wait">
          {(mode === 'satyadhvani-mic' || mode === 'dhwani-mic') ? (
            /* ── Cockpit Mode 1: Direct SatyaDhVani Microphone Stream ── */
            <motion.div
              key="satyadhvani-mic"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.15 }}
              className="w-full h-full flex flex-col justify-center"
            >
              <DirectSatyaDhVaniMicPanel apiKey={apiKey} />
            </motion.div>
          ) : mode === 'upload' ? (
            /* ── Cockpit Mode 2: Audio File Upload Split Cockpit ── */
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.15 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-start w-full"
            >
              {/* Left Column: File Dropzone (5 cols) */}
              <div className="lg:col-span-5 space-y-2.5">
                <div className="p-4 rounded-xl border border-forest/15 bg-white shadow-xs space-y-2.5">
                  <div className="flex items-center justify-between border-b border-forest/10 pb-2">
                    <span className="text-xs font-mono font-bold text-forest uppercase tracking-wider flex items-center gap-1.5">
                      <Upload size={13} className="text-forest" />
                      <span>Audio Ingestion Engine</span>
                    </span>
                    <span className="text-[10px] font-mono text-emerald-800 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 font-bold">
                      WAV · MP3 · M4A · WebM
                    </span>
                  </div>

                  <AudioUploader
                    onFileSelect={handleDetect}
                    isProcessing={isProcessing}
                  />

                  {uploadedFileName && (
                    <div className="p-2 rounded-lg bg-sage-1 border border-forest/10 flex items-center justify-between text-xs font-mono">
                      <div className="flex items-center gap-2 truncate">
                        <Waves size={14} className="text-forest shrink-0" />
                        <span className="font-bold text-forest truncate">{uploadedFileName}</span>
                      </div>
                      <button
                        onClick={handleReset}
                        className="text-rose-700 hover:text-rose-900 font-bold text-[11px] cursor-pointer flex items-center gap-1 shrink-0 ml-2"
                      >
                        <RotateCcw size={11} /> Reset
                      </button>
                    </div>
                  )}

                  <div className="p-2 rounded-lg bg-sage-1/50 border border-forest/10 space-y-1 font-mono text-[10px] text-forest/70">
                    <div className="flex justify-between">
                      <span>Sampling Rate:</span>
                      <strong className="text-forest">16,000 Hz Mono PCM</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Audio Storage:</span>
                      <strong className="text-emerald-700">0 Bytes Persisted </strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Neural Classifier:</span>
                      <strong className="text-forest">SatyaDhVani </strong>
                    </div>
                  </div>
                </div>

                {error && (
                  <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-900 text-xs font-mono font-bold">
                    {error}
                  </div>
                )}
              </div>

              {/* Right Column: Instant Detection Forensics (7 cols) */}
              <div className="lg:col-span-7">
                {isProcessing ? (
                  <div className="p-10 rounded-xl border border-forest/15 bg-white shadow-xs flex flex-col items-center justify-center text-center space-y-3">
                    <Loader2 className="w-8 h-8 text-forest animate-spin" />
                    <div>
                      <h4 className="font-display text-sm font-bold text-forest">Running SatyaDhVani Neural Forward Pass...</h4>
                      <p className="text-xs font-mono text-forest/70 mt-0.5">
                        Computing 128-band Log-Mel spectrogram, pitch contour & LFCC phase consistency
                      </p>
                    </div>
                  </div>
                ) : result ? (
                  <DetectionResult result={result} />
                ) : (
                  <div className="p-10 rounded-xl border border-dashed border-forest/20 bg-white flex flex-col items-center justify-center text-center space-y-2">
                    <Activity className="w-10 h-10 text-forest/40" />
                    <h4 className="font-display text-sm font-bold text-forest">Awaiting Audio Ingestion</h4>
                    <p className="text-xs font-mono text-forest/60 max-w-sm">
                      Upload or drop any recorded voice sample on the left to inspect deepfake probabilities, F₀ prosody contours, and multi-vector threat signals.
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          ) : (
            /* ── Cockpit Mode 3: Enterprise Multi-Vector Pipeline ── */
            <motion.div
              key="live"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.15 }}
              className="w-full h-full overflow-y-auto"
            >
              <LiveDetectionPanel embedded />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Privacy & Regulatory Compliance Modal */}
      <PrivacyComplianceModal
        isOpen={isComplianceOpen}
        onClose={() => setIsComplianceOpen(false)}
      />

    </div>
  );
}
