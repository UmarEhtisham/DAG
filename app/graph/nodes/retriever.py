# app/graph/nodes/retriever.py
import logging
from app.graph.state import PipelineState
from app.tools.dataforseo_serp import get_serp_results
from app.tools.dataforseo_ai_overview import get_ai_overview
from app.tools.dataforseo_llm_visibility import get_llm_visibility
from app.tools.base import RetryExhaustedError, PermanentError

logger = logging.getLogger(__name__)


def run_retriever(state: PipelineState) -> dict:
    """
    Retrieval Agent.
    For each planned query, calls all three DataForSEO tools
    and collects raw results.
    """
    queries = state["planned_queries"]
    domain = state["profile"]["domain"]
    raw_results = []
    errors = state.get("errors", [])

    logger.info(f"Retriever starting for {len(queries)} queries")

    for query in queries:
        logger.info(f"Fetching data for query: {query}")
        result = {
            "query": query,
            "serp": None,
            "ai_overview": None,
            "llm_visibility": None
        }

        # SERP results
        try:
            result["serp"] = get_serp_results(query, domain)
        except (RetryExhaustedError, PermanentError) as e:
            logger.error(f"SERP fetch failed for '{query}': {e}")
            errors.append(f"SERP failed for '{query}': {str(e)}")

        # AI Overview results
        try:
            result["ai_overview"] = get_ai_overview(query, domain)
        except (RetryExhaustedError, PermanentError) as e:
            logger.error(f"AI Overview fetch failed for '{query}': {e}")
            errors.append(f"AI Overview failed for '{query}': {str(e)}")

        # LLM Visibility results
        try:
            result["llm_visibility"] = get_llm_visibility(query, domain)
        except (RetryExhaustedError, PermanentError) as e:
            logger.error(f"LLM Visibility fetch failed for '{query}': {e}")
            errors.append(f"LLM Visibility failed for '{query}': {str(e)}")

        raw_results.append(result)

    # If all results failed — route to fallback
    all_failed = all(
        r["serp"] is None and r["ai_overview"] is None and r["llm_visibility"] is None
        for r in raw_results
    )

    if all_failed:
        logger.error("All retrieval calls failed — routing to fallback")
        return {
            "raw_results": raw_results,
            "status": "failed",
            "errors": errors
        }

    logger.info(f"Retriever completed. {len(raw_results)} results collected.")
    return {
        "raw_results": raw_results,
        "status": "running",
        "errors": errors
    }