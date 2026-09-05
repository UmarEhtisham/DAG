# app/graph/nodes/extractor.py
import logging
from app.graph.state import PipelineState
from app.observability.logger import NodeLogger


def run_extractor(state: PipelineState) -> dict:
    node_log = NodeLogger("extractor", state["run_id"])
    node_log.start(f"Extractor processing {len(state['raw_results'])} raw results")

    raw_results = state["raw_results"]
    domain = state["profile"]["domain"]
    normalized_data = []

    for item in raw_results:
        query = item["query"]
        serp = item.get("serp") or {}
        ai_overview = item.get("ai_overview") or {}
        llm_visibility = item.get("llm_visibility") or {}

        serp_position = None
        domain_in_serp = False
        for result in serp.get("results", []):
            if domain in result.get("domain", ""):
                domain_in_serp = True
                serp_position = result.get("position")
                break

        domain_in_ai_overview = ai_overview.get("domain_mentioned", False)
        domain_in_llm = llm_visibility.get("domain_mentioned", False)
        is_visible = domain_in_serp or domain_in_ai_overview or domain_in_llm
        visibility_status = "visible" if is_visible else "not_visible"

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

    node_log.success(f"Extractor completed. {len(normalized_data)} records normalized")

    return {
        "normalized_data": normalized_data,
        "status": "running",
        "errors": state.get("errors", [])
    }