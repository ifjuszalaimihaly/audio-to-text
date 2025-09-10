from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text
from app.clients import get_google_client
from app.setvices.transcribe_service import TranscribeService
from app.setvices.embedding_service import EmbeddingService
from app.database.models import SermonFile, SermonChunk
from app.helpers import AUDIO_EXTS, guess_mime_from_filename
import time
from app.database.models import SermonChunk
import numpy as np
from typing import Any, Optional



from app.database.connection import get_db

router = APIRouter()

# ---------------- TEXT ----------------
@router.post("/search/text")
async def transcribe_text_endpoint(search_text: str, db: Session = Depends(get_db)):
    """
    Accepts a search query for get sermon list
    """
    client = get_google_client()
    embedding_service = EmbeddingService(client)
    search_vector = embedding_service.embed_text(search_text, task_type="RETRIEVAL_DOCUMENT")

    chunks = db.query(SermonChunk.id, SermonChunk.embedding, SermonChunk.text_value).all()
    print(chunks)

    '''results = []
    for ch, dist in rows:
        results.append({
            "chunk_id": str(ch.id),
            "file_id": str(ch.file_id),
            "text": ch.text,
            "section": ch.section,
            "char_start": ch.char_start,
            "char_end": ch.char_end,
            "distance": float(dist)   # kisebb = jobb
        })'''
    return JSONResponse("hello")


@router.post("/search/text2")
async def transcribe_text_endpoint(search_text: str, db: Session = Depends(get_db)):
    """
    Accepts a search query and returns the single best-matching sermon chunk
    based on cosine distance (1 - cosine_similarity) with L2-normalized vectors.
    """
    client = get_google_client()
    embedding_service = EmbeddingService(client)

    # 1) KERESŐ VEKTOR (query) -> embed + L2 normalizálás
    search_vector = embedding_service.embed_text(
        search_text,
        task_type="retrieval_document"   # egységesen kisbetűs
    )
    if search_vector is None:
        raise HTTPException(status_code=500, detail="Embedding service returned no vector for query.")

    search_vec = _to_np_vector(search_vector)
    if search_vec is None or search_vec.size == 0:
        raise HTTPException(status_code=500, detail="Query embedding could not be parsed.")
    search_vec = _l2_normalize(search_vec)  # (D,)

    # 2) DOKUMENTUM VEKOTOROK (DB) -> betöltés + L2 normalizálás
    rows = db.query(SermonChunk.id, SermonChunk.embedding, SermonChunk.text_value).all()
    if not rows:
        raise HTTPException(status_code=404, detail="No sermon chunks found.")

    doc_ids = []
    doc_texts = []
    doc_vecs = []

    for _id, _emb, _text in rows:
        v = _to_np_vector(_emb)
        if v is None or v.size == 0:
            continue
        doc_ids.append(_id)
        doc_texts.append(_text)
        doc_vecs.append(v)

    if not doc_vecs:
        raise HTTPException(status_code=404, detail="No valid embeddings in database.")

    doc_mat = np.vstack(doc_vecs)            # (N, D)
    doc_mat = _l2_normalize(doc_mat)         # minden sor egységnormájú lesz

    # 3) COSINE SIMILARITY a normált vektorokon (gyors dot product)
    #    sims[i] = cos_sim(doc_i, query)  in [-1, 1]
    sims = doc_mat @ search_vec             # (N,)

    # 4) COSINE DISTANCE = 1 - similarity  -> MINIMALIZÁLUNK
    dists = 1.0 - sims                      # (N,)

    # 5) Legjobb találat indexe
    best_idx = int(np.argmin(dists))

    best = {
        "chunk_id": str(doc_ids[best_idx]),
        "text": doc_texts[best_idx],
        "cosine_similarity": float(sims[best_idx]),
        "cosine_distance": float(dists[best_idx]),  # kisebb = jobb
    }

    return JSONResponse(best)

def _to_np_vector(raw: Any) -> Optional[np.ndarray]:
    """
    Bármilyen tárolt embeddingből (list/tuple/JSON string/bytes/memoryview) np.ndarray-t csinál.
    Ha nem értelmezhető, None-t ad vissza.
    """
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)):
        return np.asarray(raw, dtype=np.float32)
    if isinstance(raw, (bytes, bytearray, memoryview)):
        try:
            return np.frombuffer(raw, dtype=np.float32)
        except Exception:
            return None
    if isinstance(raw, str):
        # sok DB JSON-ként tárolja
        try:
            return np.asarray(json.loads(raw), dtype=np.float32)
        except Exception:
            return None
    # végső fallback
    try:
        return np.asarray(raw, dtype=np.float32)
    except Exception:
        return None

def _l2_normalize(vecs: np.ndarray) -> np.ndarray:
    """
    L2-normalizálás (0/NaN védelem). Támogat 1D és 2D bemenetet is.
    - 1D: (D,) -> (D,)
    - 2D: (N, D) -> (N, D) soronként
    """
    vecs = np.asarray(vecs, dtype=np.float32)
    if vecs.ndim == 1:
        n = np.linalg.norm(vecs)
        if not np.isfinite(n) or n == 0.0:
            return vecs
        return vecs / n
    elif vecs.ndim == 2:
        n = np.linalg.norm(vecs, axis=1, keepdims=True)
        n = n + 1e-12
        return vecs / n
    else:
        raise ValueError("vecs must be 1D or 2D")