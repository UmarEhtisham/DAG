# app/api/schemas/profile.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProfileCreateRequest(BaseModel):
    name: str
    domain: str
    industry: str
    description: Optional[str] = None
    competitors: list[str] = []


class ProfileCreateResponse(BaseModel):
    profile_uuid: str
    name: str
    domain: str
    status: str
    created_at: datetime


class ProfileGetResponse(BaseModel):
    profile_uuid: str
    name: str
    domain: str
    industry: str
    description: Optional[str]
    competitors: list[str]
    created_at: datetime
    total_runs: int
    last_run_status: Optional[str]