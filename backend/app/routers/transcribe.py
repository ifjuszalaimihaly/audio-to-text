from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.clients import get_google_client
from app.services import TranscriptionService
from app.helpers import AUDIO_EXTS, guess_mime_from_filename

from app.database.connection import get_db

router = APIRouter()

# ---------------- TEXT ----------------
@router.post("/transcribe/text")
async def transcribe_text_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts a .txt file and processes it as sermon transcript text.
    """
    client = get_google_client()
    service = TranscriptionService(client, db)

    try:
        file_bytes = await file.read()
        raw_text = file_bytes.decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode uploaded .txt as UTF-8.")

    data = service.process_text(raw_text)
    return JSONResponse(content=data | {"raw_transcript": raw_text})


# ---------------- AUDIO ----------------
@router.post("/transcribe/audio")
async def transcribe_audio_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts audio files (.mp3, .wav, .m4a, .flac, .webm, .ogg) and transcribes them.
    """
    client = get_google_client()
    service = TranscriptionService(client, db)

    if not file.filename.lower().endswith(AUDIO_EXTS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(AUDIO_EXTS)}"
        )

    file_bytes = await file.read()
    mime_type = file.content_type or guess_mime_from_filename(file.filename)

    raw_text = service.transcribe_audio(file_bytes, mime_type)
    data = service.process_text(raw_text)
    return JSONResponse(content=data | {"raw_transcript": raw_text})

