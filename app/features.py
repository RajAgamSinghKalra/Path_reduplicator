from typing import Mapping

from rapidfuzz.distance import JaroWinkler


def jw(a: str | None, b: str | None) -> float:
    """Return the normalised Jaro–Winkler similarity.

    ``rapidfuzz`` offers a ``normalized_similarity`` helper that already
    returns a value in the 0..1 range, so we use that instead of dividing the
    ``similarity`` score by 100.  ``None`` and empty inputs simply produce a
    score of ``0.0``.
    """
    a = (a or "").lower().strip()
    b = (b or "").lower().strip()
    if not a or not b:
        return 0.0
    return JaroWinkler.normalized_similarity(a, b)


def exact_match(a: str | None, b: str | None) -> float:
    """Return ``1.0`` when both values are non-empty and equal."""
    return 1.0 if a and b and a == b else 0.0


def phone_match(a: str | None, b: str | None) -> float:
    return exact_match(a, b)


def email_match(a: str | None, b: str | None) -> float:
    return exact_match(a, b)


def govid_match(a: str | None, b: str | None) -> float:
    return exact_match(a, b)


def addr_overlap(a: str | None, b: str | None) -> float:
    """Simple Jaccard overlap of whitespace tokens for address lines."""
    set_a = set((a or "").lower().split())
    set_b = set((b or "").lower().split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def pincode_match(a: str | None, b: str | None) -> float:
    """Exact match gives 1.0; first five digits match gives 0.5."""
    a = (a or "").strip()
    b = (b or "").strip()
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if len(a) == 6 and len(b) == 6 and a[:5] == b[:5]:
        return 0.5
    return 0.0


def dob_delta_days(a: str | None, b: str | None) -> float:
    """Absolute difference in days between two ISO date strings."""
    if not a or not b:
        return 9999.0
    from datetime import date

    def to_date(x: str | date) -> date:
        return x if isinstance(x, date) else date.fromisoformat(x)

    da = to_date(a)
    db = to_date(b)
    return abs((da - db).days)

def feature_row(
    query: Mapping[str, object],
    candidate: Mapping[str, object],
    vdist: float,
) -> list[float]:
    """Generate feature vector for ranking."""
    vsim = 1.0 / (1.0 + vdist)  # distance to similarity-ish
    return [
        vsim,
        jw(query.get("full_name"), candidate.get("full_name")),
        phone_match(query.get("phone_e164"), candidate.get("phone_e164")),
        email_match(query.get("email_norm"), candidate.get("email_norm")),
        govid_match(query.get("gov_id_norm"), candidate.get("gov_id_norm")),
        addr_overlap(query.get("addr_line"), candidate.get("addr_line")),
        jw(query.get("city"), candidate.get("city")),
        jw(query.get("state"), candidate.get("state")),
        pincode_match(query.get("postal_code"), candidate.get("postal_code")),
        dob_delta_days(query.get("dob"), candidate.get("dob")),
    ]
