# Dhwani Model Card

## Model Details

| Field | Value |
|-------|-------|
| **Name** | Dhwani Voice Deepfake Detector |
| **Version** | v2.0 (v1.0 backward compatible) |
| **Type** | Binary classifier (bonafide vs. spoof) |
| **Architecture** | ResNet-SE + BiGRU + Multi-Head Attention |
| **Parameters** | ~6M (v1 was ~1.2M) |
| **Input** | 16kHz mono audio (PCM) → 3-ch (Log-Mel + Δ + Δ²) |
| **Output** | Synthetic probability [0.0, 1.0] |
| **Framework** | PyTorch |
| **Training compute** | Google Colab Free Tier (T4 GPU) |
| **Inference target** | CPU, <50ms per 3-second chunk |

## Intended Use

Dhwani is designed to detect AI-generated, cloned, and manipulated speech in:
- Telephone calls
- VoIP communications
- Banking voice verification
- Enterprise communication systems
- Government/high-risk workflows

It operates as the ML engine behind PrimeVector's `spoof-detection-service`, producing a `synthetic_probability` signal consumed by the `risk-fusion-engine`.

**Dhwani does NOT make policy decisions** (block/allow). That responsibility belongs to the `risk-fusion-engine` and `policy-threshold-engine`.

## Training Data

### Genuine Speech
- **Dataset**: ARTPARK-IISc/Vaani
- **Languages**: Hindi, English, Marathi, Gujarati
- **Access**: Streaming only (NEVER downloaded in full)
- **Diversity**: Multiple speakers, states, districts, genders
- **Label**: bonafide

### Spoof Data
- **Sources**: Publicly available deepfake/anti-spoofing datasets
- **Attack types**: TTS, voice conversion, replay (where available)
- **Labels**: Preserved per-attack-type (not collapsed into single class)

### Data Splits
- **Method**: Speaker-level separation (mandatory)
- **Ratio**: 70% train / 15% validation / 15% test
- **Guarantee**: No speaker appears in multiple splits

## Audio Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Sample rate | 16 kHz | Matches PrimeVector pipeline |
| Channels | Mono | Standard for telephony |
| n_mels | 80 | Matches feature-extraction-service |
| n_fft | 2048 | Standard for 16kHz audio |
| hop_length | 160 (10ms) | Matches PrimeVector design |
| win_length | 400 (25ms) | Matches PrimeVector design |
| Feature channels | 3 (v2) | Log-Mel + Delta + Delta² |

## v2 Improvements Over v1

| Improvement | v1 | v2 |
|-------------|----|----|  
| Architecture | 4-block vanilla CNN | ResNet-SE + BiGRU + Multi-Head Attention |
| Features | 1-ch Log-Mel | 3-ch Log-Mel + Delta + Delta² |
| Parameters | ~1.2M | ~6M |
| Loss | BCEWithLogitsLoss | Focal Loss (hard example mining) |
| SpecAugment | None | Time + frequency masking |
| Training augmentation | Eval-time only | Online (noise, telephone, reverb, speed) |
| Mixup | None | Alpha=0.2 |
| Label smoothing | None | 0.05 |
| Data per language | 30 samples | 200 samples |
| Genuine data source | FLEURS fallback | Vaani ONLY (strict) |
| Scheduler | Cosine | CosineAnnealingWarmRestarts |

## Evaluation Metrics

> **⚠️ IMPORTANT**: All values below must be filled with ACTUAL MEASURED results
> after training. Do NOT present targets or estimates as achieved results.

| Metric | Value |
|--------|-------|
| Accuracy | *measured after training* |
| Precision | *measured after training* |
| Recall | *measured after training* |
| F1 | *measured after training* |
| ROC-AUC | *measured after training* |
| EER | *measured after training* |

## Limitations and Risks

### Known Limitations
1. **Language coverage**: Only 4 Indian languages (expandable)
2. **Dataset size**: Pilot dataset (~500 MB) may be insufficient for production
3. **Modern TTS**: Not yet tested against latest synthesis systems
4. **Calibration**: Label smoothing improves but does not guarantee calibration
5. **Inference cost**: v2 is ~5x larger than v1 (still <50ms on CPU)

### Ethical Considerations
- **False positives**: A bonafide call flagged as synthetic could block legitimate transactions
- **Dialect bias**: Model may perform differently across regional accents
- **Privacy**: Inference operates in RAM only — zero audio retention

### What This Model Does NOT Do
- Does not identify WHO is speaking (that's enrollment-service)
- Does not decide whether to block a call (that's policy-threshold-engine)
- Does not perform Noisy-OR fusion (that's risk-fusion-engine)
- Does not claim that "AI voices always have low pitch variance" (too simplistic)

## Reproducibility

1. Open `Dhwani_Training_V2.ipynb` on Google Colab (Free Tier, GPU runtime)
2. Set HuggingFace token (needed for Vaani access)
3. Run all cells — estimated ~40-50 min with T4 GPU
4. Training logs, metrics, and checkpoint are saved automatically
5. Download `dhwani_baseline_v2.pt` and place in `ml/dhwani/checkpoints/`
6. Set `SPOOF_MODEL_REGISTRY_BACKEND=dhwani` in environment
7. v1 checkpoint remains at `dhwani_baseline_v1.pt` as fallback

## Citation

```
Vaani Dataset: ARTPARK-IISc/Vaani (https://huggingface.co/datasets/ARTPARK-IISc/Vaani)
PrimeVector: Voice Integrity & Impersonation Prevention Platform
```
