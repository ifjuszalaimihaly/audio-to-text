from google.genai import types
from google import genai
from typing import List, Tuple
import json
import re




class EmbeddingService:
    def __init__(self, client: genai.Client):
        """
        Service create embeddings with Google GenAI.
        """
        self.client = client
        self._SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ])")
    

    def _parse_strict_json(self, s: str) -> dict:
        """
        Tries to parse JSON even if the model wrapped it in Markdown code fences.
        """
        # Strip markdown code fences if present
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, flags=re.S)
        if fence_match:
            s = fence_match.group(1)
        return json.loads(s)


    def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        resp = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY") # RETRIEVAL_DOCUMENT for Documents
        )
        return resp.embeddings[0].values  # list[float]


    def split_sentences(self, text: str) -> List[Tuple[int, int, str]]:
        text = re.sub(r"\s+", " ", text).strip()
        out = []
        last = 0
        for part in self._SENT_SPLIT.split(text):
            part = part.strip()
            if not part:
                continue
            start = text.find(part, last)
            end = start + len(part)
            out.append((start, end, part))
            last = end
        if not out and text:
            out = [(0, len(text), text)]
        return out

    def approx_tokens(self, s: str) -> int:
        return max(1, len(s.split()))


    def chunk_corrected_text(self, corrected_text: str, target_tokens: int = 400, min_tokens: int = 200) -> List[Tuple[int,int,str]]:
        sentences = self.split_sentences(corrected_text)
        chunks = []
        i = 0
        n = len(sentences)
        while i < n:
            start_char = sentences[i][0]
            tokens = 0
            text_parts = []
            j = i
            while j < n:
                s_start, s_end, s_text = sentences[j]
                t = self.approx_tokens(s_text)
                if tokens >= min_tokens and tokens + t > target_tokens:
                    break
                text_parts.append(s_text)
                tokens += t
                j += 1
            end_char = sentences[j-1][1] if j > i else sentences[i][1]
            chunk_text = " ".join(text_parts).strip()
            if chunk_text:
                chunks.append({"start": start_char, "end": end_char, "text": chunk_text})
            i = j
        return chunks