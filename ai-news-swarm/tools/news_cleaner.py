"""Utilities for cleaning scraped news text before analysis."""

from __future__ import annotations

import re

NOISE_PATTERNS = [
    r"Advertisement.*",
    r"Subscribe.*",
    r"Most Popular.*",
    r"Skip to main content.*",
    r"Your Ad Blocker.*",
    r"Only sign in.*",
    r"The Benefits of Unlimited Digital Access.*",
    r"Let's Play.*",
    r"\(AP Photo.*?\)",
    r"\d+\s*of\s*\d+\s*\|",
    r"FILE-.*?\)",
]


def clean_news_text(text: str) -> str:
    """Remove ads, captions, and page UI noise from scraped text."""
    cleaned = text
    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\n\s*\n", "\n", cleaned)
    return cleaned.strip()


def remove_duplicate_paragraphs(text: str) -> str:
    """Drop repeated paragraphs that often occur in syndicated content."""
    paragraphs = text.split("\n")
    seen: set[str] = set()
    cleaned: list[str] = []

    for paragraph in paragraphs:
        normalized = " ".join(paragraph.split())
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(normalized)

    return "\n".join(cleaned)


def limit_article(text: str, max_chars: int = 1200) -> str:
    """Keep article text concise for downstream summarization."""
    return text[:max_chars].strip()


def preprocess_article(text: str) -> str:
    """Run complete cleaning pipeline for article text."""
    cleaned = clean_news_text(text)
    cleaned = remove_duplicate_paragraphs(cleaned)
    cleaned = limit_article(cleaned)
    return cleaned


def is_low_quality_article(text: str, min_chars: int = 300) -> bool:
    """Flag very short content that is likely too weak for analysis."""
    return len(text.strip()) < min_chars
