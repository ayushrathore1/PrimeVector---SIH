import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Mic, Square, Radio, RotateCcw, Activity } from 'lucide-react';

const TARGET_SAMPLE_RATE = 16000;
const ANALYSIS_WINDOW_SECONDS = 3;
const ANALYSIS_HOP_SECONDS = 1;

function toBase64Pcm(samples, inputSampleRate) {
  const outputLength = Math.max(1, Math.round(samples.length * TARGET_SAMPLE_RATE / inputSampleRate));
  const pcm = new Int16Array(outputLength);
  const ratio = inputSampleRate / TARGET_SAMPLE_RATE;
  for (let index = 0; index < outputLength; index += 1) {
    const sourcePosition = index * ratio;
    const left = Math.floor(sourcePosition);
    const right = Math.min(left + 1, samples.length - 1);
    const sample = samples[left] * (1 - (sourcePosition - left)) + samples[right] * (sourcePosition - left);
    pcm[index] = Math.max(-1, Math.min(1, sample)) * (sample < 0 ? 0x8000 : 0x7fff);
  }
  const bytes = new Uint8Array(pcm.buffer);
  const chunkSize = 0x8000;
  let binary = '';
  for (let offset = 0; offset < bytes.length; offset += chunkSize) binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  return btoa(binary);
}

function latestWindow(buffers, windowFrames) {
  const result = new Float32Array(windowFrames);
  let writeOffset = windowFrames;
  let remaining = windowFrames;
  for (let index = buffers.length - 1; index >= 0 && remaining > 0; index -= 1) {
    const buffer = buffers[index];
    const copyLength = Math.min(buffer.length, remaining);
    writeOffset -= copyLength;
    result.set(buffer.subarray(buffer.length - copyLength), writeOffset);
    remaining -= copyLength;
  }
  return result;
}

function detectSpeechActivity(samples) {
  let sumSq = 0;
  let peak = 0;
  let zc = 0;
  for (let i = 0; i < samples.length; i++) {
    const val = samples[i];
    const abs = Math.abs(val);
    if (abs > peak) peak = abs;
    sumSq += val * val;
    if (i > 0 && ((val >= 0 && samples[i - 1] < 0) || (val < 0 && samples[i - 1] >= 0))) {
      zc++;
    }
  }
  const rms = Math.sqrt(sumSq / Math.max(1, samples.length));
  const zcr = zc / Math.max(1, samples.length);

  // Distinguish Silence vs Ambient Noise vs Active Speech
  if (peak < 0.008 && rms < 0.003) {
    return { status: 'SILENCE', rms, peak, zcr, label: 'No Voice (Silence)' };
  }
  if (peak < 0.015 && rms < 0.006) {
    return { status: 'NOISE', rms, peak, zcr, label: 'Ambient Noise' };
  }
  return { status: 'VOICE', rms, peak, zcr, label: 'Voice Active' };
}

