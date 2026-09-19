import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Upload, Loader2, ShieldCheck, RotateCcw, Sparkles, Key } from 'lucide-react';
import AudioUploader from '../components/AudioUploader';
import AudioRecorder from '../components/AudioRecorder';
import DetectionResult from '../components/DetectionResult';
import { detectAudio } from '../utils/api';

const DEFAULT_API_KEY = 'pv_live_demo_000000000000000000000000';

export default function DetectPage() {
  const [mode, setMode] = useState('upload'); // 'upload' | 'record'
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [apiKey, setApiKey] = useState(DEFAULT_API_KEY);

  const handleDetect = async (file) => {
    setIsProcessing(true);
    setResult(null);
    setError(null);

    const resp = await detectAudio(file, apiKey);

    if (resp.success && resp.data) {
      setResult(resp.data);
    } else {
      setError(
        resp.error?.message || resp.error?.detail || resp.error ||
        'Unable to reach the detection service. Ensure the API Gateway is running and the API key is valid.'
      );
    }

    setIsProcessing(false);
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-white text-forest selection:bg-lemongrass py-10">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Header */}
        <div className="space-y-2 pb-6 border-b border-forest/15">
          <div className="inline-flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-forest">
            <Sparkles size={14} className="text-forest" />
            <span>ENTERPRISE MULTI-VECTOR FIREWALL</span>
          </div>
          <h1 className="font-display text-4xl font-extrabold text-forest tracking-tight">
            Voice Integrity & Anti-Impersonation Detector
          </h1>
          <p className="text-sm text-forest font-medium leading-relaxed">
            Real-time defense fusing <strong>Acoustic Forensics (DhVani 2)</strong>, <strong>Speaker Voiceprint Matching</strong>, <strong>Conversational Vishing NLP</strong>, and <strong>SIP Call Metadata</strong> in under 50ms.
          </p>
        </div>

        {/* API Key Banner */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-xl bg-sage-1 border border-forest/15 spade-cut-sm">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <Key size={16} className="text-forest shrink-0" />
            <span className="text-xs font-mono font-extrabold text-forest whitespace-nowrap">API Key:</span>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="pv_live_your_key_here"
              className="w-full sm:w-80 bg-white border border-forest/20 px-3 py-1.5 rounded text-xs font-mono text-forest font-bold outline-none focus:border-forest"
            />
          </div>
          <span className="text-[11px] font-mono font-extrabold px-3 py-1 rounded bg-forest text-lemongrass shadow-sm">
            {apiKey ? 'API KEY ACTIVE' : 'NO API KEY'}
          </span>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center gap-3 p-1.5 bg-sage-1 rounded-xl border border-forest/15 w-fit">
          <button
            onClick={() => setMode('upload')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-mono font-extrabold transition-all cursor-pointer ${
              mode === 'upload'
                ? 'bg-forest text-lemongrass shadow-md'
                : 'bg-white text-forest hover:bg-sage-2 border border-forest/15'
            }`}
          >
            <Upload size={15} /> Upload Audio File
          </button>
          <button
            onClick={() => setMode('record')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-mono font-extrabold transition-all cursor-pointer ${
              mode === 'record'
                ? 'bg-forest text-lemongrass shadow-md'
                : 'bg-white text-forest hover:bg-sage-2 border border-forest/15'
            }`}
          >
            <Mic size={15} /> Record Live Mic
          </button>
        </div>

        {/* Audio Input Box */}
        <div className="bg-white rounded-2xl border border-forest/15 p-6 shadow-spade spade-cut-md">
          <AnimatePresence mode="wait">
            {mode === 'upload' ? (
              <motion.div
                key="upload"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <AudioUploader
                  onFileSelect={handleDetect}
                  isProcessing={isProcessing}
                />
              </motion.div>
            ) : (
              <motion.div
                key="record"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <AudioRecorder
                  onRecordingComplete={handleDetect}
                  maxDuration={10}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Loading Spinner */}
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center gap-3 py-10"
          >
            <Loader2 className="w-9 h-9 text-forest animate-spin" />
            <div className="text-center">
              <p className="font-display text-lg font-bold text-forest">Processing audio stream with DhVani 2...</p>
              <p className="text-xs text-forest font-mono mt-1">
                Extracting Log-Mel spectral features & running SE-BiGRU neural classification
              </p>
            </div>
          </motion.div>
        )}

        {/* Results Card */}
        {result && !isProcessing && (
          <div className="space-y-6">
            <DetectionResult result={result} />

            <div className="flex justify-center pt-2">
              <button
                onClick={handleReset}
                className="inline-flex items-center gap-2 bg-forest text-lemongrass hover:bg-forest-hover font-bold text-xs px-6 py-3 rounded-md shadow-sm transition-all cursor-pointer"
              >
                <RotateCcw size={14} /> Analyze Another Audio
              </button>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && !isProcessing && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs font-mono font-bold">
            {error}
          </div>
        )}

      </div>
    </div>
  );
}
