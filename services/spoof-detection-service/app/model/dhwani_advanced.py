"""
Dhwani-Advanced: Multi-branch voice deepfake detector.

Architecture:
                       AUDIO
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      Log-Mel         Prosody       SSL Embedding
       Branch          Branch          Branch
          │              │              │
         CNN          BiGRU/MLP       Frozen
          │              │          (WavLM/wav2vec2)
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                   Feature Fusion
                    (Attention)
                         │
                         ▼
                       MLP
                         │
                         ▼
               Raw logit (synthetic)

Design decisions:
  - Log-Mel branch: same CNN as DhwaniBaseline (shared architecture)
  - Prosody branch: uses features from PrimeVector feature-extraction
    (F0, pitch, jitter, shimmer, etc.). Treated as ONE evidence source
    among several — NOT assumed to be a reliable standalone classifier.
  - SSL branch: frozen WavLM/wav2vec2 embeddings. NOT fine-tuned on
    laptop due to memory constraints. The SSL model provides pre-trained
    representations that capture subtle acoustic patterns.
  - Fusion: concatenation + learned attention weights
  - The model is language-AGNOSTIC by default. Language-specific routing
    is handled by the existing language_id.py, not inside Dhwani.
  - Speaker embeddings are NOT used for fake/real classification.
    They are only for speaker consistency (handled separately by
    enrollment-service).

Output: raw logit, consumed by detector.py's existing inference path.

Trained on Google Colab, checkpoint loaded locally for inference.
"""
from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from model.dhwani_baseline import ConvBlock


class ProsodyBranch(nn.Module):
    """
    Process prosody features (F0, pitch, jitter, shimmer, etc.).

    Prosody is treated as ONE evidence source — the model does NOT
    hard-code assumptions like "AI voices always have low pitch variance."
    That is too simplistic for modern TTS systems.

    Input:  (batch, seq_len, prosody_dim) or (batch, prosody_dim)
    Output: (batch, 64) feature vector
    """

    def __init__(self, input_dim: int = 10, hidden_dim: int = 64):
        super().__init__()
        self.has_sequence = None  # determined at forward time

        # For sequential prosody features (frame-level)
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )
        self.gru_proj = nn.Linear(hidden_dim * 2, hidden_dim)

        # For summary prosody features (utterance-level)
        self.summary_mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 3:
            # Sequential: (batch, seq_len, prosody_dim)
            gru_out, _ = self.gru(x)
            # Mean pool over time
            pooled = gru_out.mean(dim=1)
            return self.gru_proj(pooled)
        else:
            # Summary: (batch, prosody_dim)
            return self.summary_mlp(x)


class SSLBranch(nn.Module):
    """
    Process frozen SSL embeddings (WavLM, wav2vec2, HuBERT).

    The SSL encoder is NOT loaded here — embeddings are pre-extracted
    on Colab and passed as input. This avoids loading a 300M+ parameter
    model on the laptop for inference.

    Input:  (batch, ssl_dim) — pre-extracted SSL embedding
    Output: (batch, 128) feature vector
    """

    def __init__(self, input_dim: int = 768, output_dim: int = 128):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.2),
            nn.Linear(256, output_dim),
            nn.ReLU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.proj(x)


class FusionAttention(nn.Module):
    """
    Learned attention-based fusion of multi-branch features.

    Computes attention weights for each branch's contribution,
    rather than naive concatenation, so the model can learn which
    branches are most informative for each sample.

    Input: list of (batch, feature_dim) tensors
    Output: (batch, total_feature_dim) weighted-concatenated features
    """

    def __init__(self, feature_dims: list[int]):
        super().__init__()
        self.total_dim = sum(feature_dims)
        self.n_branches = len(feature_dims)

        # Per-branch attention score
        self.attention = nn.Sequential(
            nn.Linear(self.total_dim, self.n_branches),
        )

    def forward(self, branch_features: list[torch.Tensor]) -> torch.Tensor:
        if len(branch_features) == 1:
            return branch_features[0]

        # Concatenate all branch features
        concat = torch.cat(branch_features, dim=1)
        if concat.size(1) != self.total_dim:
            return concat

        # Compute attention weights
        attn_logits = self.attention(concat)
        attn_weights = F.softmax(attn_logits, dim=1)

        # Weight each branch's features
        weighted_parts = []
        for i, feat in enumerate(branch_features):
            weight = attn_weights[:, i:i+1]  # (batch, 1)
            weighted_parts.append(feat * weight)

        return torch.cat(weighted_parts, dim=1)


