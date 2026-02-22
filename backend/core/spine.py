from pathlib import Path

from backend.config import Settings
from backend.engine import Transcriber
from backend.output import SessionLogger


class CoreSpine:
    """Core offline dictation flow: transcribe audio and append session logs."""

    def __init__(self, settings: Settings):
        self.transcriber = Transcriber(settings)
        self.session_logger = SessionLogger(settings)

    def transcribe_file(self, audio_path: Path) -> str:
        return self.transcriber.transcribe(audio_path)

    def append_session_text(self, text: str) -> Path:
        return self.session_logger.append(text)
