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
    - Source
    """

    system_instruction = (
        "You are a research scout. Find the 3 most relevant and recent news articles "
        "about the user's topic and return Title, Summary, and Source."
    )

    def run(self, topic: str) -> list[dict[str, Any]]:
        """Fetch and return top 3 guarded articles for a topic."""
        results = search_news(topic=topic, max_results=6)

        curated: list[dict[str, Any]] = []
        for item in results:
            title = str(item.get("title", "")).strip()
            summary = str(item.get("summary", "")).strip()
            source = str(item.get("source", "")).strip()

            block_reason = apply_guardrails(" ".join([title, summary, source]))
            if block_reason:
                continue

            curated.append(
                {
                    "Title": title or "Untitled",
                    "Summary": summary or "No summary available.",
                    "Source": source or "Unknown source",
                    "PublishedAt": item.get("published_at"),
                }
            )

            if len(curated) == 3:
                break

        return curated
