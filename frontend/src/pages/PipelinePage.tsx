import React, { useState, useRef, useCallback, useEffect } from 'react';
import { runPipeline, generateTestTone, PipelineResponse } from '../api';

const PRESETS: Record<string, { label: string; text: string; ctx: number; tag: 'scam' | 'safe' }> = {
  scam1: { label: 'OTP + Money Transfer', text: 'Please transfer 50000 rupees immediately to this account number and share the OTP you just received on your phone. This is urgent.', ctx: 0.5, tag: 'scam' },
  scam2: { label: 'Bank Officer Scam', text: 'This is calling from State Bank of India security department. Your account has been compromised. Please share your Aadhaar number and the 6-digit code we just sent to verify your identity.', ctx: 0.6, tag: 'scam' },
  scam3: { label: 'KYC Threat', text: "Your KYC is expiring today. If you don't update it right now by sharing your PAN card and bank login, your account will be permanently blocked within 2 hours.", ctx: 0.5, tag: 'scam' },
  safe1: { label: 'Lunch Plans', text: 'Are we still meeting for lunch tomorrow? I was thinking we could try that new restaurant near the park.', ctx: 0.1, tag: 'safe' },
  safe2: { label: 'Weather Chat', text: "The weather is beautiful today. I went for a morning walk and it felt really nice. How's your weekend going?", ctx: 0.1, tag: 'safe' },
  safe3: { label: 'Project Discussion', text: "Hey, I reviewed the project proposal you sent. The timeline looks good. Can we discuss the budget in tomorrow's meeting?", ctx: 0.15, tag: 'safe' },
};

const STEPS = ['Feature Extraction', 'Spoof + Enrollment + Content', 'Risk Fusion', 'Policy Evaluation', 'Alert Dispatch'];

const CHUNK_DURATION_S = 5; // seconds per chunk for real-time streaming

interface PipelinePageProps {
  tenantId: string;
  onResult: (r: PipelineResponse) => void;
}

