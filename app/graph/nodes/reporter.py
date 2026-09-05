# app/graph/nodes/reporter.py
import logging
from datetime import datetime
from app.graph.state import PipelineState

logger = logging.getLogger(__name__)


def run_reporter(state: PipelineState) -> dict:
    """
    Report Agent.
    Assembles the final structured report from all agent outputs.
    No LLM call needed — pure assembly of existing data.
    """
    profile = state["profile"]
    insights = state["insights"]
    errors = state.get("errors", [])

    logger.info(f"Reporter assembling final report for {profile['domain']}")

    # Sort insights by opportunity score (highest first)
    sorted_insights = sorted(insights, key=lambda x: x["opportunity_score"], reverse=True)

    # Build recommendations list
    recommendations = []
    for item in sorted_insights:
        rec = item.get("recommendation", {})
        recommendations.append({
            "query": item["query"],
            "opportunity_score": item["opportunity_score"],
            "visibility_status": item["visibility_status"],
            "content_type": rec.get("content_type", "blog_post"),
            "title": rec.get("title", ""),
            "rationale": rec.get("rationale", ""),
            "target_keywords": rec.get("target_keywords", []),
            "priority": rec.get("priority", "medium")
        })

    # Build human readable summary
    visible_count = sum(1 for i in insights if i["visibility_status"] == "visible")
    not_visible_count = sum(1 for i in insights if i["visibility_status"] == "not_visible")
    avg_opportunity = round(
        sum(i["opportunity_score"] for i in insights) / len(insights), 2
    ) if insights else 0.0

    summary = f"""
Search Visibility Report for {profile['name']} ({profile['domain']})
Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

VISIBILITY SUMMARY:
- Total queries analyzed: {len(insights)}
- Queries where domain is visible: {visible_count}
- Queries where domain is not visible: {not_visible_count}
- Average opportunity score: {avg_opportunity}

TOP OPPORTUNITIES:
"""
    for i, rec in enumerate(recommendations[:3], 1):
        summary += f"""
{i}. Query: "{rec['query']}" (Opportunity Score: {rec['opportunity_score']})
   Content Suggestion: {rec['title']}
   Priority: {rec['priority']}
"""

    if errors:
        summary += f"\nWARNINGS:\n"
        for error in errors:
            summary += f"- {error}\n"

    # Final report
    final_report = {
        "profile": {
            "name": profile["name"],
            "domain": profile["domain"]
        },
        "generated_at": datetime.utcnow().isoformat(),
        "status": "partial" if errors else "completed",
        "summary": {
            "total_queries_analyzed": len(insights),
            "visible_count": visible_count,
            "not_visible_count": not_visible_count,
            "average_opportunity_score": avg_opportunity
        },
        "recommendations": recommendations,
        "human_readable_summary": summary.strip(),
        "errors": errors
    }

    logger.info(f"Reporter completed. Status: {final_report['status']}")

    return {
        "final_report": final_report,
        "status": final_report["status"],
        "errors": errors
    }