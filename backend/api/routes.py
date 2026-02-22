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
    logger.info("Received audio upload: %s", file.filename)

    suffix = Path(file.filename or "").suffix or ".wav"

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
