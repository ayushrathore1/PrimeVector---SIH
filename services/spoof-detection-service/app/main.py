"""
Spoof Detection Service — FastAPI application.

Scores audio features for likelihood of AI-synthesized/cloned speech.
Consumes output from feature-extraction-service, produces the
``synthesis_signal`` input to risk-fusion-engine (matching the RiskSignal
proto shape exactly).

This is service boilerplate (DESIGN.md §6: "delegated to AI coding tools,
lightly reviewed"). The detection logic it wraps (detector.py) contains
the important design decisions.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from detector import SpoofDetector
from language_id import LanguageIdentifier
from model_registry import ModelRegistry, StubModelRegistry, DeepfakeModelRegistry
from schemas import SpoofDetectionRequest, SynthesisSignalResponse

# Configure structured logging.
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def _create_registry() -> ModelRegistry:
    """
    Factory for the ModelRegistry backend.

    Backends:
      - "deepfake": Trained ResNet18+GRU+Attention deepfake detector
        (koyelog/deepfake-voice-detector-sota). Production default.
      - "heuristic": Log-mel heuristic scorer v4.0. Cannot distinguish
        real voice from modern TTS. Fallback only.
      - "stub": No model registered. All requests return available=false.

    If the deepfake backend is requested but model download fails
    (e.g. network issues pulling from HuggingFace), falls back to
    heuristic so the service can still start and respond with
    degraded-but-alive signals instead of crashing entirely.
    """
    backend = settings.model_registry_backend
    if backend == "deepfake":
        try:
            return DeepfakeModelRegistry()
        except Exception as e:
            logger.warning(
                "Failed to initialize deepfake model registry (%s). "
                "Falling back to heuristic backend so the service can "
                "start. Spoof detection will use acoustic heuristics "
                "until the model is available.",
                e,
            )
            return StubModelRegistry(enable_heuristic=True)
    elif backend == "heuristic":
        return StubModelRegistry(enable_heuristic=True)
    elif backend == "stub":
        return StubModelRegistry(enable_heuristic=False)
    else:
        raise ValueError(
            f"Unknown model_registry_backend='{backend}'. "
            f"Available: 'deepfake', 'heuristic', 'stub'."
        )


# Module-level references, populated at startup.
_registry: ModelRegistry | None = None
_detector: SpoofDetector | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize model registry and detector."""
    global _registry, _detector

    logger.info(
        "Starting spoof-detection-service with config: "
        "registry_backend=%s, inference_timeout_ms=%d, "
        "default_accent_cluster=%s",
        settings.model_registry_backend,
        settings.inference_timeout_ms,
        settings.default_accent_cluster,
    )

    _registry = _create_registry()
    lang_id = LanguageIdentifier(
        registry=_registry,
        default_cluster=settings.default_accent_cluster,
    )
    _detector = SpoofDetector(
        registry=_registry,
        language_identifier=lang_id,
        settings=settings,
    )

    logger.info("spoof-detection-service ready.")
    yield
    logger.info("spoof-detection-service shutting down.")


app = FastAPI(
    title="spoof-detection-service",
    version="0.1.0",
    description=(
        "Scores audio features for likelihood of AI-synthesized/cloned "
        "speech. Produces the synthesis_signal input to risk-fusion-engine."
    ),
    lifespan=lifespan,
)


@app.post("/v1/detect", response_model=SynthesisSignalResponse)
def detect(req: SpoofDetectionRequest) -> SynthesisSignalResponse:
    """
    Run spoof detection on extracted audio features.

    Returns a SynthesisSignalResponse matching the RiskSignal proto
    shape (score, confidence, available, detail). If detection fails
    or no model is registered, ``available=false`` is returned — a
    failed detection is NOT evidence of a clean call (fusion.py
    design decision 4).
    """
    return _detector.detect(req)


@app.get("/healthz")
def healthz():
    """
    Liveness probe.

    Reports whether a spoof-detection model is registered, but does
    NOT fail the health check if no model is loaded — the service
    correctly returns ``available=false`` on requests when no model
    exists, which is valid fail-safe behavior. Model availability is
    a readiness concern, not a liveness concern.
    """
    has_model = False
    if _registry is not None:
        models = _registry.list_models("spoof-detector/")
        has_model = len(models) > 0

    return {
        "status": "ok",
        "model_registered": has_model,
        "registry_backend": settings.model_registry_backend,
    }
