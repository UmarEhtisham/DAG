# app/tools/dataforseo_serp.py
import requests
from app.config import settings
from app.tools.base import call_with_retry, PermanentError


def _mock_response(query: str, domain: str) -> dict:
    return {
        "query": query,
        "domain": domain,
        "results": [
            {"position": 1, "domain": "competitor1.com", "title": f"Best SEO Tools 2024"},
            {"position": 2, "domain": "competitor2.com", "title": f"Top SEO Software Review"},
            {"position": 5, "domain": "competitor3.com", "title": f"SEO Content Tools Compared"},
            {"position": 8, "domain": domain, "title": f"{domain} - SEO Optimization Tool"},
        ],
        "source": "mock"
    }


def _live_response(query: str, domain: str) -> dict:
    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    
    auth = (settings.dataforseo_login, settings.dataforseo_password)
    
    payload = [{
        "keyword": query,
        "location_code": 2840,  # United States
        "language_code": "en",
        "device": "desktop",
        "depth": 10
    }]

    response = requests.post(
        url,
        json=payload,
        auth=auth,
        timeout=settings.api_timeout_seconds
    )

    if response.status_code == 401:
        raise PermanentError("Invalid DataForSEO credentials")

    if response.status_code == 400:
        raise PermanentError(f"Bad request: {response.text}")

    response.raise_for_status()
    
    data = response.json()
    items = data["tasks"][0]["result"][0]["items"]

    results = []
    for item in items:
        if item.get("type") == "organic":
            results.append({
                "position": item.get("rank_absolute"),
                "domain": item.get("domain"),
                "title": item.get("title")
            })

    return {
        "query": query,
        "domain": domain,
        "results": results,
        "source": "live"
    }


def get_serp_results(query: str, domain: str) -> dict:
    """
    Fetches Google SERP results for a given query.
    Uses mock data by default — set DATAFORSEO_MODE=live for real data.
    """
    if settings.dataforseo_mode == "mock":
        return _mock_response(query, domain)
    
    return call_with_retry(_live_response, query, domain)