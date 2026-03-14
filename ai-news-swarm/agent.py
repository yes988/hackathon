"""Google ADK root agent for AI News Brief Generator.

Run with:
    adk web
from this folder.
"""

from __future__ import annotations

import os

from google.adk.agents import Agent

from tools.adk_tools import generate_news_brief


root_agent = Agent(
    name="ai_news_brief_agent",
    model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.0-flash"),
    description="Generates professional AI news briefings from recent web results.",
    instruction=(
        "You are an AI News Brief Generator. "
        "When the user gives a topic, call the generate_news_brief tool and return its output. "
        "Do not invent sources. Keep the exact report structure from the tool output."
    ),
    tools=[generate_news_brief],
)
