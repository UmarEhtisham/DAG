# app/graph/nodes/fallback.py
import logging
from datetime import datetime
from app.graph.state import PipelineState

logger = logging.getLogger(__name__)


def run_fallback(state: PipelineState) -> dict:
    """
    Fallback Node.
    Called when retrieval fails after all retries.
    Returns a partial report with error details instead of crashing.
    """
    profile = state["profile"]
    errors = state.get("errors", [])

    logger.warning(f"Fallback triggered for {profile['domain']}. Errors: {errors}")

    final_report = {
        "profile": {
            "name": profile["name"],
            "domain": profile["domain"]
        },
        "generated_at": datetime.utcnow().isoformat(),
        "status": "partial",
        "summary": {
            "total_queries_analyzed": 0,
            "visible_count": 0,
            "not_visible_count": 0,
            "average_opportunity_score": 0.0
        },
        "recommendations": [],
        "human_readable_summary": f"Pipeline encountered errors and could not complete fully. Please retry.",
        "errors": errors
    }

    return {
        "final_report": final_report,
        "insights": state.get("insights", []),
        "status": "partial",
        "errors": errors
    }