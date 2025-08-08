from rapidfuzz.distance import JaroWinkler

def jw(a, b):
    a = (a or "").lower().strip()
    b = (b or "").lower().strip()
    if not a or not b:
        return 0.0
    return JaroWinkler.similarity(a, b) / 100.0


def phone_match(a, b):
    return 1.0 if a and b and a == b else 0.0


def email_match(a, b):
    return 1.0 if a and b and a == b else 0.0


def govid_match(a, b):
    return 1.0 if a and b and a == b else 0.0


def addr_overlap(a, b):
    """Simple Jaccard overlap of whitespace tokens for address lines."""
    set_a = set((a or "").lower().split())
    set_b = set((b or "").lower().split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

def feature_row(query, candidate, vdist):
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
    ]
