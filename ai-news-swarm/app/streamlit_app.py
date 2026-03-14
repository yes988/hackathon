"""Streamlit UI for AI News Brief Generator."""

from __future__ import annotations

import os
import sys

import streamlit as st

# Ensure imports work when launched as: streamlit run app/streamlit_app.py
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import generate_report  # noqa: E402


st.set_page_config(page_title="AI News Brief Generator", page_icon="📰", layout="centered")
st.title("AI News Brief Generator")
st.write("Enter a topic to generate a professional AI news briefing.")

topic = st.text_input("Enter topic:", value="AI developments in Malaysia")

if st.button("Generate Report", type="primary"):
    topic_value = topic.strip()
    if not topic_value:
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Gathering and analyzing articles..."):
            try:
                result = generate_report(topic_value)
            except Exception as exc:
                st.error(f"Failed to generate report: {exc}")
            else:
                if result.get("guardrail_blocked"):
                    st.error(result["final_output"])
                else:
                    st.subheader("Final Briefing")
                    st.text(result["final_output"])

                articles = result.get("analysis", {}).get("annotated_articles", [])
                if articles:
                    st.subheader("Article Details")
                    for idx, article in enumerate(articles, start=1):
                        title = article.get("Title", "Untitled")
                        with st.expander(f"{idx}. {title}"):
                            st.write(f"Source: {article.get('Source', 'Unknown source')}")
                            st.write(f"Freshness: {article.get('Freshness', 'Unknown')}")
                            st.write(article.get("Summary", "No summary available."))
