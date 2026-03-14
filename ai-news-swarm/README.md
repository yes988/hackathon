# AI News Swarm (Google ADK Web)

This project now supports Google ADK Web as the main interaction UI.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set required environment variables:

```bash
set TAVILY_API_KEY=your_tavily_api_key
set GOOGLE_API_KEY=your_google_api_key
```

Optional model override:

```bash
set GOOGLE_GENAI_MODEL=gemini-2.0-flash
```

## Run ADK Web

From this folder (`ai-news-swarm`), run:

```bash
adk web
```

ADK will load `agent.py` and expose a web chat UI.

## Agent Workflow

The ADK agent uses this workflow internally:

1. Scout Agent finds top 3 relevant and recent articles.
2. Analyst Agent extracts 5 key insights and marks items older than 24 hours as "Potentially Outdated".
3. Writer Agent generates the final report with sections: Title, Key Insights, Summary.
4. Guardrails block offensive output and untrusted sources.
