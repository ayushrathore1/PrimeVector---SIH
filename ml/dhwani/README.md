# Dhwani — Voice Deepfake Detection Model

**Part of PrimeVector Voice Integrity Platform**

Dhwani is a multilingual voice deepfake detection model trained on Indian speech data (Vaani dataset) to detect AI-generated, cloned, and manipulated speech in real-time communication channels.

## Quick Start

### 1. Train on Google Colab

1. Open [Google Colab](https://colab.research.google.com)
2. Upload `notebooks/dhwani_training.py` (or paste its contents)
3. Select **GPU runtime** (Runtime → Change runtime type → GPU)
4. Run all cells end-to-end
5. Download the checkpoint file when prompted

### 2. Integrate Locally

```bash
# Place the checkpoint
mkdir -p ml/dhwani/checkpoints/
# Move downloaded dhwani_baseline_v1.pt here

# Set environment variable
export SPOOF_MODEL_REGISTRY_BACKEND=dhwani

# Start the spoof-detection service
cd services/spoof-detection-service/app
uvicorn main:app --host 0.0.0.0 --port 8002
```

### 3. Verify

```bash
curl -X POST http://localhost:8002/v1/detect \
  -H "Content-Type: application/json" \
  -d '{
    "call_session_id": "test-001",
    "tenant_id": "t1",
    "audio_pcm_base64": "<base64-encoded-16bit-PCM>"
  }'
```

Expected response:
```json
{
  "score": 0.87,
  "confidence": 0.91,
  "available": true,
  "detail": "model=Dhwani-Baseline-v1.0, path=trained-model, architecture=DhwaniBaseline-CNN-4block"
}
```

## Architecture

### Dhwani-Baseline (v1.0)
```
Audio → 16kHz mono → 80-band Log-Mel → 4-block CNN → Global Avg Pool → MLP → P(synthetic)
```
- ~1.2M parameters
- <50ms inference per 3-second chunk on CPU
- Matches PrimeVector feature-extraction-service parameters

### Dhwani-Advanced (v2.0, optional)
```
                   AUDIO
                     │
      ┌──────────────┼──────────────┐
      │              │              │
   Log-Mel        Prosody       SSL (frozen)
    Branch         Branch         Branch
      │              │              │
     CNN          BiGRU/MLP      WavLM
      │              │              │
      └──────────────┼──────────────┘
                     ▼
               Attention Fusion → MLP → P(synthetic)
```

### Important Technical Note

Standard 80-band Log-Mel spectrograms represent **magnitude-spectrum information only**. They do NOT directly contain phase information. If phase analysis is needed, the advanced model supports an optional phase-aware branch.

## Dataset

- **Genuine speech**: ARTPARK-IISc/Vaani (Hindi, English, Marathi, Gujarati)
  - Streamed via HuggingFace — **NEVER downloaded in full** (7+ TB)
  - License: see [Vaani on HuggingFace](https://huggingface.co/datasets/ARTPARK-IISc/Vaani)
- **Spoof data**: Publicly available deepfake/anti-spoofing datasets
- **Speaker-level splits**: No speaker appears in multiple train/val/test splits

## Project Structure

```
ml/dhwani/
├── config/
│   └── dhwani_config.yaml          # Model & training configuration
├── notebooks/
│   └── dhwani_training.py          # Colab training notebook
├── checkpoints/                    # Downloaded from Colab (.gitignored)
│   ├── dhwani_baseline_v1.pt
│   └── dhwani_advanced_v1.pt
└── README.md

services/spoof-detection-service/app/
├── model/
│   ├── dhwani_baseline.py          # CNN architecture (inference only)
│   ├── dhwani_advanced.py          # Multi-branch architecture
│   └── inference.py                # Chunk-level inference engine
├── dhwani_registry.py              # DhwaniModelRegistry
├── config.py                       # Added "dhwani" backend option
└── main.py                         # Added DhwaniModelRegistry to factory
```

## Configuration

Set `SPOOF_MODEL_REGISTRY_BACKEND` environment variable:

| Value | Model | Description |
|-------|-------|-------------|
| `dhwani` | Dhwani CNN | Trained on Vaani + spoof data |
| `deepfake` | ResNet18+GRU | Existing koyelog model (default) |
| `heuristic` | Log-Mel heuristic | Fallback, cannot detect modern TTS |
| `stub` | None | All requests return available=false |

## Limitations

- Trained on 4 Indian languages only (Hindi, English, Marathi, Gujarati)
- Pilot dataset is small (~500 MB) — production needs larger datasets
- Not yet tested against latest TTS systems (e.g., VALL-E, Bark)
- Inference latency not yet measured on production hardware
- Calibration (temperature scaling) not yet applied

## License

The Dhwani model code is part of the PrimeVector project. The training data (Vaani) has its own license — see the [Vaani dataset page](https://huggingface.co/datasets/ARTPARK-IISc/Vaani) for terms.
