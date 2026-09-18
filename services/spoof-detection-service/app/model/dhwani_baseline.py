"""
Dhwani model definitions — voice deepfake detector architectures.

Contains both v1 (DhwaniBaseline) and v2 (DhwaniV2) architectures.

v1 — DhwaniBaseline:
  Audio → 16kHz → 80-band Log-Mel (1ch) → 4-block CNN → Global Avg Pool → MLP → logit
  Parameters: ~1.2M

v2 — DhwaniV2:
  Audio → 16kHz → 3-channel (Log-Mel + Δ + Δ²) → ResNet-SE + BiGRU + MHA → MLP → logit
  Parameters: ~6M

Design decisions:
  - 80-band Log-Mel matches PrimeVector feature-extraction-service parameters
    (n_mels=80, n_fft=2048, hop_length=160, win_length=400)
  - v2 adds delta and delta-delta features to capture temporal dynamics
    that expose AI-generated speech artifacts.
  - Output is a raw logit (not sigmoid). The existing detector.py handles
    sigmoid conversion and confidence derivation.
  - Both models target <50ms inference per 3-second chunk on CPU.

Trained on Google Colab, checkpoint loaded locally for inference.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# Shared building blocks
# ============================================================

class ConvBlock(nn.Module):
    """Conv2d → BatchNorm → ReLU → MaxPool block (used by v1)."""

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3):
        super().__init__()
        self.conv = nn.Conv2d(
            in_channels, out_channels, kernel_size,
            padding=kernel_size // 2, bias=False,
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.pool = nn.MaxPool2d(2, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.pool(F.relu(self.bn(self.conv(x))))


# ============================================================
# v1: DhwaniBaseline (backward compatible)
# ============================================================

class DhwaniBaseline(nn.Module):
    """
    v1: 4-block CNN for voice deepfake detection on 80-band Log-Mel.

    Input:  (batch, 1, n_mels=80, time_frames)
    Output: (batch, 1) — raw logit, higher = more likely synthetic

    Parameters: ~1.2M (lightweight for CPU inference)
    """

    def __init__(self, n_mels: int = 80):
        super().__init__()
        self.n_mels = n_mels

        # 4 convolutional blocks: 1→32→64→128→256
        self.conv_blocks = nn.Sequential(
            ConvBlock(1, 32, kernel_size=3),
            ConvBlock(32, 64, kernel_size=3),
            ConvBlock(64, 128, kernel_size=3),
            ConvBlock(128, 256, kernel_size=3),
        )

        # Global average pooling collapses spatial dims → (batch, 256)
        self.global_pool = nn.AdaptiveAvgPool2d(1)

        # MLP classifier: 256 → 128 → 1
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv_blocks(x)
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


# ============================================================
# v2: DhwaniV2 — ResNet-SE + BiGRU + Multi-Head Attention
# ============================================================

class SEBlock(nn.Module):
    """Squeeze-and-Excitation: learns channel attention weights.
    Helps the model learn WHICH frequency bands matter per sample."""

    def __init__(self, channels: int, reduction: int = 16):
        super().__init__()
        reduced = max(channels // reduction, 4)
        self.fc = nn.Sequential(
            nn.Linear(channels, reduced, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(reduced, channels, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, _, _ = x.size()
        w = x.mean(dim=[2, 3])
        w = self.fc(w).view(b, c, 1, 1)
        return x * w


class ResBlock(nn.Module):
    """ResNet BasicBlock with SE attention and residual connection."""

    def __init__(self, in_ch: int, out_ch: int, stride: int = 1, use_se: bool = True):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_ch)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_ch != out_ch:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 1, stride=stride, bias=False),
                nn.BatchNorm2d(out_ch),
            )
        self.se = SEBlock(out_ch) if use_se else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = self.se(out)
        out += self.shortcut(x)
        return F.relu(out)


class DhwaniV2(nn.Module):
    """
    v2: ResNet-SE + BiGRU + Multi-Head Attention deepfake detector.

    Input:  (batch, 3, 80, T) — 3-channel Log-Mel + Delta + Delta²
    Output: (batch, 1) raw logit

    Parameters: ~6M, <50ms inference per 3s chunk on CPU.
    """

    def __init__(self, n_channels: int = 3, n_mels: int = 80):
        super().__init__()
        self.n_channels = n_channels
        self.n_mels = n_mels

        # Stem
        self.stem = nn.Sequential(
            nn.Conv2d(n_channels, 64, 7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(3, stride=2, padding=1),
        )

        # ResNet blocks with SE attention
        self.layer1 = nn.Sequential(ResBlock(64, 64), ResBlock(64, 64))
        self.layer2 = nn.Sequential(ResBlock(64, 128, stride=2), ResBlock(128, 128))
        self.layer3 = nn.Sequential(ResBlock(128, 256, stride=2), ResBlock(256, 256))

        # Temporal modeling: BiGRU
        self.gru = nn.GRU(
            input_size=256, hidden_size=256,
            num_layers=2, batch_first=True,
            bidirectional=True, dropout=0.3,
        )

        # Multi-Head Attention
        self.attention = nn.MultiheadAttention(
            embed_dim=512, num_heads=8,
            batch_first=True, dropout=0.1,
        )

        # Classifier head
        self.classifier = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(256),
            nn.Dropout(0.4),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stem(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)

        # Pool over frequency → (B, 256, T')
        x = x.mean(dim=2)
        # → (B, T', 256)
        x = x.permute(0, 2, 1)

        # BiGRU → (B, T', 512)
        gru_out, _ = self.gru(x)

        # Multi-Head Attention → (B, T', 512)
        attn_out, _ = self.attention(gru_out, gru_out, gru_out)

        # Mean pool over time → (B, 512)
        pooled = attn_out.mean(dim=1)

        return self.classifier(pooled)


# ============================================================
# Loaders
# ============================================================

def load_dhwani_baseline(checkpoint_path: str, device: str = "cpu"):
    """
    Load a trained Dhwani model from a checkpoint file.
    Auto-detects v1 (DhwaniBaseline) vs v2 (DhwaniV2) from checkpoint config.

    Returns:
        model: nn.Module in eval mode
        version: str identifying the model version
        metrics: dict of training metrics (if available)
        param_count: int
        mem_mb: float
    """
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    config = checkpoint.get("config", {})
    architecture = config.get("architecture", "")

    # v2 detection: check for v2-specific config fields
    if "DhwaniV2" in architecture or config.get("n_channels", 1) == 3:
        model = DhwaniV2(
            n_channels=config.get("n_channels", 3),
            n_mels=config.get("n_mels", 80),
        )
    else:
        model = DhwaniBaseline(
            n_mels=config.get("n_mels", 80),
        )

    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()

    version = checkpoint.get("version", "Dhwani-unknown")
    metrics = checkpoint.get("metrics", {})

    param_count = sum(p.numel() for p in model.parameters())
    mem_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 * 1024)

    return model, version, metrics, param_count, mem_mb
