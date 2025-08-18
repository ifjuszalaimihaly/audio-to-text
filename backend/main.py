from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from google.genai import types
from google import genai
from dotenv import load_dotenv
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fejlesztéshez oké; élesben szűkítsd!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_google_client() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("❌ GOOGLE_API_KEY is not found in the .env file")
    return genai.Client(api_key=api_key)

def transcribe_audio(client: genai.Client, file_bytes: bytes, mime_type: str) -> str:
    """
    Transcribes Hungarian speech from the given audio bytes using Gemini.
    """
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            "Transcribe the spoken Hungarian audio into written Hungarian text",
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
        ],
    )
    # google-genai SDK: egységesített .text property
    return resp.text

def _guess_mime_from_filename(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    return {
        "mp3": "audio/mp3",
        "wav": "audio/wav",
        "m4a": "audio/mp4",   # sok kliens így jelöli
        "flac": "audio/flac",
        "webm": "audio/webm",
        "ogg": "audio/ogg",
    }.get(ext, "application/octet-stream")

@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".mp3", ".flac", ".wav", ".m4a", ".webm", ".ogg")):
        raise HTTPException(
            status_code=400,
            detail="Nem támogatott formátum. Használj .mp3, .flac, .wav, .m4a, .webm vagy .ogg fájlt.",
        )

    file_bytes = await file.read()
    client = get_google_client()

    # MIME meghatározás: először a feltöltött tartalomtípus, különben kiterjesztés alapján
    mime_type = file.content_type or _guess_mime_from_filename(file.filename)

    try:
        raw_text = transcribe_audio(client, file_bytes, mime_type)
        return JSONResponse(content={"raw_transcript": raw_text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
