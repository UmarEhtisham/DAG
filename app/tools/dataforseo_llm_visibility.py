# app/tools/dataforseo_llm_visibility.py
import requests
from app.config import settings
from app.tools.base import call_with_retry, PermanentError


def _mock_response(query: str, domain: str) -> dict:
    return {
        "query": query,
        "domain": domain,
        "domain_mentioned": False,
        "mentioned_in": [],
        "competitor_mentions": [
            {"domain": "competitor1.com", "llm": "ChatGPT"},
            {"domain": "competitor2.com", "llm": "Gemini"},
        ],
        "source": "mock"
    }


def _live_response(query: str, domain: str) -> dict:
    url = "https://api.dataforseo.com/v3/keywords_data/bing/search_volume/live"

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

    mentioned_in = []
    domain_mentioned = False

    for item in result.get("items", []):
        if domain in item.get("domain", ""):
            domain_mentioned = True
            mentioned_in.append(item.get("llm", "unknown"))

    return {
        "query": query,
        "domain": domain,
        "domain_mentioned": domain_mentioned,
        "mentioned_in": mentioned_in,
        "source": "live"
    }


def get_llm_visibility(query: str, domain: str) -> dict:
    """
    Checks if a domain is mentioned in LLM answers (ChatGPT, Gemini etc.)
    for a given query.
    Uses mock data by default — set DATAFORSEO_MODE=live for real data.
    """
    if settings.dataforseo_mode == "mock":
        return _mock_response(query, domain)

    return call_with_retry(_live_response, query, domain)