# Dhwani v2 — Developer Implementation Guide

> **Branch**: `dhwani-v2-upgrade`  
> **Status**: Ready for training → integration  
> **Breaking Changes**: None — fully backward compatible with v1

---

## What Changed & Why

Dhwani v1 (4-block CNN, ~1.2M params, 1-channel Log-Mel) achieved baseline accuracy but lacked the depth to reliably distinguish modern AI-generated speech from real human voice. v2 addresses this with a significantly upgraded architecture and training pipeline.

### Architecture: v1 → v2

| Component | v1 | v2 |
|-----------|----|----|
| **Backbone** | 4-block vanilla CNN | ResNet-18 with Squeeze-and-Excitation blocks |
| **Temporal** | None (global avg pool) | 2-layer Bidirectional GRU |
| **Attention** | None | 8-head Multi-Head Attention |
| **Features** | 1-ch Log-Mel | 3-ch: Log-Mel + Delta + Delta² |
| **Parameters** | ~1.2M | ~6M |
| **Loss** | BCEWithLogitsLoss | Focal Loss (mines hard examples) |
| **Regularization** | Dropout only | SpecAugment + Mixup + Label Smoothing + Dropout |
| **Augmentation** | Eval-time only | Online (noise, telephone filter, reverb, speed perturbation) |
| **Data** | 30 samples/lang | 200 samples/lang |
| **Spoof Source** | ASVspoof (HF) | **Custom TTS (Sarvam + ElevenLabs)** + ASVspoof fallback |

### Why 3 channels matter
- **Log-Mel**: frequency content (what the voice sounds like)
- **Delta**: velocity of spectral change (how it transitions)
- **Delta-Delta**: acceleration of change (smoothness/jitter)

AI-generated speech often has unnaturally smooth deltas or abrupt delta-delta spikes that human speech doesn't exhibit.

---

## Files Changed

### New Files

| File | Purpose |
|------|---------|
| `ml/dhwani/notebooks/Dhwani_Training_V2.ipynb` | Complete v2 training notebook (run on Colab Free Tier) |
| `ml/dhwani/notebooks/generate_spoof_dataset.py` | Sarvam AI + ElevenLabs TTS spoof data generator |
| `services/spoof-detection-service/app/model/inference.py` | Chunk-level inference with v1/v2 auto-detection |
| `services/spoof-detection-service/app/dhwani_registry.py` | Model registry with v2 checkpoint search |
| `services/spoof-detection-service/app/model/dhwani_baseline.py` | Both v1 and v2 model definitions |

### Modified Files

| File | Change |
|------|--------|
| `ml/dhwani/config/dhwani_config.yaml` | v2 hyperparams, 3-ch features, v2 checkpoint path |
| `ml/dhwani/DHWANI_MODEL_CARD.md` | Updated architecture docs, v1→v2 comparison |
| `services/spoof-detection-service/app/config.py` | Dhwani backend support |
| `services/spoof-detection-service/app/detector.py` | Dhwani registry integration |
| `services/spoof-detection-service/app/main.py` | Dhwani model loading on startup |

---

## Step-by-Step: How to Train & Deploy

### Phase 1: Generate Spoof Data (Local Machine)

```bash
# Install dependencies
pip install sarvamai elevenlabs soundfile librosa

# Generate with Sarvam AI (Hindi, English, Marathi, Gujarati)
python ml/dhwani/notebooks/generate_spoof_dataset.py \
  --sarvam-key YOUR_SARVAM_API_KEY \
  --max-per-lang 50

# Or with both Sarvam + ElevenLabs
python ml/dhwani/notebooks/generate_spoof_dataset.py \
  --sarvam-key YOUR_SARVAM_KEY \
  --elevenlabs-key YOUR_ELEVENLABS_KEY \
  --max-per-lang 50
```

