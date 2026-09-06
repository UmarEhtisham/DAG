# app/graph/nodes/retriever.py
import logging
from app.graph.state import PipelineState
from app.tools.dataforseo_serp import get_serp_results
from app.tools.dataforseo_ai_overview import get_ai_overview
from app.tools.dataforseo_llm_visibility import get_llm_visibility
from app.observability.logger import NodeLogger


def run_retriever(state: PipelineState) -> dict:
    node_log = NodeLogger("retriever", state["run_id"])
    node_log.start(f"Retriever starting for {len(state['planned_queries'])} queries")

    queries = state["planned_queries"]
    domain = state["profile"]["domain"]
    raw_results = []
    errors = state.get("errors", [])

    for query in queries:
        result = {
            "query": query,
            "serp": None,
            "ai_overview": None,
            "llm_visibility": None
        }

        try:
            result["serp"] = get_serp_results(query, domain)
        except Exception as e:
            errors.append(f"SERP failed for '{query}': {str(e)}")

        try:
            result["ai_overview"] = get_ai_overview(query, domain)
        except Exception as e:
            errors.append(f"AI Overview failed for '{query}': {str(e)}")

        try:
            result["llm_visibility"] = get_llm_visibility(query, domain)
        except Exception as e:
            errors.append(f"LLM Visibility failed for '{query}': {str(e)}")

        raw_results.append(result)

    all_failed = all(
        r["serp"] is None and r["ai_overview"] is None and r["llm_visibility"] is None
        for r in raw_results
    )

    if all_failed:
        node_log.failure("All retrieval calls failed — routing to fallback")
        return {
            "raw_results": raw_results,
            "status": "failed",
            "errors": errors
        }

    node_log.success(f"Retriever completed. {len(raw_results)} results collected")
    return {
        "raw_results": raw_results,
        "status": "running",
        "errors": errors
    }