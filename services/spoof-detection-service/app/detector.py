"""
Core spoof detection orchestrator.

Implements the full detection pipeline per DESIGN.md §4.3 and §4.4:
  1. Language/accent identification pre-pass (§4.4)
  2. Route to accent-cluster-specific or fallback model
  3. Run spoof-detection inference with timeout
  4. Build RiskSignal-shaped response with model version in detail

Design constraints upheld here:
  - Failed detection → available=false, never a low score
    (fusion.py design decision 4: "an unavailable signal is evidence
    of nothing, not evidence of safety")
  - Model version always in detail field (§4.3 shadow-mode requirement)
  - Cluster routing path always logged (§4.4 fairness reporting)
  - Confidence derived from model output, not hardcoded (see WARNING below)
  - No §4.6 pre-filter logic (belongs upstream per explicit scoping)

CONFIDENCE CALIBRATION WARNING:
  The confidence values produced by this service are derived from
  sigmoid distance-to-decision-boundary, which is a PROXY for true
  calibrated confidence. A Platt scaling or isotonic regression layer
  should be added once real evaluation data from the shadow-mode
  pipeline (§4.3) is available. See implementation_plan.md.
"""
import logging
import math
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Optional

from config import Settings
from language_id import LanguageIdentifier, LanguageIdResult
from model_registry import ModelRegistry, ModelRegistryEntry, DeepfakeModelRegistry
from schemas import SpoofDetectionRequest, SynthesisSignalResponse

logger = logging.getLogger(__name__)

# Thread pool for running model inference with a timeout.
# Sized small deliberately: the model itself is the bottleneck, and
# we don't want to queue up unbounded inference requests behind a
# slow/stuck model.
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="spoof-infer")

# Registry key prefix for spoof-detection models.
SPOOF_MODEL_PREFIX = "spoof-detector"


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid function."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    else:
        exp_x = math.exp(x)
        return exp_x / (1.0 + exp_x)


def _confidence_from_logit(logit: float) -> float:
    """
    Derive a confidence proxy from the model's raw logit.

    Uses sigmoid distance-to-decision-boundary:
      confidence = |sigmoid(logit) - 0.5| * 2.0

    Maps to:
      - 0.0 when the model is maximally uncertain (logit ≈ 0,
        sigmoid ≈ 0.5, right at the decision boundary)
      - 1.0 when the model is maximally certain (|logit| → ∞,
        sigmoid → 0 or 1)

    WARNING: This is a proxy, NOT true calibration. See module docstring.
    """
    return abs(_sigmoid(logit) - 0.5) * 2.0


