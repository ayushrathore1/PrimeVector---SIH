import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, Square, Clock, Activity } from 'lucide-react';

export default function AudioRecorder({ onRecordingComplete, maxDuration = 10 }) {
  const [isRecording, setIsRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);
  const streamRef = useRef(null);

  const cleanup = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true },
      });
      streamRef.current = stream;

      const audioCtx = new AudioContext();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateLevel = () => {
        analyser.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        setAudioLevel(avg / 255);
        animFrameRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();

      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const file = new File([blob], `recording-${Date.now()}.webm`, { type: 'audio/webm' });
        onRecordingComplete(file);
        cleanup();
      };

      recorder.start(100);
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setElapsed(0);

      timerRef.current = setInterval(() => {
        setElapsed(prev => {
          if (prev + 1 >= maxDuration) {
            stopRecording();
            return maxDuration;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (err) {
      console.error('Microphone access denied:', err);
      alert('Microphone access is required for recording. Please check browser permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    setAudioLevel(0);
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const remaining = maxDuration - elapsed;
  const progressPct = (elapsed / maxDuration) * 100;

  return (
    <div className="space-y-4 p-6 bg-sage-1 border border-forest/10 rounded-2xl spade-cut-md">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          {/* Progress Ring */}
          <svg className="w-28 h-28 -rotate-90" viewBox="0 0 120 120">
            <circle
              cx="60" cy="60" r="52"
              fill="none"
              stroke="rgba(24, 40, 14, 0.1)"
              strokeWidth="5"
            />
            {isRecording && (
              <circle
                cx="60" cy="60" r="52"
                fill="none"
                stroke="#18280E"
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 52}`}
                strokeDashoffset={`${2 * Math.PI * 52 * (1 - progressPct / 100)}`}
                className="transition-all duration-1000 ease-linear"
              />
            )}
          </svg>

          {/* Center Record Button */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`absolute inset-0 m-auto w-20 h-20 rounded-full flex items-center justify-center transition-all duration-200 cursor-pointer shadow-spade ${
              isRecording
                ? 'bg-rose-600 hover:bg-rose-700 text-white scale-105'
                : 'bg-forest hover:bg-forest-hover text-lemongrass'
            }`}
          >
            {isRecording ? (
              <Square className="w-6 h-6 fill-current" />
            ) : (
              <Mic className="w-7 h-7" />
            )}
          </button>
        </div>

        {/* Status indicator */}
        <div className="text-center space-y-1">
          {isRecording ? (
            <div className="space-y-1">
              <div className="flex items-center justify-center gap-2 text-rose-700 font-mono text-xs font-bold">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-600 animate-ping" />
                RECORDING LIVE AUDIO STREAM
              </div>
              <div className="flex items-center justify-center gap-1 text-xs text-forest/70 font-mono">
                <Clock size={12} />
                <span>{remaining}s remaining (auto-stops at {maxDuration}s)</span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-forest/70 font-mono">
              Click microphone to record live audio • Max {maxDuration}s
            </p>
          )}
        </div>
      </div>

      {/* Level visualizer bars */}
      {isRecording && (
        <div className="flex items-end justify-center gap-[3px] h-9 pt-2">
          {Array.from({ length: 24 }).map((_, i) => {
            const barLevel = Math.random() * audioLevel;
            return (
              <div
                key={i}
                className="w-1.5 rounded-full transition-all duration-75"
                style={{
                  height: `${Math.max(4, barLevel * 36)}px`,
                  backgroundColor: barLevel > 0.6
                    ? '#E11D48'
                    : barLevel > 0.3
                    ? '#18280E'
                    : '#C5FF34',
                }}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
