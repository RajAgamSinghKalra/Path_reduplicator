import re


def norm_name(s: str | None) -> str:
    """Lowercase and strip non alphabetic characters.

    ``None`` or empty inputs return an empty string.  Non-letter characters are
    replaced with spaces and multiple spaces are collapsed.
    """
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def norm_email(s: str | None) -> str:
    """Lowercase and apply provider-specific normalisation rules.

    For Gmail/Googlemail addresses, dots in the local part are ignored and
    anything after a plus sign is stripped.  Other providers simply get
    lowercased and trimmed.
    """
    s = (s or "").strip().lower()
    if not s:
        return ""
    local, sep, domain = s.partition("@")
    if domain in {"gmail.com", "googlemail.com"}:
        local = local.split("+")[0]
        local = local.replace(".", "")
    return f"{local}{sep}{domain}"

def norm_phone_e164(s: str | None) -> str:
    """Return a best-effort E.164 formatted phone number.

    Non-digit characters are stripped and a leading ``+`` is added when the
    number appears to include a country code.  The implementation is intentionally
    conservative – it does not attempt to guess country codes beyond recognising
    ``91`` for India.
    """
    s = (s or "").strip()
    s = re.sub(r"\D", "", s)
    if s.startswith("91") and len(s) == 12:
        s = "+" + s
    if not s.startswith("+") and len(s) >= 10:
        s = f"+{s}"  # you may plug a smarter CC inference here
    return s

def norm_govid(s: str | None) -> str:
    return (s or "").strip().upper()


_PIN_RE = re.compile(r"^[1-9]\d{5}$")


def norm_postal_code(s: str | None) -> str:
    """Return a 6 digit Indian PIN code or ``""`` when invalid.

    Whitespace is stripped and the code must match the ``XXNNNN`` format
    (first digit non-zero followed by five digits).  Inputs not meeting these
    criteria are treated as missing.
    """
    s = (s or "").strip().replace(" ", "")
    if not s:
        return ""
    return s if _PIN_RE.fullmatch(s) else ""

def canonical_identity_text(
    full_name: str | None,
    dob_iso: str | None,
    phone: str | None,
    email: str | None,
    govid: str | None,
    addr_line: str | None,
    city: str | None,
    state: str | None,
    postal_code: str | None,
    country: str | None,
) -> str:
    parts = [
        f"name:{norm_name(full_name)}",
        f"dob:{(dob_iso or '').strip()}",
        f"phone:{norm_phone_e164(phone)}",
        f"email:{norm_email(email)}",
        f"govid:{norm_govid(govid)}",
        f"addr:{(addr_line or '').lower()}",
        f"city:{(city or '').lower()}",
        f"state:{(state or '').lower()}",
        f"pc:{norm_postal_code(postal_code)}",
        f"ctry:{(country or '').upper()}",
    ]
    return " | ".join(parts)
