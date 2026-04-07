import re
import unicodedata

from app.core.exceptions import SecurityException

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions?",
    r"you\s+are\s+now\s+(a|an|the)\s+",
    r"(forget|disregard|override)\s+(your|all|previous)",
    r"act\s+as\s+(if\s+you\s+are|a|an)",
    r"\bDAN\b",
    r"jailbreak",
    r"prompt\s*injection",
    r"<\s*script\s*>",
    r"system\s*:\s*you",
    r"###\s*(instruction|system|prompt)",
    r"ignore\s+above",
    r"new\s+instructions?\s*:",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

MAX_QUERY_LENGTH = 1000


def sanitize(query: str) -> str:
    query = query.strip()
    query = query[:MAX_QUERY_LENGTH]
    query = "".join(
        ch for ch in query if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t")
    )
    return query


def check_injection(query: str) -> tuple[bool, str]:
    for pattern in _compiled:
        if pattern.search(query):
            return True, pattern.pattern
    return False, ""


def validate_query(query: str) -> str:
    clean = sanitize(query)
    blocked, matched = check_injection(clean)
    if blocked:
        raise SecurityException(
            f"So'rovda xavfsizlik xatosi aniqlandi. Iltimos, oddiy savol bering."
        )
    return clean
