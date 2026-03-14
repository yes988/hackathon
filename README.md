# AI Intelligence Bureau

Track A: Intelligence Bureau

This repository contains a multi-agent AI news intelligence system for researching a topic, filtering unsafe or untrusted content, extracting concise insights, and presenting a professional briefing in a Streamlit interface.

The primary implementation lives in the `ai-news-swarm` subproject. The repository root also includes lightweight `agents`, `tools`, and `app` folders so the hackathon submission structure is visible at the top level.

## What The System Does

The workflow is designed for agentic research rather than a single one-shot prompt.

1. A Scout agent searches for relevant, recent articles.
2. The search layer retries with fallback queries if the first search fails or returns no results.
3. A guardrail removes untrusted or unsafe content before analysis.
4. An Analyst agent marks stale content and extracts five key insights.
5. A Writer agent produces the final intelligence briefing.
6. A final guardrail blocks unsafe output before anything is shown to the user.

## System Architecture Diagram

```mermaid
flowchart LR
	U[User Topic] --> S[Scout Agent\nSearch + Retry Recovery]
	S --> G1[Source Guardrail\nBlacklist / Unsafe Terms]
	G1 --> A[Analyst Agent\nFreshness + Insight Extraction]
	A --> W[Writer Agent\nProfessional Briefing]
	W --> G2[Final Output Guardrail]
	G2 --> UI[Streamlit UI + Thinking Log]
```
<img src="images/screenshot.png" width="400">


The diagram source is also saved in `architecture.mmd`.

## Submission Checklist Mapping

- Track selection: `Track A: Intelligence Bureau` is stated explicitly in this README and in the app UI.
- Directory structure: top-level `agents`, `tools`, and `app` folders are included for submission visibility.
- Agentic agency: the system shows a visible thinking log with step-by-step agent activity.
- Standard implementation: the project uses Google ADK instead of a hand-rolled orchestration framework.
- System robustness: guardrails block blacklisted sources and offensive output, and the search layer performs retry and fallback recovery.
- Documentation: this README includes the system architecture diagram and role descriptions.

## Agent Roles

- Scout Agent: gathers recent articles and recovers from search failures by trying fallback queries.
- Analyst Agent: annotates article freshness and extracts five concise insights.
- Writer Agent: formats the final report into title, key insights, image references, and summary.
- Guardrail Layer: blocks untrusted sources and unsafe generated output.

## Guardrails

Guardrails are implemented in `ai-news-swarm/tools/guardrails.py`.

Current checks:

- Untrusted source blacklist
- Offensive output filter
- Early filtering during scouting
- Final blocking before rendering the report

This satisfies the hackathon requirement to demonstrate system robustness rather than only raw generation quality.

## Recovery Behavior

The search layer now demonstrates recovery behavior for judging:

- If the initial Tavily request fails, the Scout logs the failure.
- The system retries with fallback queries.
- The thinking log explicitly shows messages such as `trying a fallback query` and `fallback query recovered the search flow`.

## Thinking Log

For the demo, the app now exposes a terminal-style thinking log that shows:

- orchestration start
- search attempts
- fallback recovery
- guardrail filtering
- analysis completion
- writer completion

This is visible in the Streamlit UI and also printed when the CLI entrypoint is used.

## Key Paths

- Main project: `ai-news-swarm`
- UI: `ai-news-swarm/app/streamlit_app.py`
- Orchestrator: `ai-news-swarm/main.py`
- Agents: `ai-news-swarm/agents`
- Tools: `ai-news-swarm/tools`

## Run The Project

From `ai-news-swarm`:

```bash
pip install -r requirements.txt
set TAVILY_API_KEY=your_tavily_api_key
set GOOGLE_API_KEY=your_google_api_key
streamlit run app/streamlit_app.py
```

Optional ADK web mode:

```bash
adk web --adk_apps_dir .
```

## Demo Guidance

For the hackathon video:

- keep the video under 150 seconds
- set the YouTube video to Unlisted
- show the thinking log during generation
- trigger or describe a failed search so the fallback recovery is visible
- show a guardrail block example if possible
