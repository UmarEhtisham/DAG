# app/graph/nodes/analyzer.py
import json
import re
import logging
from langchain_openai import ChatOpenAI
from app.config import settings
from app.graph.state import PipelineState
from app.observability.logger import NodeLogger


def _calculate_opportunity_score(record: dict) -> float:
    score = 0.0

    if not record["domain_in_serp"]:
        score += 0.4
    elif record["serp_position"] and record["serp_position"] > 5:
        score += 0.2

    if not record["domain_in_ai_overview"]:
        score += 0.3

    if not record["domain_in_llm"]:
        score += 0.3

    return round(min(score, 1.0), 2)


def run_analyzer(state: PipelineState) -> dict:
    node_log = NodeLogger("analyzer", state["run_id"])
    node_log.start(f"Analyzer starting for {len(state['normalized_data'])} records")

    normalized_data = state["normalized_data"]
    profile = state["profile"]
    errors = state.get("errors", [])

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
            errors.append(f"Analyzer failed to parse response for query: {record['query']}")
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

    node_log.success(f"Analyzer completed. {len(insights)} insights generated")

    return {
        "insights": insights,
        "status": "running",
        "errors": errors
    }