import json
import re
import logging
from langchain_openai import ChatOpenAI
from app.config import settings
from app.graph.state import PipelineState

logger = logging.getLogger(__name__)


def run_planner(state: PipelineState) -> dict:
    """
    Query Planner Agent.
    Takes brand profile and generates search queries to check visibility.
    """
    profile = state["profile"]
    logger.info(f"Planner started for domain: {profile['domain']}")

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

    # Extract JSON array from response even if LLM adds extra text
    match = re.search(r'\[.*?\]', response.content, re.DOTALL)
    if not match:
        logger.error(f"Planner could not parse LLM response: {response.content}")
        return {
            "planned_queries": [],
            "status": "failed",
            "errors": state.get("errors", []) + ["Planner failed to generate queries"]
        }

    queries = json.loads(match.group())
    logger.info(f"Planner generated {len(queries)} queries: {queries}")

    return {
        "planned_queries": queries,
        "status": "running",
        "errors": state.get("errors", [])
    }