# 🎬 YouTube AI Summarizer

Paste any YouTube video link and get its full transcript plus a clean, AI-generated summary — no need to sit through the whole video to get the key points.

---

## ✨ What it does

- 📥 Automatically fetches the transcript of any YouTube video (no manual copy-pasting)
- 📜 Lets you view/download the **full transcript** on its own
- 🧩 Splits long transcripts into sentence-aware chunks so no sentence gets cut mid-way
- 🧠 Summarizes each chunk using a BART-based transformer model, with dynamic length control and beam search for better quality
- 🔁 Re-summarizes the combined result (hierarchical summarization) so the final summary reads as one coherent piece instead of stitched-together fragments
- 🖥️ Simple, clean web interface built with Streamlit

---

## 🏗️ How it's built (architecture)

This project is split into two parts that talk to each other over HTTP:

```
┌─────────────────────────┐        HTTPS (via ngrok)        ┌──────────────────────────────┐
│   Streamlit Frontend     │ ───────────────────────────────▶│   FastAPI Backend             │
│   (runs on your machine) │◀─────────────────────────────── │   (runs on Kaggle, free GPU)  │
└─────────────────────────┘                                  └──────────────────────────────┘
                                                                        │
                                                                        ▼
                                                      facebook/bart-large-cnn (Hugging Face)
```

**Why split it this way?** Running a full transformer model (BART) requires more RAM/GPU than most free hosting tiers provide. Kaggle gives free GPU access, so the heavy lifting (model inference) happens there, while the frontend stays lightweight and runs locally.

### Backend (`youtube_summarizer_backend.ipynb`)
Runs as a Kaggle Notebook. It:
1. Loads `facebook/bart-large-cnn` on Kaggle's free GPU
2. Fetches the video transcript via `youtube-transcript-api` (with optional proxy support to avoid YouTube's cloud-IP blocking)
3. Cleans the transcript (removes duplicate/repeated words common in auto-generated captions)
4. Splits it into token-aware chunks along sentence boundaries (via NLTK)
5. Summarizes each chunk with beam search and dynamic output length
6. Re-summarizes the combined result if it's still long, for a coherent final summary
7. Serves everything through a FastAPI app with two endpoints, exposed publicly via **ngrok**

### Frontend (`app.py`)
A Streamlit app that runs on your own machine. It sends the video URL to the backend's API and displays the transcript and/or summary it gets back.

---

## 🔌 API Endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `/transcript` | `POST` | Fetches + cleans the transcript only (fast, no GPU used) |
| `/summarize` | `POST` | Returns the AI-generated summary. Accepts an optional `transcript` field to reuse an already-fetched transcript instead of re-fetching it |

Both endpoints require an `Authorization: Bearer <API_KEY>` header.

---

## 🛠️ Tech Stack

- **Python**
- **Streamlit** — frontend UI
- **FastAPI** + **Uvicorn** — backend API server
- **Hugging Face Transformers** (`facebook/bart-large-cnn`) — summarization model
- **NLTK** — sentence-aware text chunking
- **youtube-transcript-api** — transcript extraction
- **pyngrok** — exposes the Kaggle-hosted backend publicly
- **Kaggle Notebooks** — free GPU compute for running the model

---

## 🚀 Getting Started

### 1. Run the backend on Kaggle
1. Upload `youtube_summarizer_backend.ipynb` to [Kaggle](https://www.kaggle.com/code) and enable a GPU accelerator (`Settings → Accelerator → GPU`).
2. Add these secrets under `Add-ons → Secrets`:
   - `NGROK_TOKEN` — get a free one at [ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken)
   - `API_KEY` — any password you choose, used to protect the API
   - *(optional, recommended)* `WEBSHARE_USERNAME` / `WEBSHARE_PASSWORD` — a residential proxy from [Webshare](https://www.webshare.io/) so YouTube doesn't block requests coming from Kaggle's cloud IPs
3. Run all cells from top to bottom and **keep the session running** — the last cell prints a public URL (e.g. `https://xxxx.ngrok-free.app`). Copy it.

### 2. Run the frontend locally
```bash
git clone <this-repo-url>
cd youtube-ai-summarizer
pip install -r requirements.txt
streamlit run app.py
```
When the app opens in your browser, enter the **API key** and the **public URL** from step 1 in the sidebar, then paste any YouTube link and click **Summarize video** or **Get transcript**.

> ⚠️ Both the Kaggle notebook session and your local `streamlit run` process need to stay running at the same time for the app to work.

---

## ⚠️ Known Limitations

- Videos need English captions (auto-generated or manual) — the model itself is English-only.
- Very long videos are capped by `MAX_CHUNKS` in the notebook to keep processing times reasonable; this can be raised if you have more GPU time to spare.
- Kaggle's free GPU quota is ~30 hours/week, and sessions disconnect after periods of inactivity — this setup is best for demos and personal use rather than an always-on production service.
- Without a proxy, YouTube may occasionally block requests coming from cloud IPs (including Kaggle's).
