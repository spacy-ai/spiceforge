from __future__ import annotations

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from synthesizer.synthesizer import SpecialistSynthesizer, SynthesisResult

logger = logging.getLogger(__name__)

app = FastAPI(title="SPACY Specialist Synthesizer")


class SynthesisRequest(BaseModel):
    blueprint: dict
    api_key: str | None = None
    api_base: str | None = None
    model: str | None = None


class SynthesisResponse(BaseModel):
    success: bool
    python_code: str
    netlist: str
    metadata: dict | None = None
    error: str | None = None


@app.get("/")
def root():
    return {"service": "Specialist Synthesizer", "status": "ready"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/synthesize", response_model=SynthesisResponse)
def synthesize(request: SynthesisRequest):
    try:
        synthesizer = SpecialistSynthesizer(
            api_key=request.api_key,
            api_base=request.api_base,
            model=request.model,
        )
        result = synthesizer.synthesize(request.blueprint)
        return SynthesisResponse(
            success=True,
            python_code=result.python_code,
            netlist=result.netlist or "",
            metadata=result.synthesis_metadata,
        )
    except Exception as exc:
        logger.error("Synthesis failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
