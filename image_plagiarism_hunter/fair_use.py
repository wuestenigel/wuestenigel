"""Fair use assessment heuristics for detected image matches."""

from urllib.parse import urlparse

from .models import FairUseIndicator, ImageMatch, Violation

# Domains commonly associated with fair use (education, news, non-profit)
FAIR_USE_DOMAIN_PATTERNS = [
    ".edu",
    ".gov",
    ".org",
    "wikipedia.org",
    "wikimedia.org",
    "archive.org",
    "creativecommons.org",
]

# Domains commonly associated with commercial use
COMMERCIAL_DOMAIN_PATTERNS = [
    ".shop",
    ".store",
    "amazon.",
    "ebay.",
    "etsy.",
    "shopify.",
    "aliexpress.",
    "alibaba.",
]

# URL path patterns suggesting editorial/educational use
EDITORIAL_PATH_PATTERNS = [
    "/blog/",
    "/news/",
    "/article/",
    "/review/",
    "/education/",
    "/research/",
    "/wiki/",
]


def assess_fair_use(match: ImageMatch) -> tuple[FairUseIndicator, str]:
    """Assess whether an image use might qualify as fair use.

    Returns an indicator and a brief explanation.
    This is a heuristic guide, not legal advice.
    """
    domain = match.domain.lower()
    url = match.page_url.lower()
    reasons = []

    # Check educational/government/non-profit domains
    for pattern in FAIR_USE_DOMAIN_PATTERNS:
        if domain.endswith(pattern) or pattern in domain:
            reasons.append(f"Domain '{domain}' suggests educational/non-profit use")
            break

    # Check for editorial context in URL path
    for pattern in EDITORIAL_PATH_PATTERNS:
        if pattern in url:
            reasons.append(f"URL path suggests editorial/educational context ('{pattern}')")
            break

    # Check for commercial indicators
    is_commercial = False
    for pattern in COMMERCIAL_DOMAIN_PATTERNS:
        if pattern in domain:
            is_commercial = True
            reasons.append(f"Domain '{domain}' suggests commercial use")
            break

    # High similarity means less transformative use
    if match.similarity_score > 95:
        reasons.append("Very high similarity suggests non-transformative use")

    # Determine overall assessment
    if is_commercial:
        return FairUseIndicator.UNLIKELY_FAIR_USE, "; ".join(reasons) or "Commercial context detected"

    if any("educational" in r or "non-profit" in r for r in reasons):
        return FairUseIndicator.LIKELY_FAIR_USE, "; ".join(reasons)

    return FairUseIndicator.UNCERTAIN, "; ".join(reasons) or "Insufficient signals for determination"


def estimate_commercial_use(domain: str) -> bool:
    """Estimate whether a domain is likely using the image commercially."""
    domain = domain.lower()
    for pattern in COMMERCIAL_DOMAIN_PATTERNS:
        if pattern in domain:
            return True
    return False
