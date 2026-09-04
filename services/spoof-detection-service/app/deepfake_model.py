"""
Deepfake voice detection model — ResNet18 + BiGRU + MultiHeadAttention.

Loads the pretrained model from koyelog/deepfake-voice-detector-sota.
Despite the upstream README's claim of Wav2Vec2, the actual trained
checkpoint is a ResNet18 CNN that operates on 128-band log-mel
spectrograms, followed by a BiGRU temporal encoder and multi-head
self-attention pooling.

Architecture (from checkpoint analysis):
  Input: (batch, 1, 128, T) log-mel spectrogram
    -> Conv2d(1, 64, 7x7, stride=2) -> BN -> ReLU -> MaxPool
    -> layer1: 2x BasicBlock(64, 64)
    -> layer2: 2x BasicBlock(64, 128, stride=2)  [with shortcut]
    -> layer3: 2x BasicBlock(128, 256, stride=2) [with shortcut]
    -> mean pool over frequency -> (batch, T', 256)
    -> BiGRU(256 -> 512)
    -> MultiHeadAttention(512, 8 heads)
    -> mean pool over time -> (batch, 512)
    -> Linear(512->512)->ReLU->BN->Drop(0.4)
    -> Linear(512->128)->ReLU->BN->Drop(0.3)
    -> Linear(128->1)   [raw logit, apply sigmoid for probability]

Model card:
  - Trained on 822K audio samples (19 datasets), 98.4% val accuracy
  - Input: 4-second audio clip at 16 kHz
  - Config: n_mels=128, n_fft=1024, hop_length=512
  - Output: scalar logit (0 = Real, 1 = Fake after sigmoid)
  - Model size: 6.1M parameters, 23.4 MB memory
  - Inference: ~25-40ms full pipeline on CPU

Audio non-retention (DESIGN.md section 7):
  Raw audio bytes are decoded to a numpy array in-memory, used to
  compute the mel spectrogram, and immediately dereferenced.  No audio
  data is written to disk, stored in a database, or logged.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Model configuration (from the checkpoint's config.json)
SAMPLE_RATE = 16000
DURATION_S = 4
MAX_SAMPLES = SAMPLE_RATE * DURATION_S  # 64000
N_MELS = 128
N_FFT = 1024
HOP_LENGTH = 512

# HuggingFace repo for weight download
MODEL_REPO = "koyelog/deepfake-voice-detector-sota"


def _build_model():
    """
    Construct the DeepfakeDetector architecture and return the nn.Module.

    Separated from weight loading so architecture can be tested independently.
    """
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    class BasicBlock(nn.Module):
        """Standard ResNet BasicBlock with optional shortcut."""
        def __init__(self, in_ch: int, out_ch: int, stride: int = 1):
            super().__init__()
            self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride=stride, padding=1, bias=False)
            self.bn1 = nn.BatchNorm2d(out_ch)
            self.conv2 = nn.Conv2d(out_ch, out_ch, 3, stride=1, padding=1, bias=False)
            self.bn2 = nn.BatchNorm2d(out_ch)
            self.shortcut = nn.Sequential()
            if stride != 1 or in_ch != out_ch:
                self.shortcut = nn.Sequential(
                    nn.Conv2d(in_ch, out_ch, 1, stride=stride, bias=False),
                    nn.BatchNorm2d(out_ch),
                )

        def forward(self, x):
            out = F.relu(self.bn1(self.conv1(x)))
            out = self.bn2(self.conv2(out))
            out += self.shortcut(x)
            return F.relu(out)

    class DeepfakeDetector(nn.Module):
        """ResNet18 CNN + BiGRU + MultiHeadAttention + Classifier."""
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 64, 7, stride=2, padding=3, bias=False)
            self.bn1 = nn.BatchNorm2d(64)
            self.layer1 = nn.Sequential(BasicBlock(64, 64), BasicBlock(64, 64))
            self.layer2 = nn.Sequential(BasicBlock(64, 128, stride=2), BasicBlock(128, 128))
            self.layer3 = nn.Sequential(BasicBlock(128, 256, stride=2), BasicBlock(256, 256))
            self.gru = nn.GRU(
                input_size=256, hidden_size=256,
                num_layers=2, batch_first=True,
                bidirectional=True, dropout=0.3,
            )
            self.attention = nn.MultiheadAttention(
                embed_dim=512, num_heads=8,
                batch_first=True, dropout=0.1,
            )
            self.classifier = nn.Sequential(
                nn.Linear(512, 512), nn.ReLU(), nn.BatchNorm1d(512), nn.Dropout(0.4),
                nn.Linear(512, 128), nn.ReLU(), nn.BatchNorm1d(128), nn.Dropout(0.3),
                nn.Linear(128, 1),
            )

        def forward(self, mel_spec):
            x = F.relu(self.bn1(self.conv1(mel_spec)))
            x = F.max_pool2d(x, 3, stride=2, padding=1)
            x = self.layer1(x)
            x = self.layer2(x)
            x = self.layer3(x)
            x = x.mean(dim=2)       # pool over frequency
            x = x.permute(0, 2, 1)  # (batch, time, 256)
            gru_out, _ = self.gru(x)
            attn_out, _ = self.attention(gru_out, gru_out, gru_out)
            pooled = attn_out.mean(dim=1)
            return self.classifier(pooled)

    return DeepfakeDetector()


def load_deepfake_model():
    """
    Download weights from HuggingFace and return a ready-to-use model.

    Returns:
        model: nn.Module in eval mode, on CPU
        version: str identifying the model version for audit trail
    """
    import torch
    from huggingface_hub import hf_hub_download

    logger.info("Downloading deepfake detector weights from %s", MODEL_REPO)
    pth_path = hf_hub_download(repo_id=MODEL_REPO, filename="pytorch_model.pth")

    model = _build_model()
    checkpoint = torch.load(pth_path, map_location="cpu", weights_only=False)

    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()

    epoch = checkpoint.get("epoch", "unknown")
    val_acc = checkpoint.get("val_accuracy", 0.0)
    version = f"koyelog-resnet18-gru-attn-ep{epoch}-acc{val_acc:.4f}"

    param_count = sum(p.numel() for p in model.parameters())
    mem_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 * 1024)
    logger.info(
        "Deepfake model loaded: version=%s, params=%s, memory=%.1fMB",
        version, f"{param_count:,}", mem_mb,
    )

    return model, version


def predict_from_pcm_base64(
    model,
    audio_pcm_base64: str,
    sample_rate: int = SAMPLE_RATE,
) -> dict:
    """
    Full inference pipeline: base64 PCM -> score.

    This is the main entry point for the spoof-detection service.
    Audio bytes are decoded in-memory, used to compute the mel
    spectrogram, and immediately dereferenced after inference.
    No audio data is persisted (DESIGN.md section 7).

    Args:
        model: The loaded DeepfakeDetector nn.Module.
        audio_pcm_base64: Base64-encoded 16-bit PCM audio.
        sample_rate: Sample rate of the audio (must be 16000).

    Returns:
        {"logit": float, "score": float}
        logit: raw model output (for confidence derivation)
        score: sigmoid(logit), probability of fake (0=real, 1=fake)
    """
    import torch
    import librosa

    # Step 1: Base64 decode -> PCM int16 bytes (in-memory only)
    pcm_bytes = base64.b64decode(audio_pcm_base64)

    # Step 2: PCM int16 -> float32
    audio_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0

    # Step 3: Pad/truncate to 4 seconds
    if len(audio_float32) > MAX_SAMPLES:
        audio_float32 = audio_float32[:MAX_SAMPLES]
    elif len(audio_float32) < MAX_SAMPLES:
        audio_float32 = np.pad(audio_float32, (0, MAX_SAMPLES - len(audio_float32)))

    # Step 4: Compute 128-band log-mel spectrogram
    mel = librosa.feature.melspectrogram(
        y=audio_float32, sr=sample_rate,
        n_fft=N_FFT, hop_length=HOP_LENGTH, n_mels=N_MELS,
    )
    log_mel = librosa.power_to_db(mel, ref=np.max)
    mel_tensor = torch.FloatTensor(log_mel).unsqueeze(0).unsqueeze(0)

    # Step 5: Model forward pass
    with torch.no_grad():
        logit = model(mel_tensor)

    logit_val = logit.squeeze().item()
    score = torch.sigmoid(logit.squeeze()).item()

    # Audio data dereferenced here — pcm_bytes, audio_int16, audio_float32,
    # mel, log_mel, mel_tensor all go out of scope and are garbage collected.
    # No disk writes, no database storage, no log fields contain audio.

    return {"logit": logit_val, "score": score}
