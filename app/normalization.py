import re

def norm_name(s: str) -> str:
    if not s: return ""
    s = s.lower()
    s = re.sub(r"[^a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def norm_email(s: str) -> str:
    """Lowercase and apply provider-specific normalisation rules.

    For Gmail/Googlemail addresses, dots in the local part are ignored and
    anything after a plus sign is stripped.  Other providers simply get
    lowercased and trimmed.
    """
    s = (s or "").strip().lower()
    if not s:
        return ""
    local, sep, domain = s.partition("@")
    if domain in ("gmail.com", "googlemail.com"):
        local = local.split("+")[0]
        local = local.replace(".", "")
    return f"{local}{sep}{domain}"

def norm_phone_e164(s: str) -> str:
    # Expect inputs like "+91..." or "91..." etc; normalize to +CC format where you can.
    s = (s or "").strip()
    s = re.sub(r"\D", "", s)
    if s.startswith("91") and len(s) == 12: s = "+" + s
    if not s.startswith("+") and len(s) >= 10:
        s = "+{}".format(s)  # you may plug a smarter CC inference here
    return s

def norm_govid(s: str) -> str:
    return (s or "").strip().upper()

def canonical_identity_text(full_name, dob_iso, phone, email, govid, addr_line, city, state, postal_code, country):
    parts = [
        f"name:{norm_name(full_name)}",
        f"dob:{(dob_iso or '').strip()}",
        f"phone:{norm_phone_e164(phone)}",
        f"email:{norm_email(email)}",
        f"govid:{norm_govid(govid)}",
        f"addr:{(addr_line or '').lower()}",
        f"city:{(city or '').lower()}",
        f"state:{(state or '').lower()}",
        f"pc:{(postal_code or '').lower()}",
        f"ctry:{(country or '').upper()}",
    ]
    return " | ".join(parts)
