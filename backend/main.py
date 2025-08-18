from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # vagy ["*"] fejlesztéshez
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_openai_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ OPENAI_API_KEY nem található a .env fájlban.")
    return OpenAI(api_key=api_key)

def transcribe_audio(client: OpenAI, file_bytes: bytes, filename: str) -> str:
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=(filename, file_bytes, "audio/mpeg"),
        language="hu"
    )
    return transcript.text

def correct_transcript(client: OpenAI, raw_text: str) -> str:
    prompt = f"""Your task is to correct typos and word segmentation errors in the raw text of Hungarian sermon audio transcripts.
    Do not rephrase or rewrite the text; only fix misspellings or incorrect word splits.
    Here is the text to process:
    {raw_text}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.mp3', '.flac', '.wav', '.m4a')):
        raise HTTPException(status_code=400, detail="Nem támogatott formátum. Használj .mp3, .flac, .wav vagy .m4a formátumot.")

    file_bytes = await file.read()
    client = get_openai_client()

    try:
        raw_text = transcribe_audio(client, file_bytes, file.filename)
        corrected_text = correct_transcript(client, raw_text)
        return JSONResponse(content={
            "raw_transcript": raw_text,
            "corrected_transcript": corrected_text
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
