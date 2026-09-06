# tests/test_tool_validation.py
# Tests that tool argument validation works correctly.
# If required arguments are missing or wrong type, errors should be caught gracefully.

import pytest
from app.tools.dataforseo_serp import get_serp_results
from app.tools.dataforseo_ai_overview import get_ai_overview
from app.tools.dataforseo_llm_visibility import get_llm_visibility


def test_serp_tool_with_valid_arguments():
    """
    Test SERP tool returns correct structure with valid arguments.
    """
    result = get_serp_results("best SEO tool", "surferseo.com")

    assert result is not None
    assert "query" in result
    assert "domain" in result
    assert "results" in result
    assert result["query"] == "best SEO tool"
    assert result["domain"] == "surferseo.com"
    assert isinstance(result["results"], list)

    print("✅ SERP tool validation test passed")


def test_ai_overview_tool_with_valid_arguments():
    """
    Test AI Overview tool returns correct structure with valid arguments.
    """
    result = get_ai_overview("best SEO tool", "surferseo.com")

    assert result is not None
    assert "query" in result
    assert "domain" in result
    assert "domain_mentioned" in result
    assert isinstance(result["domain_mentioned"], bool)

    print("✅ AI Overview tool validation test passed")


def test_llm_visibility_tool_with_valid_arguments():
    """
    Test LLM Visibility tool returns correct structure with valid arguments.
    """
    result = get_llm_visibility("best SEO tool", "surferseo.com")

    assert result is not None
    assert "query" in result
    assert "domain" in result
    assert "domain_mentioned" in result
    assert "competitor_mentions" in result
    assert isinstance(result["competitor_mentions"], list)

    print("✅ LLM Visibility tool validation test passed")


def test_serp_tool_with_empty_query():
    """
    Test SERP tool handles empty query gracefully.
    """
    result = get_serp_results("", "surferseo.com")

    assert result is not None
    assert "results" in result

    print("✅ SERP tool empty query test passed")


def test_serp_tool_returns_domain_in_results():
    """
    Test that SERP mock data includes the requested domain in results.
    """
    result = get_serp_results("best SEO tool", "surferseo.com")

    domains_in_results = [r["domain"] for r in result["results"]]
    assert "surferseo.com" in domains_in_results

    print("✅ SERP tool domain presence test passed")