"""
AutoPR's FastAPI application — the single entrypoint every client
(Gradio, React, GitHub bot) will eventually call.
"""
import logging
from fastapi import FastAPI, HTTPException

from backend.api.schemas import AnalyzeRequest, AnalyzeResponse
from backend.agents.crew import run_full_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autopr.api")

app = FastAPI(
    title="AutoPR API",
    description="Multi-agent GitHub contribution assistant — scan, analyze, and draft PRs.",
    version="0.1.0",
)

@app.get("/")
def root():
    return {"message": "AutoPR API is running. Visit /docs to try it out."}

@app.get("/health")
def health_check():
    """Simple check to confirm the API is up — useful once this is deployed."""
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    logger.info("Received /analyze request for %s", request.repo_full_name)
    try:
        result = run_full_pipeline(request.repo_full_name, request.skills)
    except Exception as e:
        logger.exception("Pipeline crashed unexpectedly")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

    return AnalyzeResponse(**result)