# app/graph/nodes/analyzer.py
import json
import re
import logging
from langchain_openai import ChatOpenAI
from app.config import settings
from app.graph.state import PipelineState

logger = logging.getLogger(__name__)


def _calculate_opportunity_score(record: dict) -> float:
    """
    Calculate opportunity score for a query (0.0 - 1.0).
    Higher score = more opportunity to improve visibility.
    """
    score = 0.0

    # Not visible in SERP = high opportunity
    if not record["domain_in_serp"]:
        score += 0.4
    elif record["serp_position"] and record["serp_position"] > 5:
        score += 0.2

    # Not in AI Overview = opportunity
    if not record["domain_in_ai_overview"]:
        score += 0.3

    # Not in LLM answers = opportunity
    if not record["domain_in_llm"]:
        score += 0.3

    return round(min(score, 1.0), 2)


def run_analyzer(state: PipelineState) -> dict:
    """
    Analysis / Synthesis Agent.
    Reasons over normalized data to produce insights and recommendations.
    """
    normalized_data = state["normalized_data"]
    profile = state["profile"]

    logger.info(f"Analyzer starting for {len(normalized_data)} records")

    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model="gpt-4o-mini",
        temperature=0
    )

    insights = []

    for record in normalized_data:
        opportunity_score = _calculate_opportunity_score(record)

        prompt = f"""
        You are a search visibility analyst.
        
        Brand: {profile['name']}
        Domain: {profile['domain']}
        Query: "{record['query']}"
        
        Visibility Data:
        - Found in Google Search: {record['domain_in_serp']} (position: {record['serp_position']})
        - Found in Google AI Overview: {record['domain_in_ai_overview']}
        - Found in LLM answers (ChatGPT/Gemini): {record['domain_in_llm']}
        
        Based on this data, suggest ONE content recommendation to improve visibility.
        
        Return ONLY a JSON object. No extra text.
        {{
            "content_type": "blog_post or landing_page or faq",
            "title": "suggested content title",
            "rationale": "why this content will help",
            "target_keywords": ["keyword1", "keyword2"],
            "priority": "high or medium or low"
        }}
        """

        response = llm.invoke(prompt)

        match = re.search(r'\{.*?\}', response.content, re.DOTALL)
        if not match:
            logger.error(f"Analyzer could not parse response for query: {record['query']}")
            continue

        recommendation = json.loads(match.group())

        insights.append({
            "query": record["query"],
            "opportunity_score": opportunity_score,
            "visibility_status": record["visibility_status"],
            "domain_in_serp": record["domain_in_serp"],
            "serp_position": record["serp_position"],
            "domain_in_ai_overview": record["domain_in_ai_overview"],
            "domain_in_llm": record["domain_in_llm"],
            "recommendation": recommendation
        })

        logger.info(f"Query '{record['query']}' — opportunity score: {opportunity_score}")

    logger.info(f"Analyzer completed. {len(insights)} insights generated.")

    return {
        "insights": insights,
        "status": "running",
        "errors": state.get("errors", [])
    }