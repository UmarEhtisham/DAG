# app/tools/dataforseo_ai_overview.py
import requests
from app.config import settings
from app.tools.base import call_with_retry, PermanentError


def _mock_response(query: str, domain: str) -> dict:
    return {
        "query": query,
        "domain": domain,
        "ai_overview_present": True,
        "domain_mentioned": False,
        "mentioned_domains": ["competitor1.com", "competitor2.com"],
        "overview_text": f"The best SEO tools include competitor1 and competitor2...",
        "source": "mock"
    }


def _live_response(query: str, domain: str) -> dict:
    url = "https://api.dataforseo.com/v3/serp/google/ai_overview/live/advanced"

    auth = (settings.dataforseo_login, settings.dataforseo_password)

    payload = [{
        "keyword": query,
        "location_code": 2840,
        "language_code": "en"
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
    result = data["tasks"][0]["result"][0]

    mentioned_domains = []
    domain_mentioned = False

    for item in result.get("items", []):
        if item.get("type") == "ai_overview":
            for ref in item.get("references", []):
                ref_domain = ref.get("domain", "")
                mentioned_domains.append(ref_domain)
                if domain in ref_domain:
                    domain_mentioned = True

    return {
        "query": query,
        "domain": domain,
        "ai_overview_present": True,
        "domain_mentioned": domain_mentioned,
        "mentioned_domains": mentioned_domains,
        "source": "live"
    }


def get_ai_overview(query: str, domain: str) -> dict:
    """
    Checks if a domain appears in Google's AI Overview for a given query.
    Uses mock data by default — set DATAFORSEO_MODE=live for real data.
    """
    if settings.dataforseo_mode == "mock":
        return _mock_response(query, domain)

    return call_with_retry(_live_response, query, domain)