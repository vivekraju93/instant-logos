"""
logo_downloader.py
------------------
Downloads company logos using the Clearbit Logo API (free, no API key needed).
Given a company name, it guesses the company's domain and fetches the logo PNG.
"""

import os
import re
import requests

# ── TIMEOUT ────────────────────────────────────────────────────────────────────
# How many seconds to wait for a logo download before giving up.
REQUEST_TIMEOUT = 10

# ── LOGO.DEV API KEY ───────────────────────────────────────────────────────────
# Get a free key at https://logo.dev — add it to your .env file as LOGO_DEV_API_KEY.
LOGO_DEV_API_KEY = os.getenv("LOGO_DEV_API_KEY", "")

# ── DOMAIN OVERRIDES ───────────────────────────────────────────────────────────
# The automatic domain-guesser works for most companies, but some names are tricky.
# If a company logo isn't found, add it here in lowercase:  "company name": "domain.com"
DOMAIN_OVERRIDES = {
    "goldman sachs": "goldmansachs.com",
    "at&t": "att.com",
    "3m": "3m.com",
    "general electric": "ge.com",
    "general motors": "gm.com",
    "johnson & johnson": "jnj.com",
    "procter & gamble": "pg.com",
    "coca-cola": "coca-cola.com",
    "the coca-cola company": "coca-cola.com",
    "hp": "hp.com",
    "hewlett packard": "hp.com",
    "jpmorgan chase": "jpmorganchase.com",
    "jp morgan": "jpmorgan.com",
    "bank of america": "bankofamerica.com",
    "wells fargo": "wellsfargo.com",
    "morgan stanley": "morganstanley.com",
    "mckinsey": "mckinsey.com",
    "mckinsey & company": "mckinsey.com",
    "booz allen hamilton": "boozallen.com",
    "pwc": "pwc.com",
    "pricewaterhousecoopers": "pwc.com",
    "kpmg": "kpmg.com",
    "ernst & young": "ey.com",
    "ey": "ey.com",
    "deloitte": "deloitte.com",
    "accenture": "accenture.com",
    "l'oreal": "loreal.com",
    "loreal": "loreal.com",
    "lvmh": "lvmh.com",
    "berkshire hathaway": "berkshirehathaway.com",
    "s&p global": "spglobal.com",
    "t-mobile": "t-mobile.com",
    "verizon": "verizon.com",
    "comcast": "comcast.com",
    "fox": "fox.com",
    "disney": "disney.com",
    "warner bros": "warnerbros.com",
    "warner brothers": "warnerbros.com",
}

# ── LEGAL SUFFIXES TO STRIP ────────────────────────────────────────────────────
# These words are removed before guessing the domain.
LEGAL_SUFFIXES = [
    r"\binc\.?\b", r"\bcorp\.?\b", r"\bltd\.?\b", r"\bllc\.?\b",
    r"\bco\.?\b",  r"\bplc\.?\b",  r"\bgroup\b", r"\bholdings\b",
    r"\blimited\b", r"\bcorporation\b", r"\bcompany\b",
]


def company_to_domain(company_name: str) -> str:
    """
    Convert a company name to a best-guess domain.
    e.g. "Apple"        → "apple.com"
         "Goldman Sachs" → "goldmansachs.com"
    """
    # Step 1: Check the override dictionary first (case-insensitive).
    key = company_name.strip().lower()
    if key in DOMAIN_OVERRIDES:
        return DOMAIN_OVERRIDES[key]

    # Step 2: Apply mechanical rules.
    domain = company_name.lower()

    # Remove legal suffixes.
    for suffix in LEGAL_SUFFIXES:
        domain = re.sub(suffix, "", domain, flags=re.IGNORECASE)

    # Remove all characters that aren't letters, digits, or hyphens.
    domain = re.sub(r"[^a-z0-9\-]", "", domain)

    # Remove leading/trailing hyphens.
    domain = domain.strip("-")

    # Append .com
    return domain + ".com"


def sanitize_filename(name: str) -> str:
    """Remove characters that are not allowed in filenames."""
    return re.sub(r'[\\/:*?"<>|]', "-", name).strip()


def download_logo(company_name: str, destination_folder: str) -> tuple[bool, str]:
    """
    Download the logo for a company and save it as a PNG file.

    Returns:
        (True, filepath)   on success
        (False, error_msg) on failure
    """
    domain = company_to_domain(company_name)
    url = f"https://img.logo.dev/{domain}?token={LOGO_DEV_API_KEY}&size=200&format=png"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT, stream=True)
    except requests.ConnectionError:
        return False, "Could not connect to logo service. Check your LOGO_DEV_API_KEY in .env."
    except requests.Timeout:
        return False, f"Timed out trying to fetch logo (domain tried: {domain})."
    except requests.RequestException as e:
        return False, f"Network error: {e}"

    if response.status_code == 404:
        return False, (
            f"Logo not found (tried domain: {domain}). "
            "You can add a manual override in logo_downloader.py → DOMAIN_OVERRIDES."
        )
    if response.status_code != 200:
        return False, f"Unexpected server response: HTTP {response.status_code} for {url}"

    # Build the output file path.
    filename = sanitize_filename(company_name) + ".png"
    filepath = os.path.join(destination_folder, filename)

    # Write the image bytes to disk.
    with open(filepath, "wb") as f:
        f.write(response.content)

    return True, filepath


def download_logos(company_names: list[str], destination_folder: str) -> list[dict]:
    """
    Download logos for a list of companies.

    Returns a list of result dicts:
        {"company": str, "success": bool, "message": str}
    """
    # Expand ~ to the full home directory path and create the folder if needed.
    destination_folder = os.path.expanduser(destination_folder)
    os.makedirs(destination_folder, exist_ok=True)

    results = []
    for name in company_names:
        name = name.strip()
        if not name:
            continue
        success, message = download_logo(name, destination_folder)
        results.append({"company": name, "success": success, "message": message})

    return results
