import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Cpu, Database, Shield, Globe, Layers, Sparkles } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white text-forest selection:bg-lemongrass py-10">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        
        {/* Header */}
        <div className="space-y-2 pb-6 border-b border-forest/10">
          <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-forest/70">
            <Brain size={14} className="text-forest" />
            <span>Neural Architecture Reference</span>
          </div>
          <h1 className="font-display text-4xl font-extrabold text-forest tracking-tight">
            About PrimeVector & Dhwani 2
          </h1>
          <p className="text-sm text-forest/80 font-normal leading-relaxed max-w-3xl">
            PrimeVector provides real-time voice authenticity detection powered by Dhwani 2 — a purpose-built acoustic model trained specifically to distinguish genuine human speech from AI-synthesized audio.
          </p>
        </div>

        {/* Model Card Table */}
        <section className="bg-sage-1 border border-forest/10 rounded-2xl p-8 spade-cut-md space-y-6 shadow-spade">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-forest text-lemongrass flex items-center justify-center font-bold shadow-sm">
              <Sparkles size={20} />
            </div>
            <div>
              <h2 className="font-display text-2xl font-extrabold text-forest">Dhwani 2 Technical Model Card</h2>
              <p className="text-xs font-mono text-forest/70">ResNet-SE + BiGRU + Multi-Head Attention Architecture</p>
            </div>
          </div>

          <div className="bg-white border border-forest/10 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-xs font-mono">
              <tbody className="divide-y divide-forest/5">
                {[
                  ['Model Name', 'Dhwani Voice Deepfake Detector v2.0'],
                  ['Target Task', 'Binary Acoustic Spoof Classification (Real Human vs. AI Cloned)'],
                  ['Topology', 'ResNet-SE blocks + 2-layer BiGRU + 8-head Multi-Head Attention'],
                  ['Parameter Count', '6.2M Parameters (~22.9 MB footprint)'],
                  ['Input Features', '16kHz mono audio → 3-channel Log-Mel Spectrogram + Delta + Delta-Delta'],
                  ['Output Verdict', 'Spoof probability [0.0 = Real Human, 1.0 = AI Synthetic]'],
                  ['P99 Inference Latency', '<50ms per 3-second audio chunk'],
                  ['Benchmark Accuracy', '98.6% Accuracy on evaluation test splits'],
                  ['F1 Score', '97.4% F1 Score'],
                  ['Framework', 'PyTorch 2.x + ONNX Runtime C++ Server'],
                ].map(([key, val]) => (
                  <tr key={key} className="hover:bg-sage-1/50 transition-colors">
                    <td className="py-3 px-5 text-forest/70 font-bold whitespace-nowrap w-48">{key}</td>
                    <td className="py-3 px-5 text-forest font-semibold">{val}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* How Dhwani 2 Works */}
        <section className="space-y-6">
          <h2 className="font-display text-2xl font-bold text-forest">Acoustic Feature Extraction Pipeline</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: Layers,
                title: '3-Channel Spectrogram',
                desc: 'Raw audio is converted into an 80-band Log-Mel spectrogram, augmented with velocity (Delta) and acceleration (Delta-Delta) features. This 3-channel stack exposes phase discontinuities characteristic of neural voice cloners.',
              },
              {
                icon: Cpu,
                title: 'ResNet-SE Backbone',
                desc: 'Squeeze-and-Excitation ResNet blocks reweight frequency channels dynamically, suppressing environmental background noise while isolating unnatural spectral phase artifacts.',
              },
              {
                icon: Brain,
                title: 'BiGRU + Attention',
                desc: 'Bidirectional GRUs model long-term prosodic rhythm across time, while 8-head multi-head attention highlights temporal frames exhibiting artificial vocoder synthesis patterns.',
              },
            ].map(({ icon: Icon, title, desc }, i) => (
              <div key={title} className="bg-sage-1 border border-forest/10 rounded-xl p-6 spade-cut-sm space-y-3">
                <div className="w-9 h-9 rounded-lg bg-forest text-lemongrass flex items-center justify-center font-bold">
                  <Icon size={18} />
                </div>
                <h4 className="font-display text-lg font-bold text-forest">{title}</h4>
                <p className="text-xs text-forest/70 leading-relaxed font-normal">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Training Datasets */}
        <section className="bg-sage-1 border border-forest/10 rounded-2xl p-8 spade-cut-md space-y-4">
          <div className="flex items-center gap-2 text-forest font-display text-xl font-bold">
            <Database size={20} />
            <h2>Training Datasets & Generalization</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-forest/80 font-sans leading-relaxed pt-2">
            <div className="bg-white p-5 rounded-xl border border-forest/10 space-y-2">
              <h4 className="font-mono text-xs text-forest font-extrabold uppercase">Genuine Speech Baselines</h4>
              <ul className="space-y-1.5 font-mono text-xs">
                <li>• <strong>Dataset:</strong> ARTPARK-IISc Vaani Speech Dataset</li>
                <li>• <strong>Languages:</strong> Hindi, English, Marathi, Gujarati</li>
                <li>• <strong>Diversity:</strong> Multi-speaker, varied acoustic room profiles</li>
                <li>• <strong>Policy:</strong> Transient streaming ingestion during training</li>
              </ul>
            </div>

            <div className="bg-white p-5 rounded-xl border border-forest/10 space-y-2">
              <h4 className="font-mono text-xs text-forest font-extrabold uppercase">Synthetic & Cloned Attacks</h4>
              <ul className="space-y-1.5 font-mono text-xs">
                <li>• <strong>Generators:</strong> Voice conversion, Neural TTS, Tacotron2, VITS</li>
                <li>• <strong>Attack Types:</strong> Zero-shot voice cloning, vocoder artifacts</li>
                <li>• <strong>Splits:</strong> Disjoint speaker isolation (70% Train / 15% Val / 15% Test)</li>
                <li>• <strong>Validation:</strong> Zero speaker leakage across evaluation sets</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Guarantees */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-sage-1 border border-forest/10 rounded-xl p-6 spade-cut-sm space-y-2">
            <Shield size={20} className="text-emerald-700" />
            <h4 className="font-display text-lg font-bold text-forest">RAM-Only Zero Data Retention</h4>
            <p className="text-xs text-forest/70 leading-relaxed font-sans">
              Audio byte arrays exist solely in volatile RAM memory during forward pass inference. Inputs are dereferenced immediately after scoring — zero files are written to disk, databases, or persistent caches.
            </p>
          </div>

          <div className="bg-sage-1 border border-forest/10 rounded-xl p-6 spade-cut-sm space-y-2">
            <Globe size={20} className="text-forest" />
            <h4 className="font-display text-lg font-bold text-forest">High-Throughput Microservice</h4>
            <p className="text-xs text-forest/70 leading-relaxed font-sans">
              The underlying FastAPI & ONNX Runtime service executes inference in under 50ms per batch on standard CPU microservices, enabling real-time deployment in high-concurrency telephony nodes.
            </p>
          </div>
        </section>

      </div>
    </div>
  );
}
