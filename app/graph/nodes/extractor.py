# app/graph/nodes/extractor.py
import logging
from app.graph.state import PipelineState

logger = logging.getLogger(__name__)


def run_extractor(state: PipelineState) -> dict:
    """
    Extraction / Normalization Agent.
    Takes raw API results and converts them into a clean, structured format.
    No LLM call needed — pure data processing.
    """
    raw_results = state["raw_results"]
    domain = state["profile"]["domain"]
    normalized_data = []

    logger.info(f"Extractor processing {len(raw_results)} raw results")

    for item in raw_results:
        query = item["query"]
        serp = item.get("serp") or {}
        ai_overview = item.get("ai_overview") or {}
        llm_visibility = item.get("llm_visibility") or {}

        # Check SERP visibility
        serp_position = None
        domain_in_serp = False
        for result in serp.get("results", []):
            if domain in result.get("domain", ""):
                domain_in_serp = True
                serp_position = result.get("position")
                break

        # Check AI Overview visibility
        domain_in_ai_overview = ai_overview.get("domain_mentioned", False)

        # Check LLM visibility
        domain_in_llm = llm_visibility.get("domain_mentioned", False)

        # Overall visibility — visible if found in any source
        is_visible = domain_in_serp or domain_in_ai_overview or domain_in_llm

        # Determine visibility status
        if is_visible:
            visibility_status = "visible"
        else:
            visibility_status = "not_visible"

        normalized_data.append({
            "query": query,
            "domain": domain,
            "domain_in_serp": domain_in_serp,
            "serp_position": serp_position,
            "domain_in_ai_overview": domain_in_ai_overview,
            "domain_in_llm": domain_in_llm,
            "is_visible": is_visible,
            "visibility_status": visibility_status,
        })

        logger.info(f"Query '{query}' — visible: {is_visible}, serp position: {serp_position}")

    logger.info(f"Extractor completed. {len(normalized_data)} records normalized.")

    return {
        "normalized_data": normalized_data,
        "status": "running",
        "errors": state.get("errors", [])
    }