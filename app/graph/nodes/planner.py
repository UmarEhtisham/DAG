# app/graph/nodes/planner.py
import json
import re
import logging
from langchain_openai import ChatOpenAI
from app.config import settings
from app.graph.state import PipelineState
from app.observability.logger import NodeLogger


def run_planner(state: PipelineState) -> dict:
    node_log = NodeLogger("planner", state["run_id"])
    node_log.start(f"Planner started for domain: {state['profile']['domain']}")

    profile = state["profile"]

    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model="gpt-4o-mini",
        temperature=0
    )

    prompt = f"""
    You are a search visibility analyst.
    
    A brand wants to understand how it appears in search and AI answers.
    
    Brand: {profile['name']}
    Domain: {profile['domain']}
    Industry: {profile['industry']}
    Description: {profile.get('description', '')}
    Competitors: {profile.get('competitors', [])}
    
    Generate 5 search queries that potential customers might use 
    when looking for this type of product or service.
    
    Return ONLY a JSON array of strings. No extra text, no explanation.
    Example: ["best SEO tool", "seo content optimizer", "surfer seo review"]
    """

    response = llm.invoke(prompt)

    match = re.search(r'\[.*?\]', response.content, re.DOTALL)
    if not match:
        node_log.failure("Planner failed to parse LLM response")
        return {
            "planned_queries": [],
            "status": "failed",
            "errors": state.get("errors", []) + ["Planner failed to generate queries"]
        }

    queries = json.loads(match.group())
    node_log.success(f"Planner generated {len(queries)} queries")

    return {
        "planned_queries": queries,
        "status": "running",
        "errors": state.get("errors", [])
    }