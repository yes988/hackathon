"""Search tool for retrieving recent news articles via Tavily API."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from tools.news_cleaner import clean_news_text, is_low_quality_article, preprocess_article

TAVILY_SEARCH_URL = "https://api.tavily.com/search"

HIGH_RELIABILITY_DOMAINS = {
    "apnews.com",
    "reuters.com",
    "bloomberg.com",
    "bbc.com",
    "bbc.co.uk",
    "washingtonpost.com",
    "nytimes.com",
    "wsj.com",
    "ft.com",
    "npr.org",
    "cnbc.com",
    "cnn.com",
}

MEDIUM_RELIABILITY_DOMAINS = {
    "techcrunch.com",
    "theverge.com",
    "wired.com",
    "arstechnica.com",
    "venturebeat.com",
    "engadget.com",
    "zdnet.com",
    "forbes.com",
    "fastcompany.com",
}

def _log(thinking_log: list[str] | None, message: str) -> None:
    """Append a message to the optional thinking log."""
    if thinking_log is not None:
        thinking_log.append(message)


def _env_flag(name: str) -> bool:
    """Return True when an environment flag is enabled."""
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _clean_title(title: str) -> str:
    """Normalize title text to remove scrape artifacts while preserving meaning."""
    cleaned = clean_news_text(title)
    cleaned = re.sub(r"\d+\s*of\s*\d+\s*\|", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"FILE-.*?\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = " ".join(cleaned.split())
    return cleaned


def _extract_published_at(result: dict[str, Any]) -> str | None:
    """Best-effort extraction of publication timestamp from Tavily-like result payloads."""
    for key in ("published_date", "published_at", "date"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_image(result: dict[str, Any]) -> str:
    """Best-effort extraction of an article image URL."""
    for key in ("image", "image_url", "thumbnail_url"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _extract_domain(url: str) -> str:
    """Return a normalized domain without common subdomain prefixes."""
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _format_outlet(domain: str) -> str:
    """Create a readable outlet name from a domain."""
    if not domain:
        return "Unknown Outlet"

    parts = domain.split(".")
    if len(parts) >= 2:
        label = parts[-2]
    else:
        label = domain

    return label.replace("-", " ").title()


def _score_reliability(domain: str) -> tuple[str, int]:
    """Map a domain to a simple reliability label and score."""
    if domain in HIGH_RELIABILITY_DOMAINS:
        return "High", 3
    if domain in MEDIUM_RELIABILITY_DOMAINS:
        return "Medium", 2
    return "Low", 1


def _normalize_article(result: dict[str, Any]) -> dict[str, Any]:
    """Map Tavily result fields into a consistent article schema for downstream agents."""
    source_url = str(result.get("url", "")).strip()
    domain = _extract_domain(source_url)
    reliability, reliability_score = _score_reliability(domain)
    raw_title = str(result.get("title", "Untitled")).strip()
    raw_content = str(result.get("content", "")).strip()
    cleaned_title = _clean_title(raw_title) or "Untitled"
    cleaned_summary = preprocess_article(raw_content)

    return {
        "title": cleaned_title,
        "summary": cleaned_summary,
        "source": _format_outlet(domain),
        "source_url": source_url,
        "domain": domain,
        "reliability": reliability,
        "reliability_score": reliability_score,
        "image": _extract_image(result),
        "published_at": _extract_published_at(result),
    }


def _sort_by_recency(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort articles by publication timestamp (newest first) when timestamps are available."""

    def sort_key(article: dict[str, Any]) -> datetime:
        raw_value = article.get("published_at")
        if not isinstance(raw_value, str) or not raw_value.strip():
            return datetime.min.replace(tzinfo=timezone.utc)

        value = raw_value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return sorted(articles, key=sort_key, reverse=True)


