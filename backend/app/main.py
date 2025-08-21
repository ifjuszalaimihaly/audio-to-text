from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.transcribe import router as transcribe_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # just for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load routers
app.include_router(transcribe_router, prefix="", tags=["transcription"])

# healthcheck
@app.get("/health")
def health():
    return {"status": "ok"}
