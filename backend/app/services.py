from google.genai import types
from google import genai
import json
import re

class TranscriptionService:
    def __init__(self, client: genai.Client):
        """
        Service for handling Hungarian sermon audio transcription, correction,
        and Bible reference extraction with Google GenAI.
        """
        self.client = client

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
        Takes raw Hungarian transcript text, returns JSON with:
        - raw transcript
        - corrected transcript
        - bible reference
        - introduction
        - scripture_reading
        - body

        Returns a dict:
        {
            "raw_transcript": "<string>",
            "corrected_transcript": "<string>",
            "bible_reference": "<string or 'Nincs igehely'>",
            "introduction": "<string>",
            "scripture_reading": "<string>",
            "body": "<string>"
        }
        """
        prompt = f"""
        You are given raw Hungarian sermon transcript text.

        Tasks:
        1) Correct typos and wrong word splits. Do NOT paraphrase or rewrite; keep meaning and style. 
        If needed, add spaces or correct misspelled letters.
        2) Extract the Bible reference (igehely) if present. Return it in Hungarian format
        (e.g., "János 3,16" or "Zsoltárok 23,1-4"). If no specific reference appears, use "Nincs igehely".
        3) Divide the corrected transcript into three parts:
        - "introduction": the opening greetings and introductory remarks, ends with mentions the from the Bible
        - "scripture_reading": the part where the Bible text is read aloud, contains just the text from the Bible
        - "body": the main sermon content.

        Output:
        Return ONLY a single JSON object with exactly these keys:
        {{
        "corrected_transcript": "<string>",
        "bible_reference": "<string>",
        "introduction": "<string>",
        "scripture_reading": "<string>",
        "body": "<string>"
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

        # always include original raw_text
        data["raw_transcript"] = raw_text

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