function pcmFromFloat32(f32: Float32Array): string {
  const pcm = new Int16Array(f32.length);
  for (let i = 0; i < f32.length; i++) {
    const s = Math.max(-1, Math.min(1, f32[i]));
    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  const bytes = new Uint8Array(pcm.buffer);
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

export const PipelinePage: React.FC<PipelinePageProps> = ({ tenantId, onResult }) => {
  const [transcript, setTranscript] = useState('');
  const [contextScore, setContextScore] = useState(0.3);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [result, setResult] = useState<PipelineResponse | null>(null);
  const [error, setError] = useState('');
  const [showJson, setShowJson] = useState(false);
  const [statusText, setStatusText] = useState('Press Start to begin real-time analysis');
  const [elapsedTime, setElapsedTime] = useState(0);
  const [chunkCount, setChunkCount] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const speechRef = useRef<any>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const analyzingRef = useRef(false); // avoid stale closures
  const transcriptRef = useRef('');
  const contextScoreRef = useRef(0.3);
  const chunkIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const chunkCountRef = useRef(0);

  // Keep refs in sync
  useEffect(() => { transcriptRef.current = transcript; }, [transcript]);
  useEffect(() => { contextScoreRef.current = contextScore; }, [contextScore]);

  const sendChunkToBackend = useCallback(async (audioBlob: Blob) => {
    if (!analyzingRef.current) return;
    try {
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      const buf = await ctx.decodeAudioData(await audioBlob.arrayBuffer());
      const f32 = buf.getChannelData(0);
      ctx.close();

      if (f32.length < 1600) return; // skip if < 0.1s

      const audio_b64 = pcmFromFloat32(f32);
      const chunkNum = ++chunkCountRef.current;
      setChunkCount(chunkNum);
      setCurrentStep(0);

      const delays = [0, 300, 600, 900, 1200];
      delays.forEach((d, i) => setTimeout(() => {
        if (analyzingRef.current) setCurrentStep(i);
      }, d));

      const res = await runPipeline({
        session_id: `realtime-${Date.now()}`,
        tenant_id: tenantId,
        subject_id: 'realtime-subject',
        audio_pcm_base64: audio_b64,
        sample_rate_hz: 16000,
        channels: 1,
        context_score: contextScoreRef.current,
        transcript: transcriptRef.current.trim(),
      });

      if (analyzingRef.current) {
        setResult(res);
        onResult(res);
        setCurrentStep(5);
      }
    } catch (e: any) {
      if (analyzingRef.current) setError(e.message);
    }
  }, [tenantId, onResult]);

  const startAnalysis = useCallback(async () => {
    setError('');
    setResult(null);
    setCurrentStep(-1);
    setChunkCount(0);
    chunkCountRef.current = 0;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
      });
      streamRef.current = stream;

      // Start Speech Recognition
      const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SR) {
        const r = new SR();
        r.continuous = true;
        r.interimResults = true;
        r.lang = 'en-IN';
        let accumulatedFinal = '';
        r.onresult = (e: any) => {
          let currentInterim = '';
          for (let i = e.resultIndex; i < e.results.length; i++) {
            const chunk = e.results[i][0].transcript;
            if (e.results[i].isFinal) {
              accumulatedFinal += chunk + ' ';
            } else {
              currentInterim += chunk;
            }
          }
          const fullText = (accumulatedFinal + ' ' + currentInterim).trim().replace(/\s+/g, ' ');
          if (fullText) setTranscript(fullText);
        };
        r.onend = () => {
          if (analyzingRef.current) {
            try { r.start(); } catch { }
          }
        };
        r.start();
        speechRef.current = r;
      }

      // Start chunked recording — every CHUNK_DURATION_S, stop recorder, send chunk, restart
      const startRecorderChunk = () => {
        if (!analyzingRef.current || !streamRef.current) return;
        audioChunksRef.current = [];
        const mr = new MediaRecorder(streamRef.current);
        mediaRecorderRef.current = mr;
        mr.ondataavailable = e => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };
        mr.onstop = () => {
          if (audioChunksRef.current.length > 0) {
            const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            sendChunkToBackend(blob);
          }
          // Start next chunk if still analyzing
          if (analyzingRef.current) {
            startRecorderChunk();
          }
        };
        mr.start();
        // Auto-stop after CHUNK_DURATION_S to trigger onstop -> send -> restart
        setTimeout(() => {
          if (mr.state === 'recording') {
            mr.stop();
          }
        }, CHUNK_DURATION_S * 1000);
      };

      analyzingRef.current = true;
      setIsAnalyzing(true);
      setStatusText('🔴 LIVE — Analyzing audio in real-time...');
      const st = Date.now();
      timerRef.current = setInterval(() => setElapsedTime(parseFloat(((Date.now() - st) / 1000).toFixed(1))), 100);

      startRecorderChunk();

    } catch (err: any) {
      setError(`Mic error: ${err.message}`);
    }
  }, [sendChunkToBackend]);

  const stopAnalysis = useCallback(() => {
    analyzingRef.current = false;
    setIsAnalyzing(false);
    setStatusText('Analysis stopped');
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    if (chunkIntervalRef.current) { clearInterval(chunkIntervalRef.current); chunkIntervalRef.current = null; }
    try { mediaRecorderRef.current?.stop(); } catch { }
    try { speechRef.current?.stop(); } catch { }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
  }, []);

  const handleClear = useCallback(() => {
    stopAnalysis();
    setTranscript('');
    setContextScore(0.3);
    setResult(null);
    setError('');
    setCurrentStep(-1);
    setShowJson(false);
    setElapsedTime(0);
    setChunkCount(0);
    chunkCountRef.current = 0;
    setStatusText('Press Start to begin real-time analysis');
  }, [stopAnalysis]);

  // Cleanup on unmount
  useEffect(() => {
    return () => { stopAnalysis(); };
  }, [stopAnalysis]);

  const riskPct = result?.risk_assessment ? Math.round(result.risk_assessment.risk_score * 100) : 0;

  return (
    <>
      <section className="py-24 relative">
        <div className="absolute right-0 top-0 w-px h-24" style={{ background: 'linear-gradient(var(--accent), transparent)', opacity: 0.18 }} />
        <div className="w-[min(1280px,calc(100%-64px))] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-[0.7fr_1.3fr] gap-12 mb-14">
            <div className="font-mono text-xs text-[var(--muted)]">03 / PIPELINE TESTER</div>
            <div>
              <h2 className="text-[clamp(32px,4vw,48px)] leading-[1.08] tracking-[-0.045em] font-medium section-line">Real-time analysis.</h2>
              <p className="mt-5 text-[var(--muted)] text-base leading-relaxed max-w-[650px]">Live microphone streaming with continuous 5-second chunk analysis. Audio is analyzed in real-time as you speak — no manual recording needed.</p>
            </div>
          </div>

          {/* Pipeline Steps */}
          <div className="grid grid-cols-5 border border-[var(--line)] bg-white mb-6 overflow-hidden" style={{ boxShadow: '0 10px 35px rgba(17,19,16,0.04)' }}>
            {STEPS.map((step, i) => (
              <div key={i} className={`p-4 border-r border-[var(--line)] last:border-r-0 text-center transition-all duration-300 ${currentStep === i ? 'bg-[rgba(21,94,239,0.06)]' : currentStep > i ? 'bg-[rgba(22,121,74,0.04)]' : ''
                }`}>
                <div className={`font-mono text-[10px] mb-1 ${currentStep === i ? 'text-[var(--accent)]' : currentStep > i ? 'text-[var(--success)]' : 'text-[var(--muted)]'}`}>
                  {currentStep > i ? '✓' : String(i + 1).padStart(2, '0')}
                </div>
                <div className="text-[11px] font-medium">{step}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.4fr] gap-4">
            {/* Input */}
            <div className="bg-white border border-[var(--line)] rounded-xl p-6 card-accent" style={{ boxShadow: '0 12px 35px rgba(17,19,16,0.035)' }}>
              <div className="font-mono text-[10px] text-[var(--muted)] uppercase mb-6">Input Configuration</div>

              <div className="flex flex-wrap gap-2 mb-4">
                {Object.entries(PRESETS).map(([k, p]) => (
                  <button key={k} onClick={() => { setTranscript(p.text); setContextScore(p.ctx); }}
                    className={`px-2.5 py-1 rounded text-[11px] font-mono cursor-pointer border transition-all hover:-translate-y-px ${p.tag === 'scam' ? 'border-[var(--danger)]/40 text-[var(--danger)] hover:bg-[var(--danger)]/5' : 'border-[var(--success)]/40 text-[var(--success)] hover:bg-[var(--success)]/5'
                      }`}>{p.label}</button>
                ))}
              </div>

              <textarea value={transcript} onChange={e => setTranscript(e.target.value)} rows={4} placeholder="Transcript appears here automatically via STT, or type manually..." className="w-full resize-none text-xs mb-4" />

              {/* Real-time Status */}
              <div className={`flex items-center gap-3 p-3 rounded-lg border mb-4 transition-all ${isAnalyzing
                  ? 'bg-[rgba(180,35,24,0.04)] border-[var(--danger)]/30'
                  : 'bg-[#F7F9FC] border-[var(--line)]'
                }`}>
                <div className={`w-3 h-3 rounded-full shrink-0 ${isAnalyzing ? 'bg-[var(--danger)] animate-pulse' : 'bg-[var(--muted)]/30'}`} />
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] font-mono font-medium text-[var(--fg)] mb-0.5">
                    {isAnalyzing ? `🔴 LIVE · ${elapsedTime}s · ${chunkCount} chunks analyzed` : statusText}
                  </div>
                  <div className="text-[10px] text-[var(--muted)] font-mono truncate">
                    {isAnalyzing ? `Streaming ${CHUNK_DURATION_S}s audio chunks continuously` : '✨ Auto-Detect Multilingual STT Active'}
                  </div>
                </div>
              </div>

              <div className="mb-5">
                <div className="flex justify-between text-[11px] font-mono text-[var(--muted)] mb-1">
                  <span>Context risk</span><span>{contextScore.toFixed(2)}</span>
                </div>
                <input type="range" min="0" max="1" step="0.05" value={contextScore} onChange={e => setContextScore(parseFloat(e.target.value))} className="w-full accent-[var(--accent)] bg-transparent border-none p-0" />
              </div>

              {/* Buttons */}
              <div className="flex gap-2">
                <button onClick={isAnalyzing ? stopAnalysis : startAnalysis}
                  className={`flex-1 min-h-[44px] rounded-lg text-sm font-medium cursor-pointer transition-all ${isAnalyzing
                      ? 'bg-[var(--danger)] text-white border border-[var(--danger)]'
                      : 'text-white'
                    }`}
                  style={isAnalyzing ? {} : { background: 'var(--ink)', border: '1px solid var(--ink)', boxShadow: '0 10px 28px rgba(17,19,16,0.12)' }}>
                  {isAnalyzing ? '⏹ Stop Analysis' : '🎙 Start Real-Time Analysis'}
                </button>
                <button onClick={handleClear}
                  className="px-4 min-h-[44px] rounded-lg text-sm font-medium cursor-pointer border border-[var(--line)] text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--accent)] transition-all bg-white"
                  style={{ boxShadow: '0 4px 12px rgba(17,19,16,0.04)' }}>
                  ✕ Clear
                </button>
              </div>
              {error && <div className="mt-3 text-xs text-[var(--danger)] font-mono p-2 bg-[var(--danger)]/5 rounded">{error}</div>}
            </div>

            {/* Results */}
            <div className="bg-white border border-[var(--line)] rounded-xl overflow-hidden panel-bar" style={{ boxShadow: '0 30px 80px rgba(17,19,16,0.11)' }}>
              {!result ? (
                <div className="p-16 text-center text-sm text-[var(--muted)]">{isAnalyzing ? 'Waiting for first audio chunk to complete...' : 'Start real-time analysis to see results'}</div>
              ) : (
                <>
                  {/* Verdict */}
                  <div className={`p-5 border-b border-[var(--line)] ${result.final_action === 'PROCEED' ? 'bg-[rgba(22,121,74,0.04)]' : result.final_action?.includes('CALLBACK') ? 'bg-[rgba(161,92,0,0.04)]' : 'bg-[rgba(180,35,24,0.04)]'}`}>
                    <div className={`text-lg font-medium ${result.final_action === 'PROCEED' ? 'text-[var(--success)]' : result.final_action?.includes('CALLBACK') ? 'text-[var(--warning)]' : 'text-[var(--danger)]'}`}>
                      {result.final_action?.replace(/_/g, ' ')}
                    </div>
                    <div className="text-xs text-[var(--muted)] mt-1">{result.degraded ? '⚠ DEGRADED — ' : ''}{result.explanation}</div>
                    {isAnalyzing && <div className="text-[10px] font-mono text-[var(--accent)] mt-1">🔴 Live updating — chunk #{chunkCount}</div>}
                  </div>

                  {/* Risk Score */}
                  {result.risk_assessment && (
                    <div className="p-5 border-b border-[var(--line)]">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-mono text-[10px] text-[var(--accent)] uppercase font-medium">Fused Risk Score</span>
                        <span className="text-2xl font-medium">{riskPct}%</span>
                      </div>
                      <div className="h-[5px] bg-[#E3E5DF] rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.max(riskPct, 3)}%`, background: 'linear-gradient(90deg, var(--success), var(--cyan))' }} />
                      </div>
                    </div>
                  )}

                  {/* Signals */}
                  <div className="p-5 border-b border-[var(--line)] space-y-4">
                    {[
                      { label: 'Synthesis Detection', sig: result.synthesis_signal },
                      { label: 'Speaker Verification', sig: result.speaker_match_signal },
                      { label: 'Content Risk (LLM)', sig: result.content_risk_signal },
                    ].map((s, i) => (
                      <div key={i}>
                        <div className="flex justify-between text-[11px] font-mono mb-1">
                          <span className="text-[var(--muted)]">{String(i + 1).padStart(2, '0')} / {s.label}</span>
                          <span>{s.sig?.available !== false ? `${Math.round((s.sig?.score || 0) * 100)}%` : 'N/A'}</span>
                        </div>
                        <div className="h-[3px] bg-[#E3E5DF] rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-500" style={{ width: `${Math.max((s.sig?.available !== false ? (s.sig?.score || 0) : 0) * 100, 2)}%`, background: 'linear-gradient(90deg, var(--accent), var(--cyan))' }} />
                        </div>
                        <div className="text-[10px] text-[var(--muted)] font-mono mt-0.5">{s.sig?.detail || '—'}</div>
                      </div>
                    ))}
                  </div>

                  {/* Meta */}
                  <div className="p-5 space-y-1">
                    {result.policy_decision && <div className="text-[10px] font-mono text-[var(--muted)]">Policy v{result.policy_decision.policy_version} · {result.policy_decision.decided_at}</div>}
                    {result.alert_event && <div className="text-[10px] font-mono text-[var(--success)]">✓ Alert dispatched to {result.alert_event.channels_dispatched} channel(s)</div>}
                    <button onClick={() => setShowJson(!showJson)} className="text-[10px] font-mono text-[var(--accent)] hover:underline cursor-pointer mt-2">
                      {showJson ? '▲ Hide' : '▼ Show'} raw JSON
                    </button>
                    {showJson && (
                      <pre className="mt-2 p-4 code-block text-[10px] overflow-auto max-h-64">{JSON.stringify(result, null, 2)}</pre>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </section>
    </>
  );
};
