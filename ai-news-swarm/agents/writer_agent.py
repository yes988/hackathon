"""Writer agent for producing a professional AI news briefing."""

from __future__ import annotations

from typing import Any

from tools.guardrails import apply_guardrails


class WriterAgent:
    """Generates the final report.

    Prompt:
    Write a professional AI news briefing.

    Structure:
    Title
    Key Insights
    Summary
    """

    prompt = (
        "Write a professional AI news briefing with this structure: "
        "Title, Key Insights, Summary."
    )

    def write_briefing(
        self,
        topic: str,
        key_insights: list[str],
        annotated_articles: list[dict[str, Any]],
    ) -> str:
        """Create the final briefing text with required sections."""
        title = f"AI News Briefing: {topic}"

        insights_lines = []
        for idx, insight in enumerate(key_insights, start=1):
            insights_lines.append(f"{idx}. {insight}")

        if annotated_articles:
            recency_stats = {
                "Recent": 0,
                "Potentially Outdated": 0,
            }
            for article in annotated_articles:
                freshness = str(article.get("Freshness", "Recent"))
                if freshness in recency_stats:
                    recency_stats[freshness] += 1

            summary = (
                f"Reviewed {len(annotated_articles)} articles. "
                f"{recency_stats['Recent']} recent and "
                f"{recency_stats['Potentially Outdated']} potentially outdated."
            )
        else:
            summary = "No trustworthy articles were available for this topic at this time."

        report = "\n".join(
            [
                title,
                "",
                "Key Insights",
                "\n".join(insights_lines),
                "",
                "Summary",
                summary,
            ]
        )

        block_reason = apply_guardrails(report)
        if block_reason:
            return block_reason

        return report
