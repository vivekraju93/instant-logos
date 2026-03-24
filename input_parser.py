"""
input_parser.py
---------------
Handles all four ways a user can provide a list of company names:
  1. Plain text typed or pasted into the text box (including bullets and CSV)
  2. An uploaded CSV or plain-text file
  3. An uploaded screenshot (uses Claude API vision to extract company names)
  4. A voice recording (uses OpenAI Whisper API to transcribe speech)
"""

import csv
import io
import os
import re
import base64

# ── TEXT PARSING ───────────────────────────────────────────────────────────────

def parse_text(text: str) -> list[str]:
    """
    Parse a string into a list of company names.
    Handles plain text (one per line), CSV, and bullet-point formats.

    Examples:
        "Apple\\nGoogle\\nMicrosoft"   → ["Apple", "Google", "Microsoft"]
        "Apple, Google, Microsoft"      → ["Apple", "Google", "Microsoft"]
        "• Apple\\n- Google\\n* Meta"   → ["Apple", "Google", "Meta"]
        "1. Apple\\n2. Google"          → ["Apple", "Google"]
    """
    if not text or not text.strip():
        return []

    # If the text is a single line with commas and no newlines,
    # treat it as comma-separated.
    if "\n" not in text and "," in text:
        raw_items = text.split(",")
    else:
        raw_items = text.splitlines()

    companies = []
    for item in raw_items:
        # Strip whitespace.
        item = item.strip()
        if not item:
            continue

        # Remove common bullet / numbering prefixes:
        #   "• Apple"  "- Apple"  "* Apple"  "1. Apple"  "1) Apple"
        item = re.sub(r"^[\u2022\u2023\u25E6\u2043\-\*\+]\s+", "", item)  # bullet chars
        item = re.sub(r"^\d+[\.\)]\s+", "", item)                           # numbered list

        item = item.strip()
        if item:
            companies.append(item)

    # De-duplicate while preserving order.
    seen = set()
    unique = []
    for c in companies:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique.append(c)

    return unique


# ── CSV / TXT FILE PARSING ─────────────────────────────────────────────────────

def parse_file(file_bytes: bytes, filename: str) -> list[str]:
    """
    Parse an uploaded CSV or plain-text file into a list of company names.
    For CSV files the first column is used.
    For .txt files each line is treated as a company name.
    """
    text = file_bytes.decode("utf-8", errors="replace")

    if filename.lower().endswith(".csv"):
        reader = csv.reader(io.StringIO(text))
        companies = []
        for row in reader:
            if row:
                # Use the first non-empty cell in the row.
                cell = row[0].strip()
                if cell and cell.lower() != "company":  # skip header rows
                    companies.append(cell)
        return companies

    # Plain text file: parse like typed text.
    return parse_text(text)


# ── IMAGE / SCREENSHOT PARSING (Claude API) ────────────────────────────────────

def parse_image(image_bytes: bytes, media_type: str = "image/png") -> list[str]:
    """
    Use Claude's vision API to extract company names from a screenshot or image.
    Returns a list of company names.

    Requires ANTHROPIC_API_KEY to be set in the environment (or .env file).
    Raises ValueError if the API key is missing.
    Raises RuntimeError if the API call fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. "
            "Copy .env.example to .env and add your Anthropic API key."
        )

    try:
        import anthropic
    except ImportError:
        raise RuntimeError("The 'anthropic' package is not installed. Run: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)

    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Look at this image and extract every company name you can see. "
                            "Return ONLY the company names, one per line, with no extra text, "
                            "numbering, or explanation. If you see no company names, return an "
                            "empty response."
                        ),
                    },
                ],
            }
        ],
    )

    raw_text = message.content[0].text
    return parse_text(raw_text)


# ── VOICE / AUDIO PARSING (OpenAI Whisper) ────────────────────────────────────

def parse_audio(audio_bytes: bytes, filename: str = "recording.wav") -> list[str]:
    """
    Transcribe a voice recording using OpenAI Whisper, then extract company names.
    Returns a list of company names.

    Requires OPENAI_API_KEY to be set in the environment (or .env file).
    Raises ValueError if the API key is missing.
    Raises RuntimeError if the API call fails.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Copy .env.example to .env and add your OpenAI API key."
        )

    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("The 'openai' package is not installed. Run: pip install openai")

    client = OpenAI(api_key=api_key)

    # Whisper needs a file-like object with a name attribute for format detection.
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text",
    )

    # The transcript is natural speech, e.g. "Apple, Google, and Microsoft".
    # parse_text handles commas, "and", etc.
    cleaned = transcript.replace(" and ", "\n").replace(" & ", "\n")
    return parse_text(cleaned)
