# tests/test_failure_retry.py
# Tests that the pipeline handles API failures gracefully
# and routes to the fallback node instead of crashing.

from unittest.mock import patch
from app.graph.build_graph import pipeline
from app.observability.logger import setup_logging

setup_logging("INFO")


def test_failure_and_fallback():
    """
    Simulate all DataForSEO tools failing.
    Pipeline should route to fallback node and return partial status.
    """

    # Force all tools to fail
    with patch("app.graph.nodes.retriever.get_serp_results") as mock_serp, \
         patch("app.graph.nodes.retriever.get_ai_overview") as mock_ai, \
         patch("app.graph.nodes.retriever.get_llm_visibility") as mock_llm:

        mock_serp.side_effect = Exception("Simulated SERP failure")
        mock_ai.side_effect = Exception("Simulated AI Overview failure")
        mock_llm.side_effect = Exception("Simulated LLM failure")

        state = {
            "profile": {
                "name": "Surfer SEO",
                "domain": "surferseo.com",
                "industry": "SEO Software",
                "description": "AI-powered SEO content optimization tool",
                "competitors": ["clearscope.io"]
            },
            "run_id": "test-failure-001",
            "planned_queries": ["best SEO tool"],
            "raw_results": [],
            "normalized_data": [],
            "insights": [],
            "final_report": {},
            "status": "running",
            "errors": [],
            "total_tokens_used": 0
        }

        result = pipeline.invoke(state)

        # Pipeline should not crash
        assert result is not None

        # Status should be partial — not completed
        assert result["status"] in ["partial", "failed"]

        # Errors should be recorded
        assert len(result["errors"]) > 0

        # Final report should still exist
        assert result["final_report"] is not None

        print("✅ Failure and fallback test passed")