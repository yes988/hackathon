"""Basic guardrails for source trust and offensive content filtering."""

from __future__ import annotations

from tools.news_cleaner import looks_corrupted_text

UNTRUSTED_SOURCES = {
    "fake-source.com",
    "beforeitsnews.com",
    "infowars.com",
    "sputniknews.com",
}

OFFENSIVE_TERMS = {
    "hate",
    "slur",
    "kill all",
    "ethnic cleansing",
    "genocide",
}

SCRAPE_ARTIFACT_TERMS = {
    "## most viewed",
    "support the guardian",
    "print subscriptions",
    "[... ]",
    "[...]",
}


def block_untrusted_source(text: str) -> str | None:
    """Block text containing known untrusted source domains."""
    lowered = text.lower()
    for source in UNTRUSTED_SOURCES:
        if source in lowered:
            return "Blocked: Untrusted source"
    return None


def block_offensive_output(text: str) -> str | None:
    """Block text containing offensive language markers."""
    lowered = text.lower()
    for term in OFFENSIVE_TERMS:
        if term in lowered:
            return "Blocked: Offensive output"
    return None


def block_scrape_artifacts(text: str) -> str | None:
    """Block output that still contains website navigation or scrape artifacts."""
    lowered = text.lower()
    for term in SCRAPE_ARTIFACT_TERMS:
        if term in lowered:
            return "Blocked: Scrape artifact detected"
    return None


def block_corrupted_output(text: str) -> str | None:
    """Block output that contains corrupted or encoded-looking strings."""
    if looks_corrupted_text(text):
        return "Blocked: Corrupted output"
    return None


def apply_guardrails(text: str) -> str | None:
    """Apply all guardrails and return first blocking reason, if any."""
    for checker in (
        block_untrusted_source,
        block_offensive_output,
        block_scrape_artifacts,
        block_corrupted_output,
    ):
        result = checker(text)
        if result:
            return result
    return None
