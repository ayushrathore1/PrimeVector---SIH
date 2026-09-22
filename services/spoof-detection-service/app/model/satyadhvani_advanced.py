"""
SatyaDhVani-Advanced model definitions — multi-branch voice deepfake detector architectures.
Re-exports from dhwani_advanced for modularity and backwards compatibility.
"""
from model.dhwani_advanced import (
    ProsodyBranch,
    SSLBranch,
    FusionAttention,
    SatyaDhVaniAdvanced,
    DhwaniAdvanced,
    load_satyadhvani_advanced,
    load_dhwani_advanced,
)

__all__ = [
    "ProsodyBranch",
    "SSLBranch",
    "FusionAttention",
    "SatyaDhVaniAdvanced",
    "DhwaniAdvanced",
    "load_satyadhvani_advanced",
    "load_dhwani_advanced",
]
