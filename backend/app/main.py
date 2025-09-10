from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.transcribe_router import router as transcribe_router
from app.routers.search_router import router as search_router

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
app.include_router(search_router, prefix="", tags=["search"])


# healthcheck
@app.get("/health")
def health():
    return {"status": "ok"}
