"""Scout agent for collecting the most relevant and recent articles."""

from __future__ import annotations

from typing import Any

from tools.guardrails import apply_guardrails
from tools.search_tool import search_news


class ScoutAgent:
    """Research scout agent.

    Agent instruction:
    You are a research scout.

    Find the 3 most relevant and recent news articles about the user's topic.

    Return:
    - Title
    - Summary
    - Image
    - Source
    """

    system_instruction = (
        "You are a research scout. Find the 3 most relevant and recent news articles "
        "about the user's topic and return Title, Summary, Image, and Source."
    )

    @staticmethod
    def _normalized_title(title: str) -> str:
        return " ".join(title.lower().split())

    @staticmethod
    def _content_fingerprint(summary: str) -> str:
        normalized = " ".join(summary.lower().split())
        return normalized[:220]

    def _deduplicate_articles(
        self,
        results: list[dict[str, Any]],
        thinking_log: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Remove duplicate articles by URL and near-identical title."""
        unique_results: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        seen_fingerprints: set[str] = set()

        for item in results:
            source_url = str(item.get("source_url", "")).strip().lower()
            normalized_title = self._normalized_title(str(item.get("title", "")))
            fingerprint = self._content_fingerprint(str(item.get("summary", "")))

            if source_url and source_url in seen_urls:
                if thinking_log is not None:
                    thinking_log.append("Scout: removed duplicate article by URL.")
                continue

            if normalized_title and normalized_title in seen_titles:
                if thinking_log is not None:
                    thinking_log.append("Scout: removed duplicate article by title.")
                continue

            if fingerprint and fingerprint in seen_fingerprints:
                if thinking_log is not None:
                    thinking_log.append("Scout: removed syndicated duplicate by content fingerprint.")
                continue

            if source_url:
                seen_urls.add(source_url)
            if normalized_title:
                seen_titles.add(normalized_title)
            if fingerprint:
                seen_fingerprints.add(fingerprint)

            unique_results.append(item)

        return unique_results

    def run(self, topic: str, thinking_log: list[str] | None = None) -> list[dict[str, Any]]:
        """Fetch and return top 3 guarded articles for a topic."""
        if thinking_log is not None:
            thinking_log.append(f"Scout: starting research for topic '{topic}'.")

        results = search_news(topic=topic, max_results=6, thinking_log=thinking_log)
        results = self._deduplicate_articles(results, thinking_log=thinking_log)

        curated: list[dict[str, Any]] = []
        for item in results:
            title = str(item.get("title", "")).strip()
            summary = str(item.get("summary", "")).strip()
            image = str(item.get("image", "")).strip()
            source = str(item.get("source", "")).strip()
            source_url = str(item.get("source_url", "")).strip()

            block_reason = apply_guardrails(" ".join([title, summary, image, source, source_url]))
            if block_reason:
                if thinking_log is not None:
                    thinking_log.append(
                        f"Scout: guardrail removed article from source '{source or source_url or 'unknown'}'."
                    )
                continue

            curated.append(
                {
                    "Title": title or "Untitled",
                    "Summary": summary or "No summary available.",
                    "Image": image or "No image available.",
                    "Source": source or "Unknown source",
                    "SourceUrl": source_url,
                    "Domain": item.get("domain", ""),
                    "Reliability": item.get("reliability", "Low"),
                    "ReliabilityScore": item.get("reliability_score", 1),
                    "PublishedAt": item.get("published_at"),
                }
            )

            if len(curated) == 3:
                break

        if thinking_log is not None:
            high_confidence = sum(1 for article in curated if article.get("Reliability") == "High")
            thinking_log.append(
                f"Scout: shortlisted {len(curated)} articles for analysis, including {high_confidence} high-reliability sources."
            )

        return curated
