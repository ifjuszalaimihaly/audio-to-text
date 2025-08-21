from fastapi import UploadFile

AUDIO_EXTS = (".mp3", ".flac", ".wav", ".m4a", ".webm", ".ogg")

def guess_mime_from_filename(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    return {
        "mp3": "audio/mp3",
        "wav": "audio/wav",
        "m4a": "audio/mp4",
        "flac": "audio/flac",
        "webm": "audio/webm",
        "ogg": "audio/ogg",
        "txt": "text/plain",
    }.get(ext, "application/octet-stream")

def is_text_upload(file: UploadFile) -> bool:
    ct = (file.content_type or "").lower()
    return ct == "text/plain" or file.filename.lower().endswith(".txt")
