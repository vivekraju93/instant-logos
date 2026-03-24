"""
app.py
------
Instant Logos — a simple tool to download company logos.

Run with:  streamlit run app.py
"""

import os
from dotenv import load_dotenv

# Load API keys from .env file (if it exists).
load_dotenv()

import streamlit as st
from input_parser import parse_text, parse_file, parse_image, parse_audio
from logo_downloader import download_logos

# ── CONFIGURATION ──────────────────────────────────────────────────────────────
# Change this to any folder on your Mac where you want logos saved.
DESTINATION_FOLDER = "~/Desktop/Logos"

# ── PAGE SETUP ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Instant Logos",
    page_icon="🏢",
    layout="centered",
)

# Custom CSS to keep the UI clean and minimal.
st.markdown(
    """
    <style>
        .block-container { max-width: 680px; padding-top: 3rem; }
        h1 { text-align: center; font-size: 2.2rem; }
        .subtitle { text-align: center; color: #888; margin-bottom: 2rem; }
        .stButton > button {
            width: 100%;
            background-color: #1a73e8;
            color: white;
            font-size: 1.1rem;
            padding: 0.6rem;
            border-radius: 8px;
            border: none;
        }
        .stButton > button:hover { background-color: #1558b0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.title("🏢 Instant Logos")
st.markdown(
    '<p class="subtitle">Type company names, upload a screenshot, or record your voice — '
    "then download all logos in one click.</p>",
    unsafe_allow_html=True,
)

# ── INPUT SECTION ──────────────────────────────────────────────────────────────

# 1. Text input (main input — works without any API keys)
text_input = st.text_area(
    "Type or paste company names",
    height=140,
    placeholder="Apple\nGoogle\nMicrosoft\n\n(plain text, bullets • – *, CSV, or numbered lists all work)",
    help="One company per line. Comma-separated lists also work.",
)

# Divider between text input and the alternative inputs.
st.markdown("**— or —**")

col1, col2 = st.columns(2)

# 2. File upload (screenshot or CSV)
with col1:
    uploaded_file = st.file_uploader(
        "📎 Upload a screenshot or CSV",
        type=["png", "jpg", "jpeg", "webp", "csv", "txt"],
        help="Screenshot with company names (requires Anthropic API key) or a CSV/text file.",
    )

# 3. Voice recording
with col2:
    audio_input = st.audio_input(
        "🎤 Record a voice note",
        help="Say the company names out loud (requires OpenAI API key).",
    )

# ── DESTINATION FOLDER DISPLAY ────────────────────────────────────────────────
expanded_destination = os.path.expanduser(DESTINATION_FOLDER)
st.caption(f"Logos will be saved to: `{expanded_destination}`")

# ── DOWNLOAD BUTTON ───────────────────────────────────────────────────────────
st.markdown("")  # spacing
run = st.button("▶  Download Logos")

# ── PROCESSING LOGIC ──────────────────────────────────────────────────────────
if run:
    companies = []
    error_messages = []

    # Step 1: Collect company names from whichever input was provided.

    # Text input
    if text_input and text_input.strip():
        companies += parse_text(text_input)

    # File upload
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name.lower()

        if filename.endswith((".csv", ".txt")):
            # CSV or plain text file — no API key needed.
            companies += parse_file(file_bytes, filename)
        else:
            # Image file — needs Claude API.
            with st.spinner("Reading company names from your screenshot..."):
                try:
                    # Determine MIME type from extension.
                    ext_to_mime = {
                        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                        ".png": "image/png",  ".webp": "image/webp",
                    }
                    ext = "." + filename.rsplit(".", 1)[-1]
                    media_type = ext_to_mime.get(ext, "image/png")
                    companies += parse_image(file_bytes, media_type)
                except ValueError as e:
                    error_messages.append(str(e))
                except Exception as e:
                    error_messages.append(f"Could not read screenshot: {e}")

    # Voice input
    if audio_input is not None:
        audio_bytes = audio_input.read()
        with st.spinner("Transcribing your voice note..."):
            try:
                companies += parse_audio(audio_bytes, filename="recording.wav")
            except ValueError as e:
                error_messages.append(str(e))
            except Exception as e:
                error_messages.append(f"Could not transcribe audio: {e}")

    # Show any API key / input errors.
    for msg in error_messages:
        st.error(msg)

    # De-duplicate (in case the user used multiple input methods).
    seen = set()
    unique_companies = []
    for c in companies:
        if c.strip().lower() not in seen:
            seen.add(c.strip().lower())
            unique_companies.append(c.strip())
    companies = unique_companies

    # Step 2: Validate we have something to work with.
    if not companies:
        st.warning(
            "No company names found. Please type some names, upload a file, or record a voice note."
        )
        st.stop()

    st.markdown(f"**Found {len(companies)} company name(s). Downloading logos...**")

    # Step 3: Download logos with a live progress bar.
    progress_bar = st.progress(0)
    results_placeholder = st.empty()
    results = []

    for i, company in enumerate(companies):
        # Download one logo at a time and update the progress bar.
        result_list = download_logos([company], DESTINATION_FOLDER)
        results.extend(result_list)
        progress_bar.progress((i + 1) / len(companies))

    # Step 4: Show results.
    progress_bar.empty()

    successes = [r for r in results if r["success"]]
    failures  = [r for r in results if not r["success"]]

    # Summary line.
    if successes:
        st.success(
            f"✅ Downloaded {len(successes)}/{len(results)} logo(s) to `{expanded_destination}`"
        )
    if failures:
        st.warning(f"⚠️ Could not find logos for {len(failures)} company/companies.")

    # Per-company results.
    with st.expander("See details", expanded=bool(failures)):
        for r in results:
            if r["success"]:
                st.markdown(f"✅ **{r['company']}** → `{os.path.basename(r['message'])}`")
            else:
                st.markdown(f"❌ **{r['company']}** — {r['message']}")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Logos provided by [Clearbit](https://clearbit.com). "
    "Screenshot parsing by [Claude](https://anthropic.com). "
    "Voice transcription by [OpenAI Whisper](https://openai.com)."
)
