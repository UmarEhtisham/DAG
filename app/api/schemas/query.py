# app/api/schemas/query.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class QueryResponse(BaseModel):
    query_uuid: str
    query_text: str
    estimated_search_volume: int
    competitive_difficulty: int
    opportunity_score: float
    domain_visible: bool
    visibility_position: Optional[int]
    visibility_status: str
    discovered_at: datetime


class RecommendationResponse(BaseModel):
    recommendation_uuid: str
    target_query_uuid: Optional[str]
    content_type: str
    title: str
    rationale: str
    target_keywords: list[str]
    priority: str