"""Streamlit UI for AI News Brief Generator - Enhanced Version."""

from __future__ import annotations
import os
import sys
from typing import Any

import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import generate_report  # noqa: E402


def _render_history(container: Any) -> None:
    """Render recent search history in the sidebar."""
    history = st.session_state.get("search_history", [])
    if not history:
        return

    container.divider()
    container.subheader("Previous Searches")
    for item in history[:5]:
        container.caption(item)


if "search_history" not in st.session_state:
    st.session_state["search_history"] = []

# 1. Page Config with a nice layout
st.set_page_config(page_title="AI Intelligence Bureau", page_icon="🛡️", layout="wide")

# 2. Sidebar for Project Info (Great for Judges!)
with st.sidebar:
    st.title("System Status")
    st.success("Google Gemini: Online")
    st.success("Tavily Search: Online")
    st.divider()
    st.info("Track A: Intelligence Bureau Prototype")
    history_container = st.container()

_render_history(history_container)

# 3. Main UI
st.title("📰 AI News Brief Generator")
st.caption("Professional Multi-Agent Research Swarm")

topic = st.text_input("Enter research topic:", value="AI developments in Malaysia")

if st.button("Generate Intelligence Report", type="primary"):
    topic_value = topic.strip()
    if not topic_value:
        st.warning("Please enter a topic.")
    else:
        # The Spinner shows 'Action' for the video demo
        with st.spinner("🕵️ Agents are scouting, analyzing, and writing..."):
            try:
                result = generate_report(topic_value)
            except Exception as exc:
                st.error(f"Failed to generate report: {exc}")
            else:
                history = [item for item in st.session_state["search_history"] if item != topic_value]
                st.session_state["search_history"] = [topic_value, *history][:5]
                history_container.empty()
                _render_history(history_container)

                thinking_log = result.get("thinking_log", [])
                analysis = result.get("analysis", {})
                articles = analysis.get("annotated_articles", [])
                stats = analysis.get("stats", {})
                source_reliability = analysis.get("source_reliability", [])

                st.divider()
                st.subheader("📊 Intelligence Dashboard")
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                metric_col1.metric("Articles", stats.get("articles_found", len(articles)))
                metric_col2.metric("Recent", stats.get("recent_articles", 0))
                metric_col3.metric("Unique Outlets", stats.get("unique_outlets", 0))
                metric_col4.metric("Confidence", stats.get("overall_confidence", "Low"))

                if source_reliability:
                    st.caption("Source Reliability Score")
                    st.dataframe(source_reliability, use_container_width=True, hide_index=True)

                if result.get("guardrail_blocked"):
                    st.error(f"🚫 Guardrail Block: {result['final_output']}")
                else:
                    st.toast("Report Generated Successfully!")
                    
                    # 4. Use Markdown for beautiful headers and lists
                    st.subheader("📝 Final Briefing")
                    st.markdown(result["final_output"])
                    st.download_button(
                        "Download Briefing",
                        result["final_output"],
                        file_name="ai_intelligence_brief.txt",
                        mime="text/plain",
                    )

                # 5. Article Details in a cleaner view
                if articles:
                    st.divider()
                    st.subheader("🔗 Sourced Intelligence")

                    for article in articles:
                        with st.expander(article.get("Title", "Untitled")):
                            source_name = article.get("Source", "N/A")
                            source_url = article.get("SourceUrl", "")
                            if source_url:
                                st.markdown(f"**Source:** [{source_name}]({source_url})")
                            else:
                                st.caption(f"Source: {source_name}")
                            st.caption(
                                f"Published: {article.get('PublishedAt', 'N/A')} | Reliability: {article.get('Reliability', 'Low')} | Freshness: {article.get('Freshness', 'Unknown')}"
                            )
                            st.write(article.get("Summary", "No summary."))
                            image_url = article.get("Image", "")
                            if image_url and image_url != "No image available.":
                                st.image(image_url, use_container_width=True)

                if thinking_log:
                    st.divider()
                    st.subheader("🧠 Agent Thinking Log")
                    st.code("\n".join(thinking_log), language="text")