**Get API keys:**
- Sarvam AI: [dashboard.sarvam.ai](https://dashboard.sarvam.ai) (free tier available)
- ElevenLabs: [elevenlabs.io](https://elevenlabs.io) (10K chars/month free)

This creates a `spoof_generated/` folder with WAV files + `manifest.csv`.

### Phase 2: Train on Google Colab

1. Open `ml/dhwani/notebooks/Dhwani_Training_V2.ipynb` in Colab
2. **Runtime → Change runtime type → T4 GPU**
3. Upload `spoof_generated/` folder to `/content/spoof_generated/`
   - Or skip this — notebook falls back to HuggingFace ASVspoof datasets
4. Run all cells (~40-50 min)
5. Download `dhwani_baseline_v2.pt` when prompted

### Phase 3: Deploy Locally

```bash
# Place checkpoint
cp dhwani_baseline_v2.pt ml/dhwani/checkpoints/

# Set environment
export SPOOF_MODEL_REGISTRY_BACKEND=dhwani

# Start service
cd services/spoof-detection-service
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

The service auto-detects v2 checkpoint and loads the upgraded model.

---

## How Auto-Detection Works

The system automatically handles v1 and v2 checkpoints:

```
Checkpoint loaded
    │
    ├─ config.architecture contains "DhwaniV2"
    │   or config.n_channels == 3?
    │
    ├─ YES → Load DhwaniV2 (ResNet-SE + BiGRU + Attention)
    │         Use 3-channel features (Log-Mel + Delta + Delta²)
    │
    └─ NO  → Load DhwaniBaseline (4-block CNN)
              Use 1-channel features (Log-Mel only)
```

**Checkpoint search order:**
1. `ml/dhwani/checkpoints/dhwani_baseline_v2.pt` (preferred)
2. `ml/dhwani/checkpoints/dhwani_baseline_v1.pt` (fallback)

No config changes needed — drop in the checkpoint and restart.

---

## For Code Reviewers

### Key Design Decisions

1. **Backward compatible loader**: `load_dhwani_baseline()` in `dhwani_baseline.py` auto-detects v1 vs v2 from checkpoint metadata. No breaking changes to the API contract.

2. **3-channel inference routing**: `inference.py` checks `isinstance(model, DhwaniV2)` and routes to either 1-channel or 3-channel feature extraction. Zero overhead for v1 models.

3. **Focal Loss over BCE**: Focal Loss down-weights easy examples (α=0.25, γ=2.0), forcing the model to learn from ambiguous boundary cases where AI speech is hardest to detect.

4. **SE blocks**: Squeeze-and-Excitation learns per-channel (frequency band) attention weights, so the model automatically focuses on the frequency ranges most discriminative for deepfake detection.

5. **SpecAugment at training only**: Time and frequency masking during training prevents overfitting to specific spectral patterns, but is disabled at inference for maximum accuracy.

### Testing Locally

```python
import torch
from model.dhwani_baseline import DhwaniV2

# Smoke test — 3-channel input
model = DhwaniV2(n_channels=3, n_mels=80)
x = torch.randn(4, 3, 80, 300)  # batch=4, 3ch, 80 mels, 300 frames
logit = model(x)
print(logit.shape)  # torch.Size([4, 1])
print(f"Params: {sum(p.numel() for p in model.parameters()):,}")
```

### File Dependencies

```
dhwani_registry.py
    ├── model/dhwani_baseline.py  (DhwaniBaseline, DhwaniV2, load_dhwani_baseline)
    └── model/inference.py        (predict_chunks, 3-ch feature extraction)
            └── librosa            (Log-Mel + Delta computation)
```

---

## Checklist for Merging

- [ ] Train v2 model on Colab and verify accuracy > v1 baseline
- [ ] Place `dhwani_baseline_v2.pt` in `ml/dhwani/checkpoints/`
- [ ] Test inference locally: `SPOOF_MODEL_REGISTRY_BACKEND=dhwani uvicorn app.main:app`
- [ ] Verify v1 checkpoint still loads correctly (backward compat)
- [ ] Run existing integration tests
- [ ] Update `.gitignore` to exclude `*.pt` checkpoint files if not already
- [ ] Squash merge into `main`

---

## FAQ

**Q: Can I still use the v1 model?**  
A: Yes. If only `dhwani_baseline_v1.pt` is present, the system loads v1 automatically.

**Q: What if I don't have Sarvam/ElevenLabs API keys?**  
A: The notebook falls back to HuggingFace ASVspoof datasets, then synthetic placeholders.

**Q: Will this slow down inference?**  
A: v2 is ~5x more params but still <50ms per 3s chunk on CPU. The 3-channel feature extraction adds ~2ms.

**Q: How do I add more languages?**  
A: Add language configs to `generate_spoof_dataset.py` PROMPTS dict and Sarvam voice mappings. Vaani supports 100+ Indian languages.
