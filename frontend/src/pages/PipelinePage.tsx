import React, { useState, useRef } from 'react';
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

interface PipelinePageProps {
  tenantId: string;
  onResult: (r: PipelineResponse) => void;
}

export const PipelinePage: React.FC<PipelinePageProps> = ({ tenantId, onResult }) => {
  const [transcript, setTranscript] = useState('');
  const [contextScore, setContextScore] = useState(0.3);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [result, setResult] = useState<PipelineResponse | null>(null);
  const [error, setError] = useState('');
  const [showJson, setShowJson] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recStatus, setRecStatus] = useState('Click to record, or use presets (test tone audio)');
  const [sttLang, setSttLang] = useState('hi-IN');
  const [recordedBase64, setRecordedBase64] = useState<string | null>(null);
  const [recDuration, setRecDuration] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const speechRef = useRef<any>(null);

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      try { speechRef.current?.stop(); } catch {}
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { sampleRate: 16000, channelCount: 1 } });
      audioChunksRef.current = [];
      setRecordedBase64(null);
      const mr = new MediaRecorder(stream);
      mediaRecorderRef.current = mr;
      mr.ondataavailable = e => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const ctx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
        const buf = await ctx.decodeAudioData(await blob.arrayBuffer());
        const f32 = buf.getChannelData(0);
        const pcm = new Int16Array(f32.length);
        for (let i = 0; i < f32.length; i++) { const s = Math.max(-1, Math.min(1, f32[i])); pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF; }
        const bytes = new Uint8Array(pcm.buffer);
        let bin = ''; for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
        setRecordedBase64(btoa(bin));
        ctx.close();
        setRecStatus(`Recorded ${(f32.length / 16000).toFixed(1)}s (${(bytes.length / 1024).toFixed(0)} KB PCM)`);
      };
      mr.start();
      const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SR) { const r = new SR(); r.continuous = true; r.interimResults = true; r.lang = 'en-IN'; r.onresult = (e: any) => { let t = ''; for (let i = e.resultIndex; i < e.results.length; i++) t += e.results[i][0].transcript; if (t.trim()) setTranscript(t.trim()); }; r.start(); speechRef.current = r; }
      setIsRecording(true); setRecDuration(0);
      setRecStatus('Recording & transcribing — speak now');
      const st = Date.now(); timerRef.current = setInterval(() => setRecDuration(parseFloat(((Date.now() - st) / 1000).toFixed(1))), 100);
    } catch (err: any) { setRecStatus(`Mic error: ${err.message}`); }
  };

  const handleRun = async () => {
    if (!transcript.trim()) { setError('Enter a transcript or record your voice.'); return; }
    setError(''); setIsLoading(true); setResult(null); setCurrentStep(0);
    const audio = recordedBase64 || generateTestTone();
    const delays = [0, 800, 1600, 2400, 3200];
    delays.forEach((d, i) => setTimeout(() => setCurrentStep(i), d));
    try {
      const res = await runPipeline({ session_id: `pipeline-${Date.now()}`, tenant_id: tenantId, subject_id: 'test-subject', audio_pcm_base64: audio, sample_rate_hz: 16000, channels: 1, context_score: contextScore, transcript: transcript.trim() });
      setResult(res); onResult(res); setCurrentStep(5);
    } catch (e: any) { setError(e.message); setCurrentStep(-1); }
    setIsLoading(false);
  };

  const riskPct = result?.risk_assessment ? Math.round(result.risk_assessment.risk_score * 100) : 0;

  return (
    <>
      <section className="py-24 relative">
        <div className="absolute right-0 top-0 w-px h-24" style={{ background: 'linear-gradient(var(--accent), transparent)', opacity: 0.18 }} />
        <div className="w-[min(1280px,calc(100%-64px))] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-[0.7fr_1.3fr] gap-12 mb-14">
            <div className="font-mono text-xs text-[var(--muted)]">03 / PIPELINE TESTER</div>
            <div>
              <h2 className="text-[clamp(32px,4vw,48px)] leading-[1.08] tracking-[-0.045em] font-medium section-line">Run the full pipeline.</h2>
              <p className="mt-5 text-[var(--muted)] text-base leading-relaxed max-w-[650px]">Execute the complete 5-step orchestration pipeline. Record audio or use a preset, then watch each stage execute in sequence.</p>
            </div>
          </div>

          {/* Pipeline Steps */}
          <div className="grid grid-cols-5 border border-[var(--line)] bg-white mb-6 overflow-hidden" style={{ boxShadow: '0 10px 35px rgba(17,19,16,0.04)' }}>
            {STEPS.map((step, i) => (
              <div key={i} className={`p-4 border-r border-[var(--line)] last:border-r-0 text-center transition-all duration-300 ${
                currentStep === i ? 'bg-[rgba(21,94,239,0.06)]' : currentStep > i ? 'bg-[rgba(22,121,74,0.04)]' : ''
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
                    className={`px-2.5 py-1 rounded text-[11px] font-mono cursor-pointer border transition-all hover:-translate-y-px ${
                      p.tag === 'scam' ? 'border-[var(--danger)]/40 text-[var(--danger)] hover:bg-[var(--danger)]/5' : 'border-[var(--success)]/40 text-[var(--success)] hover:bg-[var(--success)]/5'
                    }`}>{p.label}</button>
                ))}
              </div>

              <textarea value={transcript} onChange={e => setTranscript(e.target.value)} rows={4} placeholder="Enter transcript or record audio..." className="w-full resize-none text-xs mb-4" />

              <div className="flex items-center gap-3 p-3 bg-[#F7F9FC] rounded-lg border border-[var(--line)] mb-4">
                <button onClick={toggleRecording}
                  className={`w-9 h-9 rounded-full grid place-items-center cursor-pointer transition-all text-sm shrink-0 ${isRecording ? 'bg-[var(--danger)] text-white' : 'bg-white border border-[var(--line)] hover:border-[var(--accent)]'}`}>
                  {isRecording ? '⏹' : '🎙'}
                </button>
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] font-mono font-medium text-[var(--success)] mb-0.5">✨ Auto-Detect Multilingual STT Active</div>
                  <div className="text-[10px] text-[var(--muted)] font-mono truncate">{recStatus}</div>
                  {isRecording && <div className="text-[10px] text-[var(--accent)] font-mono">{recDuration}s</div>}
                </div>
              </div>

              <div className="mb-5">
                <div className="flex justify-between text-[11px] font-mono text-[var(--muted)] mb-1">
                  <span>Context risk</span><span>{contextScore.toFixed(2)}</span>
                </div>
                <input type="range" min="0" max="1" step="0.05" value={contextScore} onChange={e => setContextScore(parseFloat(e.target.value))} className="w-full accent-[var(--accent)] bg-transparent border-none p-0" />
              </div>

              <button onClick={handleRun} disabled={isLoading}
                className="w-full min-h-[44px] rounded-lg text-sm font-medium text-white cursor-pointer disabled:opacity-50 transition-all" style={{ background: 'var(--ink)', border: '1px solid var(--ink)', boxShadow: '0 10px 28px rgba(17,19,16,0.12)' }}>
                {isLoading ? 'Running Pipeline...' : '▶ Run Pipeline'}
              </button>
              {error && <div className="mt-3 text-xs text-[var(--danger)] font-mono p-2 bg-[var(--danger)]/5 rounded">{error}</div>}
            </div>

            {/* Results */}
            <div className="bg-white border border-[var(--line)] rounded-xl overflow-hidden panel-bar" style={{ boxShadow: '0 30px 80px rgba(17,19,16,0.11)' }}>
              {!result ? (
                <div className="p-16 text-center text-sm text-[var(--muted)]">{isLoading ? 'Processing pipeline stages...' : 'Configure inputs and run the pipeline'}</div>
              ) : (
                <>
                  {/* Verdict */}
                  <div className={`p-5 border-b border-[var(--line)] ${result.final_action === 'PROCEED' ? 'bg-[rgba(22,121,74,0.04)]' : result.final_action?.includes('CALLBACK') ? 'bg-[rgba(161,92,0,0.04)]' : 'bg-[rgba(180,35,24,0.04)]'}`}>
                    <div className={`text-lg font-medium ${result.final_action === 'PROCEED' ? 'text-[var(--success)]' : result.final_action?.includes('CALLBACK') ? 'text-[var(--warning)]' : 'text-[var(--danger)]'}`}>
                      {result.final_action?.replace(/_/g, ' ')}
                    </div>
                    <div className="text-xs text-[var(--muted)] mt-1">{result.degraded ? '⚠ DEGRADED — ' : ''}{result.explanation}</div>
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
