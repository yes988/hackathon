"""Main orchestration for AI news brief generation.

Workflow:
    topic
      -> Scout Agent
      -> Analyst Agent
      -> Writer Agent
      -> Guardrail
      -> Final output
"""

from __future__ import annotations

import argparse
from typing import Any

from agents.analyst_agent import AnalystAgent
from agents.scout_agent import ScoutAgent
from agents.writer_agent import WriterAgent
from tools.guardrails import apply_guardrails


def generate_report(topic: str) -> dict[str, Any]:
    """Run the full multi-agent pipeline and return structured output."""
    cleaned_topic = topic.strip()
    if not cleaned_topic:
        raise ValueError("Topic cannot be empty.")

    thinking_log = [f"Orchestrator: received topic '{cleaned_topic}'."]

    scout = ScoutAgent()
    analyst = AnalystAgent()
    writer = WriterAgent()

    articles = scout.run(cleaned_topic, thinking_log=thinking_log)
    analysis = analyst.analyze(articles, thinking_log=thinking_log)
    report_text = writer.write_briefing(
        topic=cleaned_topic,
        key_insights=analysis["key_insights"],
        annotated_articles=analysis["annotated_articles"],
        thinking_log=thinking_log,
    )

    # Enforce a final safety gate even if earlier steps already applied checks.
    guardrail_result = apply_guardrails(report_text)
    final_output = guardrail_result if guardrail_result else report_text

    if guardrail_result:
        thinking_log.append(f"Orchestrator: final output blocked by guardrail with '{guardrail_result}'.")
    else:
        thinking_log.append("Orchestrator: report generation completed successfully.")

    return {
        "topic": cleaned_topic,
        "articles": articles,
        "analysis": analysis,
        "final_output": final_output,
        "guardrail_blocked": bool(guardrail_result),
        "thinking_log": thinking_log,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate an AI news briefing report.")
    parser.add_argument(
        "topic",
        nargs="?",
        default="",
        help="Topic to search and generate a news briefing for.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    topic = args.topic.strip()
    if not topic:
        topic = input("Enter topic: ").strip()

    result = generate_report(topic)
    for entry in result.get("thinking_log", []):
        print(f"[Thinking] {entry}")
    print()
    print(result["final_output"])


if __name__ == "__main__":
    main()
