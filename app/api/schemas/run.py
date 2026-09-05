# app/api/schemas/run.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RunResponse(BaseModel):
    pipeline_run_uuid: str
    profile_uuid: str
    status: str
    retrieval_calls_planned: int
    records_extracted: int
    top_insights: list[dict]
    final_report: dict
    total_tokens_used: int
    started_at: datetime
    completed_at: Optional[datetime]