def _build_query_candidates(topic: str) -> list[str]:
    """Return primary plus fallback queries for recovery when search fails or is sparse."""
    normalized = " ".join(topic.split())
    lowered = normalized.lower()
    candidates = [normalized]

    if not normalized.lower().startswith("ai "):
        candidates.append(f"AI {normalized}")

    candidates.append(f"{normalized} latest news")

    shortened = " ".join(normalized.split()[:6])
    if shortened and shortened != normalized:
        candidates.append(shortened)

    # Add geography-aware AI fallbacks for prompts like
    # "AI developments in Malaysia" where direct phrasing can be too narrow.
    location_match = re.search(r"\bin\s+([a-zA-Z][a-zA-Z\s-]{2,})$", normalized, flags=re.IGNORECASE)
    if location_match:
        location = " ".join(location_match.group(1).split())
        candidates.extend(
            [
                f"AI in {location}",
                f"{location} artificial intelligence news",
                f"{location} AI policy",
            ]
        )

    if "anthropic" in lowered:
        candidates.extend(
            [
                "Anthropic Claude news",
                "Anthropic AI enterprise updates",
            ]
        )

    finance_tokens = {"money", "finance", "fintech", "banking", "economy", "payments"}
    topic_terms = set(re.findall(r"[a-zA-Z0-9]+", lowered))
    if topic_terms & finance_tokens:
        candidates.extend(
            [
                f"{normalized} finance economy fintech banking business",
                f"{normalized} market regulation enterprise",
            ]
        )

    unique_candidates: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.lower()
        if key not in seen:
            seen.add(key)
            unique_candidates.append(candidate)

    return unique_candidates


def search_news(
    topic: str,
    max_results: int = 5,
    thinking_log: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search the internet for news articles related to a topic using Tavily API.

    Args:
        topic: User-provided topic to search.
        max_results: Maximum number of articles to return.

    Returns:
        A list of normalized article dictionaries with title/summary/source/published_at.

    Raises:
        ValueError: If topic is empty or API key is missing.
        RuntimeError: If Tavily request fails.
    """
    topic = topic.strip()
    if not topic:
        raise ValueError("Topic cannot be empty.")

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("Missing TAVILY_API_KEY environment variable.")

    errors: list[str] = []
    queries = _build_query_candidates(topic)
    demo_force_fallback = _env_flag("RECOVERY_DEMO_FORCE_FALLBACK")

    for attempt, query in enumerate(queries, start=1):
        _log(thinking_log, f"Scout: search attempt {attempt} using query '{query}'.")

        # Deterministic demo mode: force attempt 1 to fail so fallback behavior is visible.
        if demo_force_fallback and attempt == 1 and len(queries) > 1:
            _log(thinking_log, "Scout: demo mode forced no results for attempt 1.")
            _log(thinking_log, f"Scout: no results for '{query}'.")
            _log(thinking_log, "Scout: broadening the search query.")
            continue

        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "topic": "news",
            "max_results": max(1, max_results),
            "include_raw_content": False,
        }

        request_data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            TAVILY_SEARCH_URL,
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw_response = response.read().decode("utf-8")
                body = json.loads(raw_response)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            error_message = f"status {exc.code}: {error_body}"
            errors.append(error_message)
            _log(thinking_log, f"Scout: search failed for '{query}' with {error_message}.")
            if attempt < len(queries):
                _log(thinking_log, "Scout: trying a fallback query.")
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            error_message = str(exc)
            errors.append(error_message)
            _log(thinking_log, f"Scout: search failed for '{query}' with {error_message}.")
            if attempt < len(queries):
                _log(thinking_log, "Scout: trying a fallback query.")
            continue
        except json.JSONDecodeError:
            error_message = "response was not valid JSON"
            errors.append(error_message)
            _log(thinking_log, f"Scout: search failed for '{query}' because {error_message}.")
            if attempt < len(queries):
                _log(thinking_log, "Scout: trying a fallback query.")
            continue

        raw_results = body.get("results", [])
        if not isinstance(raw_results, list):
            _log(thinking_log, f"Scout: Tavily returned an unexpected payload for '{query}'.")
            continue

        normalized = [_normalize_article(item) for item in raw_results if isinstance(item, dict)]
        normalized = [item for item in normalized if not is_low_quality_article(item.get("summary", ""), 120)]
        sorted_articles = _sort_by_recency(normalized)
        final_results = sorted_articles[: max(1, max_results)]

        if final_results:
            _log(thinking_log, f"Scout: retrieved {len(final_results)} candidate articles.")
            if query != topic:
                _log(thinking_log, f"Scout: fallback query '{query}' recovered the search flow.")
            return final_results

        _log(thinking_log, f"Scout: no results for '{query}'.")
        if attempt < len(queries):
            _log(thinking_log, "Scout: broadening the search query.")

    if errors:
        raise RuntimeError(f"Tavily request failed after {len(queries)} attempts: {errors[-1]}")

    return []
