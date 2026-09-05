# app/db/crud.py
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import Profile, PipelineRun, Query, Recommendation


# ── Profile ──────────────────────────────────────────

def create_profile(db: Session, data: dict) -> Profile:
    profile = Profile(**data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_profile(db: Session, profile_id: str) -> Profile | None:
    return db.query(Profile).filter(Profile.id == profile_id).first()


# ── Pipeline Run ──────────────────────────────────────

def create_run(db: Session, profile_id: str) -> PipelineRun:
    run = PipelineRun(profile_id=profile_id)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: str) -> PipelineRun | None:
    return db.query(PipelineRun).filter(PipelineRun.id == run_id).first()


def update_run(db: Session, run_id: str, data: dict) -> PipelineRun | None:
    run = get_run(db, run_id)
    if not run:
        return None
    for key, value in data.items():
        setattr(run, key, value)
    run.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(run)
    return run


# ── Queries ───────────────────────────────────────────

def save_queries(db: Session, queries: list[dict]) -> list[Query]:
    db_queries = [Query(**q) for q in queries]
    db.add_all(db_queries)
    db.commit()
    return db_queries


def get_queries(
    db: Session,
    profile_id: str,
    min_score: float = 0.0,
    status: str = None,
    page: int = 1,
    per_page: int = 20
) -> list[Query]:
    q = db.query(Query).filter(Query.profile_id == profile_id)

    if min_score:
        q = q.filter(Query.opportunity_score >= min_score)
    if status:
        q = q.filter(Query.visibility_status == status)

    offset = (page - 1) * per_page
    return q.order_by(Query.opportunity_score.desc()).offset(offset).limit(per_page).all()


def get_query_by_id(db: Session, query_id: str) -> Query | None:
    return db.query(Query).filter(Query.id == query_id).first()


# ── Recommendations ───────────────────────────────────

def save_recommendations(db: Session, recommendations: list[dict]) -> list[Recommendation]:
    db_recs = [Recommendation(**r) for r in recommendations]
    db.add_all(db_recs)
    db.commit()
    return db_recs


def get_recommendations(db: Session, profile_id: str) -> list[Recommendation]:
    return db.query(Recommendation).filter(Recommendation.profile_id == profile_id).all()