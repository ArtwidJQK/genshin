from typing import Any, Dict
from fastapi import FastAPI

app = FastAPI(
    title="Gacha & Artifact RNG Simulator",
    description="Probabilistic game simulation engine foundation",
    version="0.1.0",
)


@app.get("/health")
def health() -> Dict[str, Any]:
    """Health check endpoint to verify backend service readiness."""
    return {"status": "ok"}
