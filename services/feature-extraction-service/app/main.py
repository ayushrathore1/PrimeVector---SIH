from fastapi import FastAPI, HTTPException
from app.models import ExtractionRequest, ExtractionResponse
from app.extraction import extract_features
from app.model_registry import StubModelRegistry

app = FastAPI(title="Feature Extraction Service")
model_registry = StubModelRegistry()

@app.post("/v1/extract", response_model=ExtractionResponse)
def extract_endpoint(request: ExtractionRequest):
    try:
        response = extract_features(request, model_registry)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
