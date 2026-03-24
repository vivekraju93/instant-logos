"""
app.py
------
Instant Logos — download company logos in one click.

Run with:  streamlit run app.py
"""

import io
import zipfile
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from input_parser import parse_text
from logo_downloader import download_logos

# ── PAGE SETUP ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Instant Logos",
    page_icon=None,
    layout="centered",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .block-container {
            max-width: 640px;
            padding-top: 4rem;
            padding-bottom: 4rem;
        }

        /* Header */
        .app-title {
            font-size: 2rem;
            font-weight: 600;
            color: #111;
            text-align: center;
            letter-spacing: -0.5px;
            margin-bottom: 0.25rem;
        }
        .app-subtitle {
            font-size: 0.95rem;
            color: #888;
            text-align: center;
            margin-bottom: 2.5rem;
        }

        /* Text area */
        textarea {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.95rem !important;
            border-radius: 10px !important;
            border: 1.5px solid #e5e5e5 !important;
            background: #fafafa !important;
            padding: 0.75rem !important;
            color: #111 !important;
        }
        textarea:focus {
            border-color: #6366f1 !important;
            background: #fff !important;
            box-shadow: 0 0 0 3px rgba(99,102,241,0.08) !important;
        }

        /* Primary button */
        .stButton > button {
            width: 100%;
            background: #6366f1;
            color: white;
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
            font-weight: 500;
            padding: 0.65rem 1rem;
            border-radius: 10px;
            border: none;
            margin-top: 0.5rem;
            transition: background 0.15s ease;
        }
        .stButton > button:hover {
            background: #4f46e5;
            border: none;
        }
        .stButton > button:active {
            background: #4338ca;
        }

        /* Download buttons */
        .stDownloadButton > button {
            width: 100%;
            background: transparent;
            color: #6366f1;
            font-family: 'Inter', sans-serif;
            font-size: 0.8rem;
            font-weight: 500;
            padding: 0.4rem 0.75rem;
            border-radius: 8px;
            border: 1.5px solid #e5e5e5;
            margin-top: 0.4rem;
            transition: all 0.15s ease;
        }
        .stDownloadButton > button:hover {
            border-color: #6366f1;
            color: #4f46e5;
            background: rgba(99,102,241,0.04);
        }

        /* Logo card */
        .logo-card {
            background: #fff;
            border: 1.5px solid #f0f0f0;
            border-radius: 12px;
            padding: 1.25rem 1rem 0.75rem;
            text-align: center;
        }
        .logo-name {
            font-size: 0.8rem;
            font-weight: 500;
            color: #555;
            margin-top: 0.5rem;
        }
        .logo-error {
            background: #fff8f8;
            border: 1.5px solid #fde8e8;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            font-size: 0.8rem;
            color: #e53e3e;
        }

        /* ZIP section */
        .zip-row {
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid #f0f0f0;
        }

        /* Footer */
        .app-footer {
            text-align: center;
            font-size: 0.75rem;
            color: #bbb;
            margin-top: 3rem;
        }
        .app-footer a { color: #bbb; text-decoration: none; }
        .app-footer a:hover { color: #888; }

        /* Hide Streamlit chrome */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="app-title">Instant Logos</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="app-subtitle">Type company names and download their logos instantly.</p>',
    unsafe_allow_html=True,
)

# ── INPUT ──────────────────────────────────────────────────────────────────────
text_input = st.text_area(
    label="Companies",
    label_visibility="collapsed",
    height=150,
    placeholder="Apple\nGoogle\nMicrosoft",
)

run = st.button("Get Logos")

# ── PROCESSING ────────────────────────────────────────────────────────────────
if run:
    companies = parse_text(text_input) if text_input and text_input.strip() else []

    if not companies:
        st.warning("Please enter at least one company name.")
        st.stop()

    with st.spinner("Fetching logos…"):
        results = download_logos(companies)

    successes = [r for r in results if r["success"]]
    failures  = [r for r in results if not r["success"]]

    # ── LOGO GRID ─────────────────────────────────────────────────────────────
    if successes:
        cols = st.columns(3)
        for i, r in enumerate(successes):
            with cols[i % 3]:
                st.markdown('<div class="logo-card">', unsafe_allow_html=True)
                st.image(r["data"], use_container_width=True)
                st.markdown(f'<p class="logo-name">{r["company"]}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.download_button(
                    label="Download",
                    data=r["data"],
                    file_name=r["filename"],
                    mime="image/png",
                    key=f"dl_{i}",
                )

    # ── FAILURES ──────────────────────────────────────────────────────────────
    if failures:
        st.markdown("")
        for r in failures:
            st.markdown(
                f'<div class="logo-error">Could not find logo for <strong>{r["company"]}</strong></div>',
                unsafe_allow_html=True,
            )
            st.markdown("")

    # ── ZIP DOWNLOAD ──────────────────────────────────────────────────────────
    if len(successes) > 1:
        st.markdown('<div class="zip-row">', unsafe_allow_html=True)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in successes:
                zf.writestr(r["filename"], r["data"])
        buf.seek(0)
        st.download_button(
            label=f"Download all {len(successes)} logos as ZIP",
            data=buf,
            file_name="logos.zip",
            mime="application/zip",
            key="dl_zip",
        )
        st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(
    '<p class="app-footer">Logos by <a href="https://logo.dev" target="_blank">Logo.dev</a></p>',
    unsafe_allow_html=True,
)
