# app/api/routes/queries.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.crud import get_queries, get_query_by_id, get_profile
from app.api.schemas.query import QueryResponse
from app.graph.build_graph import pipeline
from app.observability.logger import setup_logging
from app.db.crud import save_queries, save_recommendations, create_run, update_run
from datetime import datetime

router = APIRouter()


@router.get("/profiles/{profile_uuid}/queries", response_model=list[QueryResponse])
def get_profile_queries(
    profile_uuid: str,
    min_score: float = Query(default=0.0),
    status: str = Query(default=None),
    page: int = Query(default=1),
    per_page: int = Query(default=20),
    db: Session = Depends(get_db)
):
    """
    Return all queries planned for a profile's most recent run.
    Sorted by opportunity score descending.
    Supports filtering by min_score and status.
    """
    profile = get_profile(db, profile_uuid)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    queries = get_queries(db, profile_uuid, min_score, status, page, per_page)

    return [
        QueryResponse(
            query_uuid=q.id,
            query_text=q.query_text,
            estimated_search_volume=q.estimated_search_volume,
            competitive_difficulty=q.competitive_difficulty,
            opportunity_score=q.opportunity_score,
            domain_visible=q.domain_visible,
            visibility_position=q.visibility_position,
            visibility_status=q.visibility_status,
            discovered_at=q.discovered_at
        )
        for q in queries
    ]

@router.post("/queries/{query_uuid}/recheck")
def recheck_query(query_uuid: str, db: Session = Depends(get_db)):
    
    query = get_query_by_id(db, query_uuid)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    profile = get_profile(db, query.profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    run = create_run(db, profile.id)

    state = {
        "profile": {
            "name": profile.name,
            "domain": profile.domain,
            "industry": profile.industry,
            "description": profile.description,
            "competitors": profile.competitors or []
        },
        "run_id": run.id,
        "planned_queries": [query.query_text],  # sirf ek query
        "raw_results": [],
        "normalized_data": [],
        "insights": [],
        "final_report": {},
        "status": "running",
        "errors": [],
        "total_tokens_used": 0
    }

    # Planner skip karo — seedha retriever se shuru karo
    from app.graph.nodes.retriever import run_retriever
    from app.graph.nodes.extractor import run_extractor
    from app.graph.nodes.analyzer import run_analyzer
    from app.graph.nodes.reporter import run_reporter

    state = {**state, **run_retriever(state)}
    state = {**state, **run_extractor(state)}
    state = {**state, **run_analyzer(state)}
    result = {**state, **run_reporter(state)}

    # DB mein save karo
    queries_to_save = []
    for insight in result.get("insights", []):
        queries_to_save.append({
            "run_id": run.id,
            "profile_id": profile.id,
            "query_text": insight["query"],
            "opportunity_score": insight["opportunity_score"],
            "domain_visible": insight["domain_in_serp"],
            "visibility_position": insight.get("serp_position"),
            "visibility_status": insight["visibility_status"],
            "estimated_search_volume": 0,
            "competitive_difficulty": 0
        })

    saved_queries = save_queries(db, queries_to_save)
    query_map = {q.query_text: q.id for q in saved_queries}

    recs_to_save = []
    for insight in result.get("insights", []):
        rec = insight.get("recommendation", {})
        recs_to_save.append({
            "run_id": run.id,
            "profile_id": profile.id,
            "query_id": query_map.get(insight["query"]),
            "content_type": rec.get("content_type", "blog_post"),
            "title": rec.get("title", ""),
            "rationale": rec.get("rationale", ""),
            "target_keywords": rec.get("target_keywords", []),
            "priority": rec.get("priority", "medium")
        })

    save_recommendations(db, recs_to_save)
    update_run(db, run.id, {
        "status": result["status"],
        "retrieval_calls_planned": 1,
        "records_extracted": len(result.get("normalized_data", [])),
        "report": result.get("final_report", {}),
        "error_message": ", ".join(result.get("errors", [])) or None
    })

    return {
        "query_uuid": query_uuid,
        "status": result["status"],
        "final_report": result.get("final_report", {})
    }

# @router.post("/queries/{query_uuid}/recheck")
# def recheck_query(query_uuid: str, db: Session = Depends(get_db)):
#     """
#     Re-run the pipeline for a single query.
#     Useful after publishing content to check if visibility improved.
#     """
#     setup_logging("INFO")

#     query = get_query_by_id(db, query_uuid)
#     if not query:
#         raise HTTPException(status_code=404, detail="Query not found")

#     profile = get_profile(db, query.profile_id)
#     if not profile:
#         raise HTTPException(status_code=404, detail="Profile not found")

#     run = create_run(db, profile.id)

#     state = {
#         "profile": {
#             "name": profile.name,
#             "domain": profile.domain,
#             "industry": profile.industry,
#             "description": profile.description,
#             "competitors": profile.competitors or []
#         },
#         "run_id": run.id,
#         "planned_queries": [query.query_text],
#         "raw_results": [],
#         "normalized_data": [],
#         "insights": [],
#         "final_report": {},
#         "status": "running",
#         "errors": [],
#         "total_tokens_used": 0
#     }

#     result = pipeline.invoke(state)

#     queries_to_save = []
#     for insight in result.get("insights", []):
#         queries_to_save.append({
#             "run_id": run.id,
#             "profile_id": profile.id,
#             "query_text": insight["query"],
#             "opportunity_score": insight["opportunity_score"],
#             "domain_visible": insight["domain_in_serp"],
#             "visibility_position": insight.get("serp_position"),
#             "visibility_status": insight["visibility_status"],
#             "estimated_search_volume": 0,
#             "competitive_difficulty": 0
#         })

#     saved_queries = save_queries(db, queries_to_save)

#     query_map = {q.query_text: q.id for q in saved_queries}
#     recs_to_save = []
#     for insight in result.get("insights", []):
#         rec = insight.get("recommendation", {})
#         recs_to_save.append({
#             "run_id": run.id,
#             "profile_id": profile.id,
#             "query_id": query_map.get(insight["query"]),
#             "content_type": rec.get("content_type", "blog_post"),
#             "title": rec.get("title", ""),
#             "rationale": rec.get("rationale", ""),
#             "target_keywords": rec.get("target_keywords", []),
#             "priority": rec.get("priority", "medium")
#         })

#     save_recommendations(db, recs_to_save)

#     update_run(db, run.id, {
#         "status": result["status"],
#         "retrieval_calls_planned": len(result.get("planned_queries", [])),
#         "records_extracted": len(result.get("normalized_data", [])),
#         "report": result.get("final_report", {}),
#         "error_message": ", ".join(result.get("errors", [])) or None
#     })

#     return {
#         "query_uuid": query_uuid,
#         "status": result["status"],
#         "final_report": result.get("final_report", {})
#     }