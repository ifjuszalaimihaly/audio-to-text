from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.clients import get_google_client
from app.setvices.transcribe_service import TranscribeService
from app.setvices.embedding_service import EmbeddingService
from app.database.models import SermonFile, SermonChunk
from app.helpers import AUDIO_EXTS, guess_mime_from_filename
import time

from app.database.connection import get_db

router = APIRouter()

# ---------------- TEXT ----------------
@router.post("/transcribe/text")
async def transcribe_text_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts a .txt file and processes it as sermon transcript text.
    """
    client = get_google_client()
    transcribe_service = TranscribeService(client)
    embedding_service = EmbeddingService(client)


    try:
        file_bytes = await file.read()
        raw_text = file_bytes.decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode uploaded .txt as UTF-8.")

    data = transcribe_service.process_text(raw_text, type = "text")
    chunks = embedding_service.chunk_corrected_text(data["corrected_transcript"])




    sermon_file = SermonFile(
        source_type="text",
        original_filename = None,
        preacher = None,
        occasion = data["occasion"],
        sermon_date = data["date"],
        bible_ref = data["bible_reference"],
        tags = data["tags"],
        raw_text = raw_text,
        scripture_reading = data["scripture_reading"],
        introduction = data["introduction"],
        body = data["body"],
        corrected_text = data["corrected_transcript"]
    )
    db.add(sermon_file)
    db.flush()
    for index, chunk in enumerate(chunks):

        time.sleep(1)
        chunk["embedding"] = embedding_service.embed_text(
            chunk["text"], 
            task_type="RETRIEVAL_DOCUMENT"
        )
        sermon_chunk = SermonChunk(
            file_id = sermon_file.id,
            chunk_index = index,
            char_start = chunk["start"],
            char_end = chunk["end"],
            text_value = data["corrected_transcript"],
            embedding = chunk["embedding"]
        )
        db.add(sermon_chunk)
    db.commit()
    return JSONResponse(content=data | {"raw_transcript": raw_text})


# ---------------- AUDIO ----------------
@router.post("/transcribe/audio")
async def transcribe_audio_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts audio files (.mp3, .wav, .m4a, .flac, .webm, .ogg) and transcribes them.
    """
    client = get_google_client()
    transcribe_service = TranscribeService(client)

    if not file.filename.lower().endswith(AUDIO_EXTS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(AUDIO_EXTS)}"
        )

    file_bytes = await file.read()
    mime_type = file.content_type or guess_mime_from_filename(file.filename)

    raw_text = transcribe_service.transcribe_audio(file_bytes, mime_type)
    data = transcribe_service.process_text(raw_text, type = "audio")
    sermon_file = SermonFile(
        source_type="text",
        original_filename=None,
        preacher=None,
        occasion=data["occasion"],
        sermon_date=data["date"],
        bible_ref=data["bible_reference"],
        tags=data["tags"],
        raw_text=raw_text,
        scripture_reading=data["scripture_reading"],
        introduction=data["introduction"],
        body=data["body"],
        corrected_text=data["corrected_transcript"]
    )
    db.add(sermon_file)
    db.commit()
    return JSONResponse(content=data | {"raw_transcript": raw_text})

