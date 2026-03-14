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

    @staticmethod
    def _overall_confidence(average_reliability: float) -> str:
        if average_reliability >= 2.5:
            return "High"
        if average_reliability >= 1.75:
            return "Medium"
        return "Low"

    def analyze(
        self,
        articles: list[dict[str, Any]],
        thinking_log: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return article annotations plus five concise insights."""
        if thinking_log is not None:
            thinking_log.append(f"Analyst: reviewing {len(articles)} articles for freshness and themes.")

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

        unique_outlets = {str(article.get("Source", "Unknown source")) for article in annotated_articles}
        recent_count = sum(1 for article in annotated_articles if article.get("Freshness") == "Recent")
        reliability_scores = [int(article.get("ReliabilityScore", 1)) for article in annotated_articles]
        average_reliability = (
            sum(reliability_scores) / len(reliability_scores) if reliability_scores else 0.0
        )
        overall_confidence = self._overall_confidence(average_reliability)

        source_reliability = [
            {
                "Source": article.get("Source", "Unknown source"),
                "Reliability": article.get("Reliability", "Low"),
                "SourceUrl": article.get("SourceUrl", ""),
            }
            for article in annotated_articles
        ]

        if thinking_log is not None:
            outdated_count = sum(
                1 for article in annotated_articles if article.get("Freshness") == "Potentially Outdated"
            )
            thinking_log.append(
                f"Analyst: produced {len(insights)} key insights, flagged {outdated_count} outdated articles, and rated source confidence as {overall_confidence}."
            )

        return {
            "annotated_articles": annotated_articles,
            "key_insights": insights,
            "stats": {
                "articles_found": len(annotated_articles),
                "recent_articles": recent_count,
                "unique_outlets": len(unique_outlets),
                "average_reliability": round(average_reliability, 2),
                "overall_confidence": overall_confidence,
            },
            "source_reliability": source_reliability,
        }
