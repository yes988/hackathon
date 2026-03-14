"""Analyst agent for extracting structured insights from articles."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class AnalystAgent:
    """Analyzes articles and extracts five key insights.

    Prompt:
    Analyze the articles.

    Extract 5 key insights.

    If an article is older than 24 hours,
    mark it as "Potentially Outdated".
    """

    prompt = (
        "Analyze the articles. Extract 5 key insights. "
        "If an article is older than 24 hours, mark it as 'Potentially Outdated'."
    )

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            return None

        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _is_potentially_outdated(self, published_at: Any) -> bool:
        parsed = self._parse_datetime(published_at)
        if parsed is None:
            return False

        return datetime.now(timezone.utc) - parsed > timedelta(hours=24)

    def analyze(self, articles: list[dict[str, Any]]) -> dict[str, Any]:
        """Return article annotations plus five concise insights."""
        annotated_articles: list[dict[str, Any]] = []
        for article in articles:
            item = dict(article)
            item["Freshness"] = (
                "Potentially Outdated"
                if self._is_potentially_outdated(item.get("PublishedAt"))
                else "Recent"
            )
            annotated_articles.append(item)

        insights: list[str] = []
        for article in annotated_articles:
            title = str(article.get("Title", "Untitled"))
            summary = str(article.get("Summary", "")).strip()
            freshness = article.get("Freshness", "Recent")
            base = summary if summary else "No detailed summary provided."
            insights.append(f"{title}: {base} ({freshness})")
            if len(insights) == 5:
                break

        while len(insights) < 5:
            insights.append("No additional high-confidence insight available from current article set.")

        return {
            "annotated_articles": annotated_articles,
            "key_insights": insights,
        }