class DhwaniAdvanced(nn.Module):
    """
    Multi-branch voice deepfake detector with Log-Mel + Prosody + SSL.

    Input:
        mel:     (batch, 1, 80, T) Log-Mel spectrogram
        prosody: (batch, prosody_dim) or (batch, T, prosody_dim)  [optional]
        ssl:     (batch, ssl_dim)  [optional, pre-extracted embeddings]

    Output: (batch, 1) raw logit

    The model degrades gracefully when optional branches are absent:
    - mel only → uses CNN branch only (equivalent to DhwaniBaseline)
    - mel + prosody → uses CNN + prosody branches
    - mel + prosody + ssl → full multi-branch fusion
    """

    def __init__(
        self,
        n_mels: int = 80,
        prosody_dim: int = 10,
        ssl_dim: int = 768,
        use_prosody: bool = True,
        use_ssl: bool = True,
    ):
        super().__init__()
        self.use_prosody = use_prosody
        self.use_ssl = use_ssl

        # Branch 1: Log-Mel CNN (always active)
        self.mel_branch = nn.Sequential(
            ConvBlock(1, 32, kernel_size=3),
            ConvBlock(32, 64, kernel_size=3),
            ConvBlock(64, 128, kernel_size=3),
            ConvBlock(128, 256, kernel_size=3),
        )
        self.mel_pool = nn.AdaptiveAvgPool2d(1)
        mel_out_dim = 256

        # Branch 2: Prosody (optional)
        prosody_out_dim = 64
        if use_prosody:
            self.prosody_branch = ProsodyBranch(
                input_dim=prosody_dim, hidden_dim=prosody_out_dim,
            )

        # Branch 3: SSL embeddings (optional)
        ssl_out_dim = 128
        if use_ssl:
            self.ssl_branch = SSLBranch(
                input_dim=ssl_dim, output_dim=ssl_out_dim,
            )

        # Fusion
        branch_dims = [mel_out_dim]
        if use_prosody:
            branch_dims.append(prosody_out_dim)
        if use_ssl:
            branch_dims.append(ssl_out_dim)

        self.fusion = FusionAttention(branch_dims)
        fusion_out_dim = sum(branch_dims)

        # Classifier
        self.classifier = nn.Sequential(
            nn.Linear(fusion_out_dim, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.4),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
        )

    def forward(
        self,
        mel: torch.Tensor,
        prosody: Optional[torch.Tensor] = None,
        ssl: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass with graceful degradation for missing branches.

        Args:
            mel:     (batch, 1, 80, T) Log-Mel spectrogram [required]
            prosody: (batch, prosody_dim) prosody features  [optional]
            ssl:     (batch, ssl_dim) SSL embeddings        [optional]

        Returns:
            (batch, 1) raw logit
        """
        # Branch 1: Log-Mel CNN
        mel_feat = self.mel_branch(mel)
        mel_feat = self.mel_pool(mel_feat).view(mel_feat.size(0), -1)

        branch_outputs = [mel_feat]

        # Branch 2: Prosody
        if self.use_prosody:
            if prosody is not None:
                prosody_feat = self.prosody_branch(prosody)
            else:
                prosody_feat = torch.zeros(mel.size(0), 64, device=mel.device)
            branch_outputs.append(prosody_feat)

        # Branch 3: SSL
        if self.use_ssl:
            if ssl is not None:
                ssl_feat = self.ssl_branch(ssl)
            else:
                ssl_feat = torch.zeros(mel.size(0), 128, device=mel.device)
            branch_outputs.append(ssl_feat)

        # Fusion + classification
        fused = self.fusion(branch_outputs)
        return self.classifier(fused)


def load_dhwani_advanced(checkpoint_path: str, device: str = "cpu"):
    """
    Load a trained Dhwani-Advanced model from a checkpoint file.

    Returns:
        model: DhwaniAdvanced in eval mode
        version: str
        metrics: dict
    """
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

    config = checkpoint.get("config", {})
    model = DhwaniAdvanced(
        n_mels=config.get("n_mels", 80),
        prosody_dim=config.get("prosody_dim", 10),
        ssl_dim=config.get("ssl_dim", 768),
        use_prosody=config.get("use_prosody", True),
        use_ssl=config.get("use_ssl", True),
    )
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()

    version = checkpoint.get("version", "Dhwani-Advanced-unknown")
    metrics = checkpoint.get("metrics", {})

    return model, version, metrics