export default function RealtimeAudioCapture({
  disabled,
  onStart,
  onWindow,
  onStop,
  onClear,
  hasReport = false,
}) {
  const [active, setActive] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [liveActivity, setLiveActivity] = useState('IDLE');
  const [error, setError] = useState(null);

  // Keep callback refs stable across renders to prevent reconnection loops
  const onWindowRef = useRef(onWindow);
  onWindowRef.current = onWindow;
  const onStopRef = useRef(onStop);
  onStopRef.current = onStop;
  const onStartRef = useRef(onStart);
  onStartRef.current = onStart;

  const streamRef = useRef(null);
  const contextRef = useRef(null);
  const processorRef = useRef(null);
  const animationRef = useRef(null);
  const timerRef = useRef(null);
  const canvasRef = useRef(null);
  const buffersRef = useRef([]);
  const bufferedFramesRef = useRef(0);
  const capturedFramesRef = useRef(0);
  const nextWindowAtRef = useRef(0);
  const lastSentFrameRef = useRef(0);
  const sendingRef = useRef(false);

  const drawStandbyWave = useCallback(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    // Deep Forest Canvas
    ctx.fillStyle = '#0B1609';
    ctx.fillRect(0, 0, w, h);

    // Subtle center zero-crossing line
    ctx.strokeStyle = 'rgba(197, 255, 52, 0.15)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();
    ctx.setLineDash([]);

    // Straight baseline waveform until voice is inputted
    ctx.strokeStyle = '#C5FF34';
    ctx.lineWidth = 2.0;
    ctx.shadowColor = '#C5FF34';
    ctx.shadowBlur = 4;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();
    ctx.shadowBlur = 0;
  }, []);

  useEffect(() => {
    if (!active && !hasReport) {
      drawStandbyWave();
      setElapsedSeconds(0);
      setLiveActivity('IDLE');
    }
  }, [active, hasReport, drawStandbyWave]);

  const stop = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current.onaudioprocess = null;
      processorRef.current = null;
    }
    if (typeof window !== 'undefined') {
      window.__satyaActiveAudioProcessor = null;
      window.__satyaActiveAudioContext = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    // Flush final audio window if we have captured audio that hasn't been sent yet
    if (buffersRef.current.length > 0 && contextRef.current) {
      const sampleRate = contextRef.current.sampleRate;
      const windowFrames = Math.round(sampleRate * ANALYSIS_WINDOW_SECONDS);
      const minFrames = Math.round(sampleRate * 0.35); // at least ~350ms of speech
      const unsentFrames = capturedFramesRef.current - lastSentFrameRef.current;

      if (unsentFrames >= minFrames || (lastSentFrameRef.current === 0 && capturedFramesRef.current >= minFrames)) {
        try {
          const windowPcm = latestWindow(buffersRef.current, windowFrames);
          const base64Audio = toBase64Pcm(windowPcm, sampleRate);
          const speechActivity = detectSpeechActivity(windowPcm);
          setLiveActivity(speechActivity.status);
          lastSentFrameRef.current = capturedFramesRef.current;
          Promise.resolve(onWindowRef.current?.({
            audio_pcm_base64: base64Audio,
            sample_rate_hz: TARGET_SAMPLE_RATE,
            channels: 1,
            duration_ms: ANALYSIS_WINDOW_SECONDS * 1000,
            speech_status: speechActivity.status,
            rms: speechActivity.rms,
            peak: speechActivity.peak,
            zcr: speechActivity.zcr,
          })).catch(() => {});
        } catch (_) {}
      }
    }

    if (contextRef.current && contextRef.current.state !== 'closed') {
      contextRef.current.close().catch(() => {});
      contextRef.current = null;
    }
    setActive(false);
    onStopRef.current?.();
  }, []);

  const stopRef = useRef(stop);
  stopRef.current = stop;

  // Cleanup ONLY on unmount to prevent premature mic stream interruption
  useEffect(() => {
    return () => {
      stopRef.current?.();
    };
  }, []);


  const start = async () => {
    try {
      setError(null);
      buffersRef.current = [];
      bufferedFramesRef.current = 0;
      capturedFramesRef.current = 0;
      nextWindowAtRef.current = 0;
      lastSentFrameRef.current = 0;
      sendingRef.current = false;

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });
      streamRef.current = mediaStream;

      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const audioContext = new AudioContextClass();
      contextRef.current = audioContext;

      const sourceNode = audioContext.createMediaStreamSource(mediaStream);
      const analyserNode = audioContext.createAnalyser();
      analyserNode.fftSize = 2048;
      const scriptNode = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = scriptNode;

      sourceNode.connect(analyserNode);
      analyserNode.connect(scriptNode);
      scriptNode.connect(audioContext.destination);

      const sampleRate = audioContext.sampleRate;
      const windowFrames = Math.round(sampleRate * ANALYSIS_WINDOW_SECONDS);
      const hopFrames = Math.round(sampleRate * ANALYSIS_HOP_SECONDS);
      nextWindowAtRef.current = windowFrames;

      if (typeof window !== 'undefined') {
        window.__satyaActiveAudioProcessor = scriptNode;
        window.__satyaActiveAudioContext = audioContext;
      }

      scriptNode.onaudioprocess = (event) => {
        const inputData = event.inputBuffer.getChannelData(0);
        const cloned = new Float32Array(inputData.length);
        cloned.set(inputData);
        buffersRef.current.push(cloned);
        bufferedFramesRef.current += cloned.length;
        capturedFramesRef.current += cloned.length;

        const maxKeepFrames = windowFrames * 2;
        while (bufferedFramesRef.current - buffersRef.current[0]?.length > maxKeepFrames) {
          bufferedFramesRef.current -= buffersRef.current[0].length;
          buffersRef.current.shift();
        }

        if (capturedFramesRef.current >= nextWindowAtRef.current && !sendingRef.current) {
          nextWindowAtRef.current += hopFrames;
          const windowPcm = latestWindow(buffersRef.current, windowFrames);
          const base64Audio = toBase64Pcm(windowPcm, sampleRate);
          const speechActivity = detectSpeechActivity(windowPcm);
          setLiveActivity(speechActivity.status);
          lastSentFrameRef.current = capturedFramesRef.current;
          sendingRef.current = true;
          Promise.resolve(onWindowRef.current?.({
            audio_pcm_base64: base64Audio,
            sample_rate_hz: TARGET_SAMPLE_RATE,
            channels: 1,
            duration_ms: ANALYSIS_WINDOW_SECONDS * 1000,
            speech_status: speechActivity.status,
            rms: speechActivity.rms,
            peak: speechActivity.peak,
            zcr: speechActivity.zcr,
          }))
            .catch((windowError) => {
              setError(windowError.message || 'Error processing live audio window.');
            })
            .finally(() => {
              sendingRef.current = false;
            });
        }
      };

      const canvas = canvasRef.current;
      const drawingContext = canvas.getContext('2d');
      const waveform = new Uint8Array(analyserNode.frequencyBinCount);

      const draw = () => {
        if (!canvasRef.current) return;
        const w = canvas.width;
        const h = canvas.height;

        drawingContext.fillStyle = '#0B1609';
        drawingContext.fillRect(0, 0, w, h);

        drawingContext.strokeStyle = 'rgba(197, 255, 52, 0.15)';
        drawingContext.lineWidth = 1;
        drawingContext.setLineDash([4, 4]);
        drawingContext.beginPath();
        drawingContext.moveTo(0, h / 2);
        drawingContext.lineTo(w, h / 2);
        drawingContext.stroke();
        drawingContext.setLineDash([]);

        analyserNode.getByteTimeDomainData(waveform);

        let sumSquares = 0;
        for (let i = 0; i < waveform.length; i++) {
          const norm = (waveform[i] - 128) / 128;
          sumSquares += norm * norm;
        }
        const rms = Math.sqrt(sumSquares / waveform.length);
        const isVoiceActive = rms >= 0.008;

        drawingContext.shadowBlur = isVoiceActive ? 10 : 3;
        drawingContext.shadowColor = '#C5FF34';
        drawingContext.strokeStyle = '#C5FF34';
        drawingContext.lineWidth = isVoiceActive ? 2.2 : 2.0;
        drawingContext.beginPath();

        if (!isVoiceActive) {
          // Keep wave straight until voice is inputted
          drawingContext.moveTo(0, h / 2);
          drawingContext.lineTo(w, h / 2);
        } else {
          // Live dynamic voice waveform
          waveform.forEach((value, index) => {
            const x = (index / (waveform.length - 1)) * w;
            const y = (value / 255) * h;
            if (index === 0) drawingContext.moveTo(x, y);
            else drawingContext.lineTo(x, y);
          });
        }
        drawingContext.stroke();
        drawingContext.shadowBlur = 0;

        animationRef.current = requestAnimationFrame(draw);
      };
      draw();
      timerRef.current = setInterval(() => setElapsedSeconds((seconds) => seconds + 1), 1000);
      setElapsedSeconds(0);
      setActive(true);
      onStart?.();
    } catch (captureError) {
      setError(captureError.message || 'Microphone access is required for live analysis.');
      stop();
    }
  };

  return (
    <div className="rounded-2xl border border-[#E5EAE0] bg-white p-5 space-y-3 shadow-xs">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-[#0B150A]" />
          <h2 className="font-mono text-sm font-bold text-[#0B150A] tracking-wider">
            Live PCM Oscilloscope
          </h2>
        </div>

        <div className="flex items-center gap-2">
          {hasReport && !active && (
            <button
              type="button"
              onClick={() => {
                onClear?.();
                drawStandbyWave();
              }}
              className="flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-mono font-bold text-rose-700 hover:text-rose-900 bg-rose-50 hover:bg-rose-100 border border-rose-200 hover:border-rose-300 transition-all cursor-pointer shadow-2xs"
              title="Erase score and clear analysis report"
            >
              <RotateCcw size={12} />
              <span>CLEAR REPORT</span>
            </button>
          )}

          <button
            type="button"
            onClick={active ? stop : start}
            disabled={disabled}
            className={`flex items-center gap-2 rounded-full px-4 py-2 text-xs font-mono font-bold transition-all cursor-pointer shadow-xs disabled:cursor-not-allowed disabled:opacity-40 ${
              active
                ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-900/30'
                : 'bg-[#0F1C0B] hover:bg-[#182C13] text-[#C5FF34] border border-[#182C13]'
            }`}
          >
            {active ? (
              <>
                <Square size={12} fill="currentColor" />
                <span>STOP STREAM</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-[#C5FF34] shadow-[0_0_6px_#C5FF34]"></span>
                <span>START LIVE ANALYSIS</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Waveform Container Box */}
      <div className={`overflow-hidden rounded-xl border bg-[#0B1609] relative transition-all ${
        active
          ? 'border-[#C5FF34] shadow-[0_0_15px_rgba(197,255,52,0.2)]'
          : 'border-[#182C13]'
      }`}>
        <div className="flex items-center justify-between border-b border-white/10 bg-[#0B1609] px-3 py-1.5 text-[11px] font-mono text-[#C5FF34] font-bold">
          <span className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${active ? 'bg-[#C5FF34] animate-ping' : hasReport ? 'bg-amber-400' : 'bg-[#C5FF34]'}`}></span>
            <span className={active ? 'text-[#C5FF34] font-bold' : hasReport ? 'text-amber-300 font-bold' : 'text-[#C5FF34] font-bold'}>
              {active
                ? liveActivity === 'VOICE'
                  ? 'VOICE INGESTION · SPEECH DETECTED'
                  : liveActivity === 'NOISE'
                  ? 'VOICE INGESTION · AMBIENT NOISE ONLY'
                  : 'VOICE INGESTION · NO VOICE / SILENCE'
                : hasReport
                ? 'STREAM STOPPED · ANALYSIS RETAINED'
                : 'SYSTEM STANDBY · READY'}
            </span>
          </span>
          <span className="text-white/70 font-mono text-[11px]">
            {active
              ? `${elapsedSeconds}s elapsed`
              : hasReport
              ? `${elapsedSeconds}s recorded · Press Clear to erase score`
              : 'Click Start to Speak Any Voice'}
          </span>
        </div>
        <div className="relative">
          <canvas ref={canvasRef} width={800} height={160} className="block h-40 w-full" />
        </div>
      </div>

      {error && (
        <p className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-xs font-mono text-rose-800 font-semibold">
          {error}
        </p>
      )}
    </div>
  );
}
