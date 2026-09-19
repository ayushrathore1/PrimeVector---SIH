import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Cpu, Database, Shield, Globe, Layers, Sparkles, AlertTriangle, ArrowUpRight } from 'lucide-react';

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
            About PrimeVector & DhVani 2
          </h1>
          <p className="text-sm text-forest/80 font-normal leading-relaxed max-w-3xl">
            PrimeVector provides real-time voice authenticity detection powered by DhVani 2 — a purpose-built acoustic model designed to detect AI-generated, cloned, and manipulated speech in telephone calls, VoIP communications, and enterprise verification systems.
          </p>
        </div>

        {/* Model Card Table */}
        <section className="bg-sage-1 border border-forest/10 rounded-2xl p-8 spade-cut-md space-y-6 shadow-spade">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-forest text-lemongrass flex items-center justify-center font-bold shadow-sm">
              <Sparkles size={20} />
            </div>
            <div>
              <h2 className="font-display text-2xl font-extrabold text-forest">DhVani 2 Technical Model Card</h2>
              <p className="text-xs font-mono text-forest/70">ResNet-SE + BiGRU + Multi-Head Attention Architecture</p>
            </div>
          </div>

          <div className="bg-white border border-forest/10 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-xs font-mono">
              <tbody className="divide-y divide-forest/5">
                {[
                  ['Model Name', 'DhVani Voice Deepfake Detector v2.0'],
                  ['Target Task', 'Binary classifier (bonafide vs. spoof)'],
                  ['Topology', 'ResNet-SE blocks + 2-layer BiGRU + Multi-Head Attention'],
                  ['Parameter Count', '~6M Parameters (v1 was ~1.2M)'],
                  ['Input Features', '16kHz mono PCM → 3-channel (Log-Mel + Δ + Δ²)'],
                  ['Feature Specs', 'n_mels=80, n_fft=2048, hop_length=160 (10ms), win_length=400 (25ms)'],
                  ['Output', 'Synthetic probability [0.0 = Bonafide, 1.0 = Spoof]'],
                  ['P99 Inference Latency', '<50ms per 3-second audio chunk on CPU'],
                  ['Loss Function', 'Focal Loss (hard example mining)'],
                  ['Augmentation', 'SpecAugment + Online (noise, telephone, reverb, speed) + Mixup α=0.2'],
                  ['Label Smoothing', '0.05'],
                  ['Framework', 'PyTorch'],
                  ['Training Compute', 'Google Colab Free Tier (T4 GPU)'],
                ].map(([key, val]) => (
                  <tr key={key} className="hover:bg-sage-1/50 transition-colors">
                    <td className="py-3 px-5 text-forest/70 font-bold whitespace-nowrap w-52">{key}</td>
                    <td className="py-3 px-5 text-forest font-semibold">{val}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Evaluation Metrics — Honest */}
        <section className="bg-amber-50 border border-amber-200 rounded-2xl p-6 spade-cut-md space-y-4">
          <div className="flex items-center gap-2 text-amber-800 font-display text-lg font-bold">
            <AlertTriangle size={18} />
            <h2>Evaluation Metrics — Pending Measurement</h2>
          </div>
          <p className="text-xs text-amber-900/80 font-sans leading-relaxed">
            Per our model card policy, all evaluation metrics below must be filled with <strong>actual measured results</strong> after training completes. We do not present targets or estimates as achieved results.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            {['Accuracy', 'Precision', 'Recall', 'F1', 'ROC-AUC', 'EER'].map((metric) => (
              <div key={metric} className="bg-white border border-amber-200 rounded-lg p-3 text-center">
                <div className="text-xs font-mono text-amber-800 font-bold">{metric}</div>
                <div className="text-lg font-display font-extrabold text-amber-600 mt-1">—</div>
                <div className="text-[10px] font-mono text-amber-700/60">Post-training</div>
              </div>
            ))}
          </div>
        </section>

        {/* v2 Improvements Table */}
        <section className="bg-sage-1 border border-forest/10 rounded-2xl p-8 spade-cut-md space-y-4">
          <h2 className="font-display text-2xl font-extrabold text-forest flex items-center gap-2">
            <ArrowUpRight size={20} className="text-emerald-600" />
            v2 Improvements Over v1
          </h2>
          <div className="bg-white border border-forest/10 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="bg-forest text-lemongrass">
                  <th className="py-3 px-5 text-left font-bold">Improvement</th>
                  <th className="py-3 px-5 text-left font-bold">v1</th>
                  <th className="py-3 px-5 text-left font-bold">v2</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-forest/5 text-forest">
                {[
                  ['Architecture', '4-block vanilla CNN', 'ResNet-SE + BiGRU + Multi-Head Attention'],
                  ['Features', '1-ch Log-Mel', '3-ch Log-Mel + Delta + Delta²'],
                  ['Parameters', '~1.2M', '~6M'],
                  ['Loss', 'BCEWithLogitsLoss', 'Focal Loss (hard example mining)'],
                  ['SpecAugment', 'None', 'Time + frequency masking'],
                  ['Training Augmentation', 'Eval-time only', 'Online (noise, telephone, reverb, speed)'],
                  ['Mixup', 'None', 'Alpha=0.2'],
                  ['Label Smoothing', 'None', '0.05'],
                  ['Data per Language', '30 samples', '200 samples'],
                  ['Genuine Data Source', 'FLEURS fallback', 'Vaani ONLY (strict)'],
                  ['Scheduler', 'Cosine', 'CosineAnnealingWarmRestarts'],
                ].map(([improvement, v1, v2]) => (
                  <tr key={improvement} className="hover:bg-sage-1/50 transition-colors">
                    <td className="py-2.5 px-5 font-bold text-forest/70">{improvement}</td>
                    <td className="py-2.5 px-5 text-forest/60">{v1}</td>
                    <td className="py-2.5 px-5 font-semibold text-emerald-800">{v2}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* How DhVani 2 Works */}
        <section className="space-y-6">
          <h2 className="font-display text-2xl font-bold text-forest">Acoustic Feature Extraction Pipeline</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: Layers,
                title: '3-Channel Spectrogram',
                desc: 'Raw 16kHz mono PCM is converted into an 80-band Log-Mel spectrogram, augmented with velocity (Delta) and acceleration (Delta²) features. This 3-channel stack exposes phase discontinuities characteristic of neural voice cloners.',
              },
              {
                icon: Cpu,
                title: 'ResNet-SE Backbone',
                desc: 'Squeeze-and-Excitation ResNet blocks reweight frequency channels dynamically, suppressing environmental background noise while isolating unnatural spectral phase artifacts from synthetic speech.',
              },
              {
                icon: Brain,
                title: 'BiGRU + Attention',
                desc: 'Bidirectional GRUs model long-term prosodic rhythm across time, while multi-head attention highlights temporal frames exhibiting artificial vocoder synthesis patterns.',
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
              <h4 className="font-mono text-xs text-forest font-extrabold uppercase">Genuine Speech (Bonafide)</h4>
              <ul className="space-y-1.5 font-mono text-xs">
                <li>• <strong>Dataset:</strong> ARTPARK-IISc/Vaani (HuggingFace streaming)</li>
                <li>• <strong>Languages:</strong> Hindi, English, Marathi, Gujarati</li>
                <li>• <strong>Access:</strong> Streaming only (NEVER downloaded in full)</li>
                <li>• <strong>Diversity:</strong> Multi-speaker, varied states, districts, genders</li>
                <li>• <strong>Label:</strong> bonafide</li>
              </ul>
            </div>

            <div className="bg-white p-5 rounded-xl border border-forest/10 space-y-2">
              <h4 className="font-mono text-xs text-forest font-extrabold uppercase">Synthetic & Cloned Attacks (Spoof)</h4>
              <ul className="space-y-1.5 font-mono text-xs">
                <li>• <strong>Sources:</strong> Publicly available deepfake/anti-spoofing datasets</li>
                <li>• <strong>Attack types:</strong> TTS, voice conversion, replay</li>
                <li>• <strong>Labels:</strong> Preserved per-attack-type (not collapsed)</li>
                <li>• <strong>Splits:</strong> Speaker-level separation (70% Train / 15% Val / 15% Test)</li>
                <li>• <strong>Guarantee:</strong> No speaker appears in multiple splits</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Limitations */}
        <section className="bg-sage-1 border border-forest/10 rounded-2xl p-8 spade-cut-md space-y-4">
          <div className="flex items-center gap-2 text-forest font-display text-xl font-bold">
            <AlertTriangle size={20} className="text-amber-600" />
            <h2>Known Limitations & Ethical Considerations</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-forest/80 font-sans leading-relaxed pt-2">
            <div className="bg-white p-5 rounded-xl border border-forest/10 space-y-2">
              <h4 className="font-mono text-xs text-forest font-extrabold uppercase">Technical Limitations</h4>
              <ul className="space-y-1.5 font-mono text-xs">
                <li>• <strong>Language Coverage:</strong> Only 4 Indian languages (expandable)</li>
                <li>• <strong>Dataset Size:</strong> Pilot dataset (~500 MB) may be insufficient for production</li>
                <li>• <strong>Modern TTS:</strong> Not yet tested against latest synthesis systems</li>
                <li>• <strong>Calibration:</strong> Label smoothing improves but does not guarantee calibration</li>
                <li>• <strong>Model Size:</strong> v2 is ~5x larger than v1 (still &lt;50ms on CPU)</li>
              </ul>
            </div>

            <div className="bg-white p-5 rounded-xl border border-forest/10 space-y-2">
              <h4 className="font-mono text-xs text-forest font-extrabold uppercase">Ethical Considerations</h4>
              <ul className="space-y-1.5 font-mono text-xs">
                <li>• <strong>False Positives:</strong> A bonafide call flagged as synthetic could block legitimate transactions</li>
                <li>• <strong>Dialect Bias:</strong> Model may perform differently across regional accents</li>
                <li>• <strong>Privacy:</strong> Inference operates in RAM only — zero audio retention</li>
              </ul>
              <h4 className="font-mono text-xs text-forest font-extrabold uppercase mt-4">What DhVani Does NOT Do</h4>
              <ul className="space-y-1.5 font-mono text-xs">
                <li>• Does NOT identify WHO is speaking (enrollment-service)</li>
                <li>• Does NOT decide whether to block (policy-threshold-engine)</li>
                <li>• Does NOT perform Noisy-OR fusion (risk-fusion-engine)</li>
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
              Audio byte arrays exist solely in volatile RAM memory during forward pass inference. Inputs are dereferenced immediately after scoring — zero files are written to disk, databases, or persistent caches. This is a hard invariant enforced across the entire platform.
            </p>
          </div>

          <div className="bg-sage-1 border border-forest/10 rounded-xl p-6 spade-cut-sm space-y-2">
            <Globe size={20} className="text-forest" />
            <h4 className="font-display text-lg font-bold text-forest">Fail-Safe Design (Never Fails Open)</h4>
            <p className="text-xs text-forest/70 leading-relaxed font-sans">
              Missing signals, timeouts, or dependency outages always result in conservative recommendations. The system never treats missing data as safe — it defaults to callback verification to protect against social engineering attacks.
            </p>
          </div>
        </section>

      </div>
    </div>
  );
}
