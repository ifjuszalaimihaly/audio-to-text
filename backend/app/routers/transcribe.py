from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from app.clients import get_google_client
from app.services import transcribe_audio, correct_transcript, extract_bible_reference
from app.helpers import AUDIO_EXTS, guess_mime_from_filename, is_text_upload

router = APIRouter()

@router.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    client = get_google_client()
    file_bytes = await file.read()

    # TXT esetén kihagyjuk a transzkripciót
    if is_text_upload(file):
        try:
            raw_text = file_bytes.decode("utf-8", errors="replace")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode uploaded .txt as UTF-8.")
    else:
        if not file.filename.lower().endswith(AUDIO_EXTS):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Use .txt or one of .mp3, .flac, .wav, .m4a, .webm, .ogg.",
            )
        mime_type = file.content_type or guess_mime_from_filename(file.filename)
        raw_text = transcribe_audio(client, file_bytes, mime_type)

    corrected_text = correct_transcript(client, raw_text)
    bible_reference = extract_bible_reference(client, corrected_text)

    return JSONResponse(
        content={
            "raw_transcript": raw_text,
            "corrected_transcript": corrected_text,
            "bible_reference": bible_reference,
        }
    )
