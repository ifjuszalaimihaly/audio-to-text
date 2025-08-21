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
    allow_origins=["*"],  # OK for development; restrict in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Clients --------------------

def get_google_client() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("❌ GOOGLE_API_KEY is not found in the .env file")
    return genai.Client(api_key=api_key)

# -------------------- Core Tasks --------------------

def transcribe_audio(client: genai.Client, file_bytes: bytes, mime_type: str) -> str:
    """
    Transcribes Hungarian speech from the given audio bytes using Gemini.
    """
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            "Transcribe the spoken Hungarian audio into written Hungarian text.",
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
        ],
    )
    return resp.text or ""


def correct_transcript(client: genai.Client, raw_text: str) -> str:
    prompt = f"""
    Your task is to correct typos and word segmentation errors in the raw text of Hungarian sermon audio transcripts.
    Do not rephrase or rewrite the text; only fix misspellings or incorrect word splits, or add spaces between the words if needed.

    Here is the text to process:
    {raw_text}
    """

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
    )
    return (resp.text or "").strip()


def extract_bible_reference(client: genai.Client, transcript: str) -> str:
    """
    Extracts the Bible reference (igehely) mentioned in a Hungarian sermon transcript.
    Returns only the reference in Hungarian (e.g., 'János 3,16'), without explanations.
    """
    prompt = f"""
    Your task is to extract the Bible reference from the following Hungarian sermon transcript.
    Return only the reference in Hungarian format (e.g., 'János 3,16' or 'Zsoltárok 23,1-4').
    If there is no specific reference, reply with: 'Nincs igehely'.

    Transcript:
    {transcript}
    """

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
    )
    return (resp.text or "").strip()

# -------------------- Helpers --------------------

AUDIO_EXTS = (".mp3", ".flac", ".wav", ".m4a", ".webm", ".ogg")


def _guess_mime_from_filename(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    return {
        "mp3": "audio/mp3",
        "wav": "audio/wav",
        "m4a": "audio/mp4",   # many clients label it this way
        "flac": "audio/flac",
        "webm": "audio/webm",
        "ogg": "audio/ogg",
        "txt": "text/plain",
    }.get(ext, "application/octet-stream")


def _is_text_upload(file: UploadFile) -> bool:
    ct = (file.content_type or "").lower()
    return ct == "text/plain" or file.filename.lower().endswith(".txt")

# -------------------- Endpoint --------------------

@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    client = get_google_client()
    file_bytes = await file.read()

    # If TXT was uploaded, skip transcription and treat the content as raw text
    if _is_text_upload(file):
        try:
            raw_text = file_bytes.decode("utf-8", errors="replace")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode uploaded .txt as UTF-8.")
    else:
        # Validate audio extensions
        if not file.filename.lower().endswith(AUDIO_EXTS):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported file type. Use .txt for text, or one of .mp3, .flac, .wav, .m4a, .webm, .ogg for audio."
                ),
            )
        # MIME detection: prefer provided content_type, else guess from filename
        mime_type = file.content_type or _guess_mime_from_filename(file.filename)
        raw_text = transcribe_audio(client, file_bytes, mime_type)

    # Common post-processing path (both txt and audio)
    corrected_text = correct_transcript(client, raw_text)
    bible_reference = extract_bible_reference(client, corrected_text)

    return JSONResponse(
        content={
            "raw_transcript": raw_text,
            "corrected_transcript": corrected_text,
            "bible_reference": bible_reference,
        }
    )
