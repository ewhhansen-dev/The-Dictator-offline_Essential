import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.config import Settings, load_settings
from backend.core import CoreSpine

router = APIRouter()
logger = logging.getLogger(__name__)

# Singleton instance
_spine = None

# Allowed audio formats
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}
ALLOWED_MIME_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/webm",
    "audio/ogg",
    "audio/flac",
    "audio/x-flac",
}


class AppendRequest(BaseModel):
    text: str


class TranscribeResponse(BaseModel):
    text: str


def get_settings() -> Settings:
    return load_settings()


def get_spine(settings: Settings = Depends(get_settings)) -> CoreSpine:
    global _spine
    if _spine is None:
        _spine = CoreSpine(settings)
    return _spine


@router.get("/health")
def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "ok",
        "version": "0.1.0",
        "mode": "offline-essential",
        "transcription_model": settings.transcription.model,
        "session_directory": str(settings.session.directory),
        "external_api_enabled": False,
    }


@router.get("/config")
def get_config(settings: Settings = Depends(get_settings)):
    return settings


@router.post("/transcribe")
def transcribe_audio(
    file: UploadFile = File(...),
    spine: CoreSpine = Depends(get_spine),
) -> TranscribeResponse:
    logger.info("Received audio upload: %s, content_type: %s", file.filename, file.content_type)

    # 1. Validate extension
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected upload with invalid extension: %s", suffix)
        raise HTTPException(status_code=400, detail=f"Invalid file extension: {suffix}")

    # 2. Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning("Rejected upload with invalid MIME type: %s", file.content_type)
        raise HTTPException(status_code=400, detail=f"Invalid MIME type: {file.content_type}")

    # 3. Basic Magic Byte Verification
    # Read the first 256 bytes to check for common audio headers
    header = file.file.read(256)
    file.file.seek(0)  # Reset file pointer for shutil.copyfileobj

    is_valid_header = False
    if header.startswith(b"RIFF") and b"WAVE" in header[:12]:
        is_valid_header = True  # WAV
    elif header.startswith((b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3")):
        is_valid_header = True  # MP3
    elif header.startswith(b"OggS"):
        is_valid_header = True  # Ogg
    elif header.startswith(b"fLaC"):
        is_valid_header = True  # FLAC
    elif b"ftyp" in header[4:12]:
        is_valid_header = True  # MP4/M4A
    elif header.startswith(b"\x1a\x45\xdf\xa3"):
        is_valid_header = True  # WebM/Matroska

    if not is_valid_header:
        logger.warning("Rejected upload with invalid magic bytes: %s", filename)
        raise HTTPException(status_code=400, detail="Invalid audio file content")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        text = spine.transcribe_file(tmp_path)
        return TranscribeResponse(text=text)
    except Exception as exc:
        logger.error("Transcription failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@router.post("/session/append")
def append_session(
    request: AppendRequest,
    spine: CoreSpine = Depends(get_spine),
):
    try:
        path = spine.append_session_text(request.text)
        return {"status": "success", "file": str(path)}
    except Exception as exc:
        logger.error("Failed to append to session: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
