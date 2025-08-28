from google.genai import types
from sqlalchemy.orm import Session
from app.database.models import SermonFile
from google import genai
import json
import re

class TranscriptionService:
    def __init__(self, client: genai.Client, db: Session):
        """
        Service for handling Hungarian sermon audio transcription, correction,
        and Bible reference extraction with Google GenAI.
        """
        self.client = client
        self.db = db

    def transcribe_audio(self, file_bytes: bytes, mime_type: str) -> str:
        """
        Transcribes Hungarian speech from audio bytes.
        """
        resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "Transcribe the spoken Hungarian audio into written Hungarian text.",
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            ],
        )
        print(resp.text)
        return resp.text or ""

    def process_text(self, raw_text: str) -> dict:
        """
        Takes raw Hungarian sermon transcript text, returns structured JSON with corrected text,
        bible reference, sermon parts, occasion, date, and tags.
        """

        prompt = f"""
        You are given raw Hungarian sermon transcript text.

        Tasks:
        1) Correct typos and wrong word splits. Do NOT paraphrase or rewrite; keep meaning and style.
        2) Extract the Bible reference (igehely) if present. Return it in Hungarian format
        (e.g., "János 3,16" or "Zsoltárok 23,1-4"). If no reference, return "Nincs igehely".
        3) Split the sermon text into three parts (if identifiable):
        - "introduction" (bevezetés)
        - "scripture_reading" (textus felolvasása)
        - "body" (prédikáció törzsszövege).
        If a part is missing, return an empty string.
        4) Identify the occasion when the sermon was delivered (e.g. "Vasárnapi istentisztelet",
        "Esküvői szertartás", "Temetés", "Konfirmáció", etc.).
        If not clear, return "Ismeretlen alkalom".
        5) Extract the date if explicitly mentioned (format: "YYYY. hónap nap." e.g. "2024. június 16.").
        If no date found, return "Nincs dátum".
        6) Generate exactly 20 descriptive tags (in Hungarian, lowercase, single words or short phrases)
        about the sermon content, separated into a JSON array.
        Examples: ["hit", "szeretet", "megváltás", ...].

        Output:
        Return ONLY a single JSON object with exactly these keys:
        {{
        "corrected_transcript": "<string>",
        "bible_reference": "<string>",
        "introduction": "<string>",
        "scripture_reading": "<string>",
        "body": "<string>",
        "occasion": "<string>",
        "date": "<string>",
        "tags": ["<string>", "<string>", "..."]  # exactly 20 elements
        }}

        Do not include any explanations or extra fields.

        Text to process:
        {raw_text}
        """.strip()

        resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
        )

        raw_out = (resp.text or "").strip()
        data = self._parse_strict_json(raw_out)
        if not isinstance(data, dict):
            raise ValueError("Model did not return a JSON object.")

        # defaults
        data.setdefault("corrected_transcript", "")
        data.setdefault("bible_reference", "Nincs igehely")
        data.setdefault("introduction", "")
        data.setdefault("scripture_reading", "")
        data.setdefault("body", "")
        data.setdefault("occasion", "Ismeretlen alkalom")
        data.setdefault("date", "Nincs dátum")
        data.setdefault("tags", [])

        # always include original raw_text
        data["raw_text"] = raw_text
        sermon_file = SermonFile(
            source_type="text",
            original_filename=None,
            preacher=None,
            occasion=data["occasion"],
            sermon_date=None,
            bible_ref=data["bible_reference"],
            tags=None,
            raw_text=raw_text,
            corrected_text=data["corrected_transcript"]
        )
        print(type(self.db))
        self.db.add(sermon_file)
        self.db.commit()

        return data



    def _parse_strict_json(self, s: str) -> dict:
            """
            Tries to parse JSON even if the model wrapped it in Markdown code fences.
            """
            # Strip markdown code fences if present
            fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, flags=re.S)
            if fence_match:
                s = fence_match.group(1)
            return json.loads(s)