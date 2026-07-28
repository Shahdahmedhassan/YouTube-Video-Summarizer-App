"""
YouTube AI Summarizer — Local Frontend
Runs on your own machine and talks to the FastAPI backend running on Kaggle.

SETUP:
1. Run the Kaggle backend notebook first, keep it running, and copy the
   PUBLIC_URL it prints.
2. Set two environment variables before running this app (don't hardcode
   secrets in the file):

   macOS/Linux:
       export YT_SUMMARIZER_API_KEY="the same API_KEY you put in Kaggle Secrets"
       export YT_SUMMARIZER_URL="https://xxxx.ngrok-free.app"

   Windows (PowerShell):
       $env:YT_SUMMARIZER_API_KEY="the same API_KEY you put in Kaggle Secrets"
       $env:YT_SUMMARIZER_URL="https://xxxx.ngrok-free.app"

3. Run: streamlit run app.py
"""

import os
import re

import requests
import streamlit as st

# =========================================================
# Configuration — read from environment, never hardcoded
# =========================================================
API_KEY = os.environ.get("YT_SUMMARIZER_API_KEY", "")
PUBLIC_URL = os.environ.get("YT_SUMMARIZER_URL", "")

st.set_page_config(
    page_title="YouTube Summarizer",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# =========================================================
# If secrets aren't set, let the user paste them in the sidebar
# instead of crashing — friendlier for first run.
# =========================================================
with st.sidebar:
    st.header("⚙️ Backend connection")
    if not API_KEY:
        API_KEY = st.text_input("API key (from Kaggle Secrets)", type="password")
    else:
        st.caption("✅ API key loaded from environment")
    if not PUBLIC_URL:
        PUBLIC_URL = st.text_input("Public URL (from the Kaggle notebook output)")
    else:
        st.caption(f"✅ Backend URL: {PUBLIC_URL}")

# =========================================================
# Styling
# =========================================================
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background: linear-gradient(180deg, #0f1117 0%, #161925 100%); }
    .main-title { font-size: 2.1rem; font-weight: 700; color: #f5f5f7; text-align: center; margin-bottom: 0.2rem; }
    .sub-title { font-size: 0.95rem; color: #9a9ba5; text-align: center; margin-bottom: 2rem; }
    .stButton button {
        background: linear-gradient(90deg, #6c63ff, #5046e5); color: white; border: none;
        border-radius: 10px; padding: 0.7rem 1.5rem; font-weight: 600; width: 100%;
    }
    .result-card {
        background-color: #1c1f2b; border: 1px solid #2c2f3e; border-radius: 14px;
        padding: 1.6rem; margin-top: 1.5rem; color: #e4e4e9; line-height: 1.8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def extract_video_id(url: str):
    patterns = [r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", r"youtu\.be\/([0-9A-Za-z_-]{11})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def call_transcript_api(youtube_url: str):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"youtube_url": youtube_url}
    return requests.post(f"{PUBLIC_URL}/transcript", headers=headers, json=payload, timeout=60)


def call_summarize_api(youtube_url: str, transcript: str = None):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"youtube_url": youtube_url}
    if transcript:
        payload["transcript"] = transcript  # reuse it — skips a second YouTube fetch on the backend
    return requests.post(f"{PUBLIC_URL}/summarize", headers=headers, json=payload, timeout=180)


if "transcript" not in st.session_state:
    st.session_state.transcript = None
    st.session_state.transcript_for_url = None


st.markdown('<div class="main-title">🎬 YouTube Summarizer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Paste a YouTube link and get an instant summary</div>', unsafe_allow_html=True)

youtube_url = st.text_input("Video URL", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")

video_id = extract_video_id(youtube_url) if youtube_url else None
if video_id:
    st.image(f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg", use_container_width=True)

col_t, col_s = st.columns(2)
with col_t:
    get_transcript_clicked = st.button("📜 Get transcript", use_container_width=True)
with col_s:
    summarize_clicked = st.button("✨ Summarize video", use_container_width=True)

if get_transcript_clicked:
    if not API_KEY or not PUBLIC_URL:
        st.error("Please fill in the API key and backend URL in the sidebar first.")
    elif not video_id:
        st.error("This doesn't look like a valid YouTube URL.")
    else:
        with st.spinner("Fetching transcript..."):
            try:
                response = call_transcript_api(youtube_url)
                try:
                    data = response.json()
                except ValueError:
                    data = {"raw": response.text}

                if response.status_code == 200:
                    st.session_state.transcript = data.get("transcript", "")
                    st.session_state.transcript_for_url = youtube_url
                else:
                    st.session_state.transcript = None
                    st.error(data.get("message", str(data)))
            except requests.exceptions.ConnectionError:
                st.error("Could not reach the backend. Make sure the Kaggle notebook is still running and the URL is correct.")
            except requests.exceptions.Timeout:
                st.error("The request took too long. Try again.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# Show the transcript whenever we have one cached for the current URL
if st.session_state.transcript and st.session_state.transcript_for_url == youtube_url:
    word_count = len(st.session_state.transcript.split())
    with st.expander(f"📜 Full transcript ({word_count:,} words)", expanded=True):
        st.markdown(
            f'<div style="max-height:400px; overflow-y:auto; white-space:pre-wrap; '
            f'color:#e4e4e9; line-height:1.7;">{st.session_state.transcript}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇️ Download transcript (.txt)",
            st.session_state.transcript,
            file_name="transcript.txt",
            mime="text/plain",
        )

if summarize_clicked:
    if not API_KEY or not PUBLIC_URL:
        st.error("Please fill in the API key and backend URL in the sidebar first.")
    elif not youtube_url.strip():
        st.warning("Please enter a video URL first.")
    elif not video_id:
        st.error("This doesn't look like a valid YouTube URL.")
    else:
        with st.spinner("Analyzing and summarizing the video... (can take 30-90s on first request)"):
            try:
                cached_transcript = (
                    st.session_state.transcript
                    if st.session_state.transcript_for_url == youtube_url
                    else None
                )
                response = call_summarize_api(youtube_url, transcript=cached_transcript)
                try:
                    data = response.json()
                except ValueError:
                    data = {"raw": response.text}

                if response.status_code == 200:
                    summary_text = data.get("summary") or str(data)
                    st.markdown(
                        f'<div class="result-card"><b>📄 Summary</b><br><br>{summary_text}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error(data.get("message", str(data)))

            except requests.exceptions.ConnectionError:
                st.error("Could not reach the backend. Make sure the Kaggle notebook is still running and the URL is correct.")
            except requests.exceptions.Timeout:
                st.error("The request took too long. Try again — the model may still be warming up.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
