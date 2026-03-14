"""Google ADK root agent for AI News Brief Generator.

Run with:
    adk web
from this folder.
"""

from __future__ import annotations

import os
from pathlib import Path

from google.adk.agents import Agent
from dotenv import load_dotenv

from tools.adk_tools import generate_news_brief


def _load_env_files() -> None:
    """Load env vars from common local paths used in this project."""
    current = Path(__file__).resolve()
    project_root = current.parent

    candidates = [
        project_root / ".env",
        project_root / "agents" / ".env",
    ]

    for candidate in candidates:
        if candidate.exists():
            load_dotenv(dotenv_path=candidate, override=False)


def _configure_google_auth_mode() -> None:
    """Normalize auth env vars for Vertex or API-key mode."""
    has_api_key = bool(os.getenv("GOOGLE_API_KEY"))
    raw_mode = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower()
    vertex_explicit = raw_mode in {"1", "true", "yes", "on"}

    if vertex_explicit:
        if not os.getenv("GOOGLE_CLOUD_PROJECT") and os.getenv("PROJECT_ID"):
            os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("PROJECT_ID", "")
        if not os.getenv("GOOGLE_CLOUD_LOCATION"):
            os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    elif has_api_key:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"


_load_env_files()
_configure_google_auth_mode()


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
