# Instant Logos

A micro-app that finds and downloads company logos automatically.
Give it a list of companies — type them, paste them, upload a screenshot, or speak them aloud —
and it saves a PNG logo for each one to a folder on your Mac.

---

## What it looks like

```
┌─────────────────────────────────────────────┐
│  🏢 Instant Logos                           │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Apple                               │   │
│  │ Google                              │   │
│  │ Microsoft                           │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [📎 Upload screenshot or CSV]              │
│  [🎤 Record a voice note]                   │
│                                             │
│         [  ▶  Download Logos  ]             │
└─────────────────────────────────────────────┘
```

---

## Setup (one-time)

### 1. Check that Python is installed

Open **Terminal** (press `Cmd + Space`, type "Terminal", press Enter) and run:

```bash
python3 --version
```

You should see something like `Python 3.11.0`. If you see an error, download Python from
[python.org](https://www.python.org/downloads/) and install it.

### 2. Download this project

If you received this as a zip file, unzip it. If you're using git:

```bash
git clone https://github.com/vivekraju93/instant-logos.git
cd instant-logos
```

### 3. Install dependencies

In Terminal, navigate to the project folder and run:

```bash
pip3 install -r requirements.txt
```

This installs all the necessary libraries (only needed once).

### 4. Set up API keys *(optional — only for screenshot and voice features)*

> **Tip:** Typing or pasting company names works without any API keys. Skip this step if you
> only need that.

Copy the example file:

```bash
cp .env.example .env
```

Open `.env` in a text editor (e.g. TextEdit) and fill in your keys:

```
ANTHROPIC_API_KEY=sk-ant-...    ← for screenshot upload
OPENAI_API_KEY=sk-...            ← for voice recording
```

- Get an Anthropic key at [console.anthropic.com](https://console.anthropic.com)
- Get an OpenAI key at [platform.openai.com](https://platform.openai.com/api-keys)

---

## Running the app

```bash
streamlit run app.py
```

Your browser will open automatically at `http://localhost:8501`.

---

## How to use it

| Input method | How |
|---|---|
| **Type / paste** | Type company names in the text box — one per line, comma-separated, or as a bullet list |
| **Upload a file** | Upload a `.csv` or `.txt` file with company names (no API key needed) |
| **Upload a screenshot** | Upload a screenshot that contains company names — Claude reads it for you |
| **Voice note** | Click the microphone, say the company names, stop recording — Whisper transcribes it |

Then click **▶ Download Logos**. Logos are saved to `~/Desktop/Logos/` as PNG files.

### Changing the save folder

Open `app.py` in a text editor and change this line near the top:

```python
DESTINATION_FOLDER = "~/Desktop/Logos"
```

---

## Troubleshooting

**"command not found: python3"**
→ Install Python from [python.org](https://www.python.org/downloads/)

**"ModuleNotFoundError: No module named 'streamlit'"**
→ Run `pip3 install -r requirements.txt` again

**"Logo not found for Company X"**
→ Open `logo_downloader.py` and add the company to the `DOMAIN_OVERRIDES` dictionary at the top,
  e.g. `"company x": "companyx.com"`

**Screenshot / voice features say "API key not set"**
→ Make sure you created a `.env` file with valid API keys (see Setup step 4 above)

---

## How it works

1. Company names are extracted from whichever input you provide.
2. Each name is converted to a domain (e.g. "Apple" → "apple.com").
3. The logo is fetched from the [Clearbit Logo API](https://clearbit.com) (free, no account needed).
4. The PNG is saved to your chosen folder, named after the company.
