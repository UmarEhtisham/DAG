# app/api/routes/profiles.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.crud import create_profile, get_profile
from app.api.schemas.profile import ProfileCreateRequest, ProfileCreateResponse, ProfileGetResponse

router = APIRouter()


@router.post("/profiles", response_model=ProfileCreateResponse, status_code=201)
def register_profile(request: ProfileCreateRequest, db: Session = Depends(get_db)):
    """
    Register a new brand profile.
    This is the entry point before running the pipeline.
    """
    data = {
        "name": request.name,
        "domain": request.domain,
        "industry": request.industry,
        "description": request.description,
        "competitors": request.competitors
    }

    profile = create_profile(db, data)

    return ProfileCreateResponse(
        profile_uuid=profile.id,
        name=profile.name,
        domain=profile.domain,
        status="created",
        created_at=profile.created_at
    )


@router.get("/profiles/{profile_uuid}", response_model=ProfileGetResponse)
def get_profile_by_id(profile_uuid: str, db: Session = Depends(get_db)):
    """
    Retrieve a brand profile with summary stats.
    """
    profile = get_profile(db, profile_uuid)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    total_runs = len(profile.runs)
    last_run_status = profile.runs[-1].status if profile.runs else None

    return ProfileGetResponse(
        profile_uuid=profile.id,
        name=profile.name,
        domain=profile.domain,
        industry=profile.industry,
        description=profile.description,
        competitors=profile.competitors or [],
        created_at=profile.created_at,
        total_runs=total_runs,
        last_run_status=last_run_status
    )