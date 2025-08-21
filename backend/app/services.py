from google.genai import types
from google import genai


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
        return resp.text or ""

    def correct_transcript(self, raw_text: str) -> str:
        """
        Fix typos and word segmentation issues in Hungarian transcripts,
        without paraphrasing or rewriting.
        """
        prompt = f"""
        Your task is to correct typos and word segmentation errors in the raw text of Hungarian sermon audio transcripts.
        Do not rephrase or rewrite the text; only fix misspellings or incorrect word splits, or add spaces between the words if needed.

        Here is the text to process:
        {raw_text}
        """
        resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
        )
        return (resp.text or "").strip()

    def extract_bible_reference(self, transcript: str) -> str:
        """
        Extract Bible reference (igehely) from a Hungarian sermon transcript.
        """
        prompt = f"""
        Your task is to extract the Bible reference from the following Hungarian sermon transcript.
        Return only the reference in Hungarian format (e.g., 'János 3,16' or 'Zsoltárok 23,1-4').
        If there is no specific reference, reply with: 'Nincs igehely'.

        Transcript:
        {transcript}
        """
        resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
        )
        return (resp.text or "").strip()
