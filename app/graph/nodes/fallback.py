# app/graph/nodes/fallback.py
import logging
from datetime import datetime
from app.graph.state import PipelineState
from app.observability.logger import NodeLogger


def run_fallback(state: PipelineState) -> dict:
    node_log = NodeLogger("fallback", state["run_id"])
    node_log.start("Fallback triggered — pipeline encountered errors")

    profile = state["profile"]
    errors = state.get("errors", [])

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
        "human_readable_summary": "Pipeline encountered errors and could not complete fully. Please retry.",
        "errors": errors
    }

    node_log.failure(f"Fallback completed. Errors: {len(errors)}")

    return {
        "final_report": final_report,
        "insights": state.get("insights", []),
        "status": "partial",
        "errors": errors
    }