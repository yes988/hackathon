"""Tool functions exposed to Google ADK."""

from __future__ import annotations

import json
from typing import Any

from agents.analyst_agent import AnalystAgent
from agents.scout_agent import ScoutAgent
from agents.writer_agent import WriterAgent
from tools.guardrails import apply_guardrails


def _safe_json_load(value: str) -> list[dict[str, Any]]:
    """Parse article payloads from JSON strings."""
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON payload for articles.") from exc

    if not isinstance(loaded, list):
        raise ValueError("Articles payload must be a JSON list.")

    return [item for item in loaded if isinstance(item, dict)]


def scout_articles(topic: str) -> str:
    """Find top 3 relevant and recent articles for a topic.

    Returns JSON string with:
    - articles: [{Title, Summary, Source, PublishedAt}, ...]
    """
    scout = ScoutAgent()
    articles = scout.run(topic)
    return json.dumps({"articles": articles}, ensure_ascii=True)


def analyze_articles(articles_json: str) -> str:
    """Analyze articles and return 5 key insights.

    Input must be a JSON list of article objects.
    Returns JSON string with:
    - annotated_articles
    - key_insights
    """
    analyst = AnalystAgent()
    articles = _safe_json_load(articles_json)
    analysis = analyst.analyze(articles)
    return json.dumps(analysis, ensure_ascii=True)


def write_briefing(topic: str, analysis_json: str) -> str:
    """Generate a professional AI news briefing from analysis JSON."""
    try:
        loaded = json.loads(analysis_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON payload for analysis.") from exc

    if not isinstance(loaded, dict):
        raise ValueError("Analysis payload must be a JSON object.")

    writer = WriterAgent()
    key_insights = loaded.get("key_insights", [])
    annotated_articles = loaded.get("annotated_articles", [])

    if not isinstance(key_insights, list):
        key_insights = []
    if not isinstance(annotated_articles, list):
        annotated_articles = []

    report = writer.write_briefing(
        topic=topic,
        key_insights=[str(item) for item in key_insights],
        annotated_articles=[item for item in annotated_articles if isinstance(item, dict)],
    )
    return report


def run_guardrails(text: str) -> str:
    """Apply guardrails to generated output and return pass/fail message."""
    result = apply_guardrails(text)
    if result:
        return result
    return "Passed"


def generate_news_brief(topic: str) -> str:
    """One-shot workflow tool: Scout -> Analyst -> Writer -> Guardrail."""
    scout = ScoutAgent()
    analyst = AnalystAgent()
    writer = WriterAgent()

    articles = scout.run(topic)
    analysis = analyst.analyze(articles)
    report = writer.write_briefing(
        topic=topic,
        key_insights=analysis["key_insights"],
        annotated_articles=analysis["annotated_articles"],
    )

    guardrail = apply_guardrails(report)
    if guardrail:
        return guardrail

    return report
