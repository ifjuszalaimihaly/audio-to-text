# 📖 Sermon Transcription Project

This project consists of a **FastAPI backend** and a **Vue.js frontend** that enables users to upload audio files (e.g., sermons), automatically generate transcripts (*Speech-to-Text*), and then refine the raw text using a language model.

---

## 🚀 Features

* 🎙️ **Audio upload** (`.mp3`, `.wav`, `.flac`, `.m4a`)
* ✍️ **Transcription** with Google **Gemini** (`gemini-2.5-flash`) model
* 🧠 **Text refinement** (correcting typos, fixing word segmentation issues)
* 🌐 **Vue 3 frontend** for simple usage
* 🐳 **Docker support** for both backend and frontend

---

## 📂 Project Structure

```bash
.
├── backend/           # FastAPI application
│   ├── main.py        # FastAPI entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env           # Google API key
│
├── frontend/          # Vue 3 application
│   ├── src/
│   ├── package.json
│   └── Dockerfile
│
└── README.md
