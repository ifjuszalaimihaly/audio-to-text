# 📖 Sermon Transcription Project

This project consists of a **FastAPI backend** and a **Vue.js frontend** that enables users to upload audio files (e.g., sermons), automatically generate transcripts (*Speech-to-Text*), and then refine the raw text using a language model.

---

## 🚀 Features

* 🎙️ **Audio upload** (`.mp3`, `.wav`, `.flac`, `.m4a`)
* ✍️ **Transcription** with OpenAI `gpt-4o-transcribe` model
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
│   └── .env           # OpenAI API key
│
├── frontend/          # Vue 3 application
│   ├── src/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
│
└── README.md
```

---

## 🔧 Setup

### 1. OpenAI API Key

In `backend/.env`:

```env
OPENAI_API_KEY=your_api_key_here
```

### 2. Run Backend with Docker

```bash
cd backend
docker build -t transcriber-backend .
docker run -p 8000:8000 --env-file .env transcriber-backend
```

👉 The backend will then be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Run Frontend with Docker

```bash
cd frontend
docker build -t transcriber-frontend .
docker run -p 8080:80 transcriber-frontend
```

👉 The frontend will then be available at: [http://localhost:8080](http://localhost:8080)

---

## 🐳 Docker Compose (optional)

To start both frontend and backend together, create a `docker-compose.yml`:

```yaml
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env

  frontend:
    build: ./frontend
    ports:
      - "8080:80"
```

Run:

```bash
docker-compose up --build
```

---

## ⚙️ Usage

1. Open the frontend: 👉 [http://localhost:8080](http://localhost:8080)
2. Upload an audio file (`.mp3`, `.wav`, `.flac`, `.m4a`)
3. The system will generate both the **raw transcript** and the **corrected transcript**

---

## 📌 Technologies

* **Backend**: [FastAPI](https://fastapi.tiangolo.com/), OpenAI API, [Uvicorn](https://www.uvicorn.org/)
* **Frontend**: [Vue 3](https://vuejs.org/), [Axios](https://axios-http.com/), TailwindCSS (optional)
* **Deployment**: Docker

---

## 📝 Note

This project is a **prototype / proof-of-concept** that demonstrates how to integrate OpenAI Speech-to-Text and language models into a full-stack web application.
