import React from 'react';
import { Smartphone, Mic, Download, ShieldCheck, CheckCircle2, AlertTriangle, Terminal, Lock } from 'lucide-react';
import CodeBlock from '../components/CodeBlock';

export default function AndroidPage() {
  const androidBuildScript = `# Build APK from source (Android Studio / Gradle)
cd android/
./gradlew assembleDebug

# Output APK path:
# android/app/build/outputs/apk/debug/app-debug.apk

# Install on target Android device via ADB:
adb install android/app/build/outputs/apk/debug/app-debug.apk`;

  return (
    <div className="min-h-screen bg-white text-forest selection:bg-lemongrass py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Header */}
        <div className="pb-6 border-b border-forest/10">
          <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-forest/70 mb-1">
            <Smartphone size={14} className="text-forest" />
            <span>Mobile Edge Client</span>
          </div>
          <h1 className="font-display text-4xl font-extrabold text-forest tracking-tight">PrimeVector Android Client Showcase</h1>
          <p className="text-xs font-mono text-forest/60 mt-1">
            Live edge client featuring real-time mic-based voice ingestion & Sarvam STT streaming
          </p>
        </div>

        {/* Hero Showcase Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          {/* Left: Honest Technical Rationale */}
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sage-1 border border-forest/15 text-forest font-mono text-xs font-semibold">
              <Mic size={14} /> Real-Time Microphone Ingestion Client
            </div>

            <h2 className="font-display text-3xl font-extrabold text-forest leading-tight">
              Designed for real-time mobile caller verification without telephony hacks.
            </h2>

            <div className="space-y-4 text-xs text-forest/80 font-sans leading-relaxed">
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-2">
                <div className="flex items-center gap-2 font-mono font-bold text-amber-800">
                  <Lock size={14} /> Crucial Technical Distinction: Mic Capture vs. Call Recording
                </div>
                <p className="text-amber-900/80">
                  The PrimeVector Android client uses <strong>real-time ambient mic capture</strong>, NOT legacy Android call recording APIs. Modern Android versions (Android 9+) explicitly block background call recording for privacy compliance.
                </p>
                <p className="text-amber-900/80">
                  By using mic-based ambient ingestion during speaker verification, PrimeVector runs on 100% stock, unrooted Android devices while achieving sub-60ms pipeline latency.
                </p>
              </div>

              <ul className="space-y-2 font-mono text-xs">
                <li className="flex items-center gap-2 text-forest">
                  <CheckCircle2 size={14} className="text-emerald-700 shrink-0" /> Integrated Sarvam STT for multilingual speech-to-text
                </li>
                <li className="flex items-center gap-2 text-forest">
                  <CheckCircle2 size={14} className="text-emerald-700 shrink-0" /> Sub-60ms PCM frame streaming directly to orchestrator
                </li>
                <li className="flex items-center gap-2 text-forest">
                  <CheckCircle2 size={14} className="text-emerald-700 shrink-0" /> Visual acoustic waveform & instant risk alert toasts
                </li>
              </ul>
            </div>
          </div>

          {/* Right: UI Screenshots */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-xl border border-forest/10 bg-sage-1 p-2 overflow-hidden shadow-spade text-center group">
              <img
                src="/assets/android_mic_capture.png"
                alt="PrimeVector Android Real-Time Mic Capture Interface"
                className="rounded-lg w-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div className="p-2 font-mono text-[11px] text-forest/60">
                Live Mic Ingestion & Sarvam STT Stream
              </div>
            </div>

            <div className="rounded-xl border border-forest/10 bg-sage-1 p-2 overflow-hidden shadow-spade text-center group">
              <img
                src="/assets/android_fraud_alert.png"
                alt="PrimeVector Android Fraud Alert Notification Interface"
                className="rounded-lg w-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div className="p-2 font-mono text-[11px] text-forest/60">
                High-Risk Voice Clone Alert Banner
              </div>
            </div>
          </div>
        </div>

        {/* APK & Build Instructions */}
        <div className="rounded-2xl border border-forest/10 bg-sage-1 p-6 shadow-spade spade-cut-md space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-forest/10">
            <div>
              <h3 className="font-display text-xl font-bold text-forest">Android Build & Deployment</h3>
              <p className="text-xs font-mono text-forest/60">Gradle build command for Android Studio testing</p>
            </div>

            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-forest/15 hover:border-forest/40 text-forest font-mono text-xs font-semibold transition-colors"
            >
              <Download size={14} className="text-forest" />
              <span>Download APK Source</span>
            </a>
          </div>

          <CodeBlock code={androidBuildScript} language="bash" title="Build & ADB Deploy Script" />
        </div>
      </div>
    </div>
  );
}
