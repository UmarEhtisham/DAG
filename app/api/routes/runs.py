# app/api/routes/runs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.db.crud import get_profile, create_run, update_run, save_queries, save_recommendations
from app.api.schemas.run import RunResponse
from app.graph.build_graph import pipeline
from app.observability.logger import setup_logging

router = APIRouter()


@router.post("/profiles/{profile_uuid}/run", response_model=RunResponse)
def trigger_pipeline(profile_uuid: str, db: Session = Depends(get_db)):
    """
    Trigger the full DAG pipeline for a profile.
    Runs all agents in sequence and returns the final report.
    """
    setup_logging("INFO")

    # Get profile from DB
    profile = get_profile(db, profile_uuid)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Create a new run record in DB
    run = create_run(db, profile_uuid)

    # Build initial state for the pipeline
    state = {
        "profile": {
            "name": profile.name,
            "domain": profile.domain,
            "industry": profile.industry,
            "description": profile.description,
            "competitors": profile.competitors or []
        },
        "run_id": run.id,
        "planned_queries": [],
        "raw_results": [],
        "normalized_data": [],
        "insights": [],
        "final_report": {},
        "status": "running",
        "errors": [],
        "total_tokens_used": 0
    }

    # Run the pipeline
    result = pipeline.invoke(state)

    # Save queries to DB
    queries_to_save = []
    for insight in result.get("insights", []):
        queries_to_save.append({
            "run_id": run.id,
            "profile_id": profile_uuid,
            "query_text": insight["query"],
            "opportunity_score": insight["opportunity_score"],
            "domain_visible": insight["domain_in_serp"],
            "visibility_position": insight.get("serp_position"),
            "visibility_status": insight["visibility_status"],
            "estimated_search_volume": 0,
            "competitive_difficulty": 0
        })

    saved_queries = save_queries(db, queries_to_save)

    # Save recommendations to DB
    query_map = {q.query_text: q.id for q in saved_queries}
    recs_to_save = []
    for insight in result.get("insights", []):
        rec = insight.get("recommendation", {})
        recs_to_save.append({
            "run_id": run.id,
            "profile_id": profile_uuid,
            "query_id": query_map.get(insight["query"]),
            "content_type": rec.get("content_type", "blog_post"),
            "title": rec.get("title", ""),
            "rationale": rec.get("rationale", ""),
            "target_keywords": rec.get("target_keywords", []),
            "priority": rec.get("priority", "medium")
        })

    save_recommendations(db, recs_to_save)

    # Update run record in DB
    final_report = result.get("final_report", {})
    update_run(db, run.id, {
        "status": result["status"],
        "retrieval_calls_planned": len(result.get("planned_queries", [])),
        "records_extracted": len(result.get("normalized_data", [])),
        "report": final_report,
        "error_message": ", ".join(result.get("errors", [])) or None
    })

    # Top insights for response
    top_insights = sorted(
        result.get("insights", []),
        key=lambda x: x["opportunity_score"],
        reverse=True
    )[:3]

    return RunResponse(
        pipeline_run_uuid=run.id,
        profile_uuid=profile_uuid,
        status=result["status"],
        retrieval_calls_planned=len(result.get("planned_queries", [])),
        records_extracted=len(result.get("normalized_data", [])),
        top_insights=top_insights,
        final_report=final_report,
        total_tokens_used=result.get("total_tokens_used", 0),
        started_at=run.started_at,
        completed_at=datetime.utcnow()
    )