class SpoofDetector:
    """
    Orchestrates spoof detection: language ID → model routing → inference.

    All detection results include the model version used, enabling the
    shadow-mode evaluation pipeline (§4.3) to compare scores across
    model versions without any code changes.
    """

    def __init__(
        self,
        registry: ModelRegistry,
        language_identifier: LanguageIdentifier,
        settings: Settings,
    ):
        self._registry = registry
        self._lang_id = language_identifier
        self._timeout_s = settings.inference_timeout_ms / 1000.0

        # Log startup state for operational visibility.
        generic = registry.get_model(f"{SPOOF_MODEL_PREFIX}/generic")
        if generic is None:
            logger.warning(
                "BLOCKING DEPENDENCY: No generic spoof-detection model "
                "registered (key='%s/generic'). All detections will "
                "return available=false until a model is registered.",
                SPOOF_MODEL_PREFIX,
            )
        else:
            logger.info(
                "Generic spoof-detection model loaded: version=%s",
                generic.version,
            )

        # Log which cluster-specific variants are available.
        available_models = registry.list_models(f"{SPOOF_MODEL_PREFIX}/")
        if available_models:
            logger.info(
                "Registered spoof-detection models: %s", available_models
            )
        else:
            logger.warning("No spoof-detection models registered at all.")

        # Explicit warning about confidence calibration status.
        logger.warning(
            "Confidence values are derived from sigmoid "
            "distance-to-decision-boundary (uncalibrated proxy). "
            "Upgrade to Platt scaling / isotonic regression once "
            "shadow-mode evaluation data is available (§4.3)."
        )

    def detect(self, request: SpoofDetectionRequest) -> SynthesisSignalResponse:
        """
        Run the full spoof-detection pipeline.

        Supports dual-path detection:
          - If audio_pcm_base64 is present AND the registry is a
            DeepfakeModelRegistry, use the trained model directly.
            Audio is decoded in-memory, used for inference, and
            immediately dereferenced (DESIGN.md section 7).
          - Otherwise, fall back to the heuristic path using
            pre-extracted audio_features.

        Returns a SynthesisSignalResponse matching the RiskSignal proto
        shape, suitable for direct use as the ``synthesis_signal`` input
        to risk-fusion-engine.
        """
        # Dual-path: prefer trained model when raw audio is available
        if (
            request.audio_pcm_base64 is not None
            and isinstance(self._registry, DeepfakeModelRegistry)
        ):
            return self._run_trained_inference(request)

        # Fallback: heuristic path using pre-extracted log-mel features
        lang_result = self._lang_id.identify(request.audio_features)
        model_entry, routing_path = self._resolve_model(lang_result)

        if model_entry is None:
            detail = (
                f"model=none, cluster={lang_result.cluster}, "
                f"path={routing_path}, reason=no model registered"
            )
            logger.warning(
                "Spoof detection unavailable: no model found. "
                "call_session_id=%s, %s",
                request.call_session_id, detail,
            )
            return SynthesisSignalResponse(
                score=0.0,
                confidence=0.0,
                available=False,
                detail=detail,
            )

        return self._run_inference(
            model_entry=model_entry,
            audio_features=request.audio_features,
            call_session_id=request.call_session_id,
            cluster=lang_result.cluster,
            routing_path=routing_path,
        )

    def _run_trained_inference(
        self, request: SpoofDetectionRequest
    ) -> SynthesisSignalResponse:
        """
        Run the trained deepfake model on raw PCM audio.

        Audio bytes are decoded in-memory, mel spectrogram computed,
        model inference run, and all audio data immediately dereferenced.
        No audio is persisted to disk, database, or logs (DESIGN.md section 7).
        """
        assert isinstance(self._registry, DeepfakeModelRegistry)
        trained_entry = self._registry.trained_entry
        version = trained_entry.version

        try:
            future = _executor.submit(
                trained_entry.model, request.audio_pcm_base64
            )
            result = future.result(timeout=self._timeout_s)

            logit = float(result["logit"])
            score = _sigmoid(logit)
            confidence = _confidence_from_logit(logit)

            score = max(0.0, min(1.0, score))
            confidence = max(0.0, min(1.0, confidence))

            detail = (
                f"model={version}, path=trained-model, "
                f"architecture=ResNet18+GRU+Attention"
            )

            logger.info(
                "Spoof detection (trained model): call_session_id=%s, "
                "score=%.4f, confidence=%.4f, %s",
                request.call_session_id, score, confidence, detail,
            )

            return SynthesisSignalResponse(
                score=score,
                confidence=confidence,
                available=True,
                detail=detail,
            )

        except FuturesTimeoutError:
            detail = (
                f"model={version}, path=trained-model, "
                f"reason=inference timeout ({self._timeout_s*1000:.0f}ms)"
            )
            logger.error(
                "Spoof detection TIMEOUT (trained): call_session_id=%s, %s",
                request.call_session_id, detail,
            )
            return SynthesisSignalResponse(
                score=0.0, confidence=0.0, available=False, detail=detail,
            )

        except Exception as exc:
            detail = (
                f"model={version}, path=trained-model, "
                f"reason=inference error: {exc}"
            )
            logger.error(
                "Spoof detection FAILED (trained): call_session_id=%s, %s",
                request.call_session_id, detail, exc_info=True,
            )
            return SynthesisSignalResponse(
                score=0.0, confidence=0.0, available=False, detail=detail,
            )

    def _resolve_model(
        self, lang_result: LanguageIdResult
    ) -> tuple[Optional[ModelRegistryEntry], str]:
        """
        Resolve the spoof-detection model based on language ID result.

        Tries cluster-specific first, falls back to generic.
        Returns (model_entry_or_None, routing_path_string).

        The routing path is logged and included in the detail field
        for per-cluster fairness reporting (§4.4).
        """
        cluster = lang_result.cluster

        if cluster != "generic":
            # Try cluster-specific model first.
            cluster_key = f"{SPOOF_MODEL_PREFIX}/{cluster}"
            entry = self._registry.get_model(cluster_key)
            if entry is not None:
                logger.info(
                    "Routing to cluster-specific model: key=%s, "
                    "version=%s, lang_id_confidence=%.3f",
                    cluster_key, entry.version, lang_result.confidence,
                )
                return entry, "cluster-specific"

            logger.info(
                "No cluster-specific model for '%s', falling back to "
                "generic. lang_id_confidence=%.3f",
                cluster, lang_result.confidence,
            )

        # Fall back to the generic (language-agnostic) model.
        generic_key = f"{SPOOF_MODEL_PREFIX}/generic"
        entry = self._registry.get_model(generic_key)
        if entry is not None:
            logger.info(
                "Using generic fallback model: key=%s, version=%s",
                generic_key, entry.version,
            )
            return entry, "fallback"

        return None, "no-model"

    def _run_inference(
        self,
        model_entry: ModelRegistryEntry,
        audio_features: list[float],
        call_session_id: str,
        cluster: str,
        routing_path: str,
    ) -> SynthesisSignalResponse:
        """
        Execute model inference with timeout protection.

        On any failure (timeout, exception, bad output), returns
        available=false. This is a hard requirement: a failed detection
        is NOT evidence of a clean call (fusion.py design decision 4).

        On success, derives score from sigmoid(logit) and confidence
        from the distance-to-decision-boundary proxy.
        """
        version = model_entry.version

        try:
            future = _executor.submit(model_entry.model, audio_features)
            result = future.result(timeout=self._timeout_s)

            # Expected model output:
            #   {"logit": float}  — preferred, allows proper confidence derivation
            #   {"score": float}  — acceptable, confidence derived from score distance
            if "logit" in result:
                logit = float(result["logit"])
                score = _sigmoid(logit)
                confidence = _confidence_from_logit(logit)
            elif "score" in result:
                score = float(result["score"])
                # Without a logit, we cannot compute true distance-to-boundary.
                # Use the score's own distance from 0.5 as a rough proxy.
                confidence = abs(score - 0.5) * 2.0
                logger.info(
                    "Model returned score without logit — confidence "
                    "derived from score distance to 0.5, not logit "
                    "magnitude. model_version=%s", version,
                )
            else:
                raise ValueError(
                    f"Model output missing both 'logit' and 'score' keys. "
                    f"Got keys: {list(result.keys())}"
                )

            # Clamp to [0, 1] for safety (should already be in range,
            # but defend against floating-point edge cases).
            score = max(0.0, min(1.0, score))
            confidence = max(0.0, min(1.0, confidence))

            detail = (
                f"model={version}, cluster={cluster}, path={routing_path}"
            )

            logger.info(
                "Spoof detection complete: call_session_id=%s, "
                "score=%.4f, confidence=%.4f, %s",
                call_session_id, score, confidence, detail,
            )

            return SynthesisSignalResponse(
                score=score,
                confidence=confidence,
                available=True,
                detail=detail,
            )

        except FuturesTimeoutError:
            detail = (
                f"model={version}, cluster={cluster}, path={routing_path}, "
                f"reason=inference timeout ({self._timeout_s*1000:.0f}ms)"
            )
            logger.error(
                "Spoof detection TIMEOUT: call_session_id=%s, %s",
                call_session_id, detail,
            )
            return SynthesisSignalResponse(
                score=0.0,
                confidence=0.0,
                available=False,
                detail=detail,
            )

        except Exception as exc:
            detail = (
                f"model={version}, cluster={cluster}, path={routing_path}, "
                f"reason=inference error: {exc}"
            )
            logger.error(
                "Spoof detection FAILED: call_session_id=%s, %s",
                call_session_id, detail,
                exc_info=True,
            )
            return SynthesisSignalResponse(
                score=0.0,
                confidence=0.0,
                available=False,
                detail=detail,
            )
