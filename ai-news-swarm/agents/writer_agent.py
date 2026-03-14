"""Writer agent for producing a professional AI news briefing."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from tools.guardrails import apply_guardrails


class WriterAgent:
    """Generates the final report.

    Prompt:
    Write a professional AI news briefing.

    Structure:
    Title
    Key Insights
    Image (if available)
    Summary
    """

    prompt = (
        "Create an intelligence briefing using only key insights. "
        "Do not copy raw article paragraphs. "
        "Use sections: Key Development, Why This Happened, Business Impact, "
        "Strategic Implications, Intelligence Assessment. "
        "Keep each section concise, around 2 to 4 sentences."
    )

    @staticmethod
    def _topic_label(topic: str) -> str:
        return " ".join(topic.split()).title() if topic.strip() else "Unknown Topic"

    @staticmethod
    def _first_nonempty(items: list[str], fallback: str) -> str:
        for item in items:
            if item.strip():
                return item.strip()
        return fallback

    @staticmethod
    def _unique_nonempty(items: list[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for item in items:
            normalized = " ".join(item.split())
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalized)
        return unique

    @staticmethod
    def _limit_sentences(text: str, max_sentences: int = 3) -> str:
        parts = [part.strip() for part in text.replace("\n", " ").split(".") if part.strip()]
        limited = parts[:max_sentences]
        if not limited:
            return text.strip()
        return ". ".join(limited) + "."

    def write_briefing(
        self,
        topic: str,
        key_insights: list[str],
        annotated_articles: list[dict[str, Any]],
        thinking_log: list[str] | None = None,
    ) -> str:
        """Create the final briefing text with required sections."""
        if thinking_log is not None:
            thinking_log.append(
                f"Writer: drafting briefing for '{topic}' from {len(annotated_articles)} annotated articles."
            )

        title = f"AI Intelligence Brief - {self._topic_label(topic)}"
        date_label = datetime.now().strftime("%B %Y")

        stats = {
            "articles_found": len(annotated_articles),
            "recent_articles": sum(1 for article in annotated_articles if article.get("Freshness") == "Recent"),
            "unique_outlets": len({str(article.get('Source', 'Unknown source')) for article in annotated_articles}),
            "overall_confidence": "Low",
        }

        if annotated_articles:
            reliability_scores = [int(article.get("ReliabilityScore", 1)) for article in annotated_articles]
            average_reliability = sum(reliability_scores) / len(reliability_scores)
            if average_reliability >= 2.5:
                stats["overall_confidence"] = "High"
            elif average_reliability >= 1.75:
                stats["overall_confidence"] = "Medium"

        lead_summary = self._first_nonempty(
            [str(article.get("Summary", "")) for article in annotated_articles],
            "No trustworthy articles were available for this topic at this time.",
        )
        lead_summary = self._limit_sentences(lead_summary, max_sentences=3)

        why_happened = [
            str(article.get("Summary", "")).strip()
            for article in annotated_articles[1:3]
            if str(article.get("Summary", "")).strip()
        ]
        if not why_happened:
            why_happened = [insight for insight in key_insights[:2] if insight.strip()]
        why_happened = [self._limit_sentences(item, max_sentences=2) for item in self._unique_nonempty(why_happened)]
        if not why_happened:
            why_happened = ["Insufficient trustworthy evidence was found to infer a root cause."]

        source_reliability_lines = []
        seen_sources: set[str] = set()
        for article in annotated_articles:
            source_name = str(article.get("Source", "Unknown source"))
            source_key = source_name.lower()
            if source_key in seen_sources:
                continue
            seen_sources.add(source_key)
            source_reliability_lines.append(f"- {source_name} - {article.get('Reliability', 'Low')}")

        implication_lines = []
        unique_implications = self._unique_nonempty([str(item) for item in key_insights])
        for idx, insight in enumerate(unique_implications[:3], start=1):
            implication_lines.append(f"{idx}. {insight}")
        if not implication_lines:
            implication_lines.append("1. No validated strategic implications are available from the current source set.")

        assessment_lines = []
        if stats["articles_found"]:
            assessment_lines.append(
                f"- Short-term: monitored coverage is based on {stats['articles_found']} articles across {stats['unique_outlets']} outlets."
            )
            assessment_lines.append(
                f"- Confidence: source quality is assessed as {stats['overall_confidence']} with {stats['recent_articles']} recent articles."
            )
            assessment_lines.append(
                "- Long-term: continued policy, commercial, and platform responses should be tracked for follow-on effects."
            )
        else:
            assessment_lines.append("- Confidence remains low because no trustworthy articles were available.")

        report = "\n".join(
            [
                title,
                "",
                f"Date: {date_label}",
                f"Topic: {topic}",
                "",
                "---",
                "",
                "### Key Development",
                f"- {lead_summary}",
                "",
                "### Why This Happened",
                "\n".join(f"- {item}" for item in why_happened),
                "",
                "### Business Impact",
                f"- Sources analyzed: {stats['articles_found']}",
                f"- Recent articles: {stats['recent_articles']}",
                f"- Unique outlets: {stats['unique_outlets']}",
                f"- Overall source confidence: {stats['overall_confidence']}",
                "",
                "### Strategic Implications",
                "\n".join(implication_lines),
                "",
                "### Intelligence Assessment",
                "\n".join(assessment_lines),
                "",
                "### Source Reliability Score",
                "\n".join(source_reliability_lines) if source_reliability_lines else "- No reliable sources available.",
            ]
        )

        block_reason = apply_guardrails(report)
        if block_reason:
            if thinking_log is not None:
                thinking_log.append(f"Writer: final guardrail blocked the report with '{block_reason}'.")
            return block_reason

        if thinking_log is not None:
            thinking_log.append("Writer: final briefing passed the report guardrail.")

        return report
