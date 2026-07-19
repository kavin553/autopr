"""
Request/response models for the API — defines exactly what a client
sends and receives, and gives FastAPI automatic validation + docs.
"""
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    repo_full_name: str   # e.g. "gradio-app/gradio"
    skills: list[str]     # e.g. ["Python", "FastAPI", "Gradio"]


class AnalyzeResponse(BaseModel):
    scan_result: str
    top_issue_number: int | None
    change_plan: str | None
    pr_draft: str | None
    error: str | None