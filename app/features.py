from rapidfuzz.distance import JaroWinkler
import math

def jw(a,b):
    a = (a or "").lower().strip()
    b = (b or "").lower().strip()
    if not a or not b: return 0.0
    return JaroWinkler.similarity(a,b)/100.0

def phone_match(a,b): return 1.0 if a and b and a==b else 0.0
def email_match(a,b): return 1.0 if a and b and a==b else 0.0
def govid_match(a,b): return 1.0 if a and b and a==b else 0.0

def feature_row(query, candidate, vdist):
    # Convert distance (0..2 for cosine-like) to similarity-ish
    vsim = 1.0/(1.0 + vdist)
    return [
        vsim,
        jw(query.get("full_name"), candidate.get("full_name")),
        phone_match(query.get("phone_e164"), candidate.get("phone_e164")),
        email_match(query.get("email_norm"), candidate.get("email_norm")),
        govid_match(query.get("gov_id_norm"), candidate.get("gov_id_norm")),
        jw(query.get("city"), candidate.get("city")),
        jw(query.get("state"), candidate.get("state")),
    ]
