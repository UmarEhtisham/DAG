# tests/test_happy_path.py
# Tests the full pipeline run from start to finish with mock data.

from app.graph.build_graph import pipeline
from app.observability.logger import setup_logging

setup_logging("INFO")


def test_happy_path():
    """
    Test that the full pipeline runs successfully with mock data.
    Planner → Retriever → Extractor → Analyzer → Reporter
    """
    state = {
        "profile": {
            "name": "Surfer SEO",
            "domain": "surferseo.com",
            "industry": "SEO Software",
            "description": "AI-powered SEO content optimization tool",
            "competitors": ["clearscope.io", "marketmuse.com"]
        },
        "run_id": "test-happy-path-001",
        "planned_queries": [],
        "raw_results": [],
        "normalized_data": [],
        "insights": [],
        "final_report": {},
        "status": "running",
        "errors": [],
        "total_tokens_used": 0
    }

    result = pipeline.invoke(state)

    # Pipeline should complete successfully
    assert result["status"] == "completed"

    # Planner should generate queries
    assert len(result["planned_queries"]) > 0

    # Retriever should fetch results
    assert len(result["raw_results"]) > 0

    # Extractor should normalize data
    assert len(result["normalized_data"]) > 0

    # Analyzer should generate insights
    assert len(result["insights"]) > 0

    # Reporter should generate final report
    assert result["final_report"]["status"] == "completed"
    assert "human_readable_summary" in result["final_report"]

    print("✅ Happy path test passed")