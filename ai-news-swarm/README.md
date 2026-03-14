AI News Swarm

Track A: Intelligence Bureau

This subproject contains the primary implementation for the hackathon submission: a multi-agent AI news research workflow built on Google ADK with a Streamlit UI.

## Core Features

- Multi-agent flow: Scout, Analyst, Writer
- Recovery behavior: fallback search queries when the first search fails
- Guardrails: source blacklist and offensive output blocking
- Thinking log: visible step-by-step agent activity for demos and judging
- UI: Streamlit interface for report generation and evidence review

## Setup

```bash
pip install -r requirements.txt
set TAVILY_API_KEY=your_tavily_api_key
set GOOGLE_API_KEY=your_google_api_key
```

Optional model override:

```bash
set GOOGLE_GENAI_MODEL=gemini-2.0-flash
```

## Run Streamlit UI

```bash
streamlit run app/streamlit_app.py
```

## Run ADK Web

```bash
adk web --adk_apps_dir .
```

## Workflow

1. Scout Agent searches for recent articles.
2. The search layer retries with fallback queries on failure.
3. Guardrails remove untrusted or unsafe content.
4. Analyst Agent extracts five key insights and flags stale items.
5. Writer Agent produces the final intelligence briefing.
6. Final output passes through a final guardrail check.

## Guardrail Coverage

Guardrails are implemented in `tools/guardrails.py` and enforced during both scouting and final output generation.

## Demo Notes

Use the thinking log in the UI to show agent activity, fallback recovery, and guardrail behavior during the hackathon demo.
