"""Basic guardrails for source trust and offensive content filtering."""

from __future__ import annotations

UNTRUSTED_SOURCES = {
    "fake-source.com",
}

OFFENSIVE_TERMS = {
    "hate",
    "slur",
    "kill all",
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


def apply_guardrails(text: str) -> str | None:
    """Apply all guardrails and return first blocking reason, if any."""
    for checker in (block_untrusted_source, block_offensive_output):
        result = checker(text)
        if result:
            return result
    return None
