"""Search tool for retrieving recent news articles via Tavily API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


def _extract_published_at(result: dict[str, Any]) -> str | None:
    """Best-effort extraction of publication timestamp from Tavily-like result payloads."""
    for key in ("published_date", "published_at", "date"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalize_article(result: dict[str, Any]) -> dict[str, Any]:
    """Map Tavily result fields into a consistent article schema for downstream agents."""
    return {
        "title": result.get("title", "Untitled"),
        "summary": result.get("content", "").strip(),
        "source": result.get("url", ""),
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


def search_news(topic: str, max_results: int = 5) -> list[dict[str, Any]]:
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

    payload = {
        "api_key": api_key,
        "query": topic,
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
        raise RuntimeError(
            f"Tavily request failed with status {exc.code}: {error_body}"
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Tavily request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Tavily response was not valid JSON.") from exc

    raw_results = body.get("results", [])
    if not isinstance(raw_results, list):
        return []

    normalized = [_normalize_article(item) for item in raw_results if isinstance(item, dict)]
    sorted_articles = _sort_by_recency(normalized)
    return sorted_articles[: max(1, max_